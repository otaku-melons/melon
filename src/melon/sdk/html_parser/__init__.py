from typing import TYPE_CHECKING

from bs4 import BeautifulSoup, NavigableString, PageElement, Tag

from dublib.functions.data import to_sequence
from dublib.functions.data.string import remove_recurring_substrings

from ...core.base.structs.image import ImageData, ImageResolution, ImageType
from ...core.exceptions.html import UnresolvedTagError
from ...core.html.allowed_tags import ALLOWED_TAGS
from ...core.html.elements import Blockquote, Header, Paragraph
from ...core.html.enums import Align, TagCategory

if TYPE_CHECKING:
	from collections.abc import Sequence

	from bs4._typing import AttributeValueList

class HyperTextParser:
	"""HTML elements parser."""

	def __init__(self, pretty: bool = False):
		"""
		HTML elements parser.

		Args:
			pretty (bool): Enable pretty content processing.
		"""

		self._pretty: bool = pretty

	def check_unresolved_childrens(self, tag: Tag, raise_error: bool = False) -> tuple[str, ...]:
		"""
		Check is tag contains unresolved childrens.

		Args:
			tag (Tag): HTML tag.
			raise_error (bool): Raise exception if unresolved tag found.

		Raises:
			UnresolvedTagError: Unresolved tag found.

		Return:
			tuple[str, ...]: Unresolved tags names.
		"""

		unresolved_tags: list[str] = []

		for child in tag.find_all():

			if child.name not in ALLOWED_TAGS.get_category_tags_names(TagCategory.Styling):
				if raise_error:
					raise UnresolvedTagError(child.name)
				else:
					unresolved_tags.append(child.name)

		return tuple(unresolved_tags)

	def clear_attributes(self, tag: Tag) -> tuple[str, ...]:
		"""
		Clear unresolved attributes for tag and inner tags.

		Args:
			tag (Tag): HTML tag.

		Raises:
			UnresolvedTagError: Unresolved tag.

		Returns:
			tuple[str, ...]: Removed attributes names.
		"""

		removed: list[str] = []

		targets: list[Tag] = tag.find_all()
		targets.append(tag)

		for target in targets:
			tag_data = ALLOWED_TAGS.get_tag(target.name)
			attributes: dict = target.attrs.copy()

			if not tag_data:
				raise UnresolvedTagError(target.name)

			for attribute in target.attrs:

				if tag_data.is_support_data and attribute.startswith("data-"):
					continue

				if attribute == "style" and tag_data.is_alignable:
					continue

				if attribute not in tag_data.attributes:
					del attributes[attribute]
					removed.append(attribute)

			target.attrs = attributes

		return tuple(removed)

	def has_child_tag(self, tag: Tag, child: str) -> bool:
		"""
		Check is tag has child tag.

		Args:
			tag (Tag): HTML tag.
			child (str): Child tag name.

		Returns:
			bool: `True` if tag has chaild with given name.
		"""

		return bool(tag.find(child))

	def make_tag(self, name: str, content: "PageElement | Sequence[PageElement] | str", attributes: dict[str, "AttributeValueList | str"] | None = None) -> Tag:
		"""
		Make tag without builder.

		Args:
			name (str): Tag name.
			content (PageElement | Sequence[PageElement] | str): Tag content.
			attributes (attributes: dict[str, AttributeValueList | str] | None): Attributes dictionary.

		Returns:
			Tag: New tag.
		"""

		new_tag = Tag(name = name)

		if isinstance(content, str):
			content = BeautifulSoup(content, "html.parser").contents

		for item in to_sequence(content):
			new_tag.append(item)

		if attributes:
			for name in attributes.keys():
				new_tag[name] = attributes[name]

		return new_tag

	def normalize_text(self, text: str) -> str:
		"""
		Normalize text.

		- Replace no-break spaces with normal.
		- Replace recurring spaces.
		- Strip.

		Args:
			text (str): Normalizable text.

		Returns:
			str: Normalized text.
		"""

		text = text.replace("\u00a0", " ")
		text = remove_recurring_substrings(text, " ")
		text = text.strip()

		return text

	def parse_align(self, tag: Tag) -> Align | None:
		"""
		Parse tag align from `align` attribute or `style`.

		Args:
			tag (Tag): HTML tag.

		Returns:
			Align | None: Tag align or `None` if parsing failed.
		"""

		align_value: str | None = None

		if "align" in tag.attrs:
			value: str = str(tag.attrs["align"])
			align_value = value

		elif "style" in tag.attrs:
			values: list[str] = str(tag.attrs["style"]).split(";")

			for style in values:
				name, value = style.split(":")
				name = name.strip()

				if name == "text-align":
					value = value.strip()
					align_value = value
					break

		try:
			return Align(align_value)
		except ValueError:
			pass

	def parse_blockquote(self, tag: Tag, paragraphs_tags: "Sequence[str]" = ("p"), from_strings: bool = True) -> Blockquote | None:
		"""
		Parse blockquote.

		Args:
			tag (Tag): HTML tag.
			paragraphs_tags (Sequence[str]): Tags names from which paragraphs will be parsed.
			from_strings (bool): Allow parse paragraphs from `NavigableString`.

		Returns:
			Blockquote | None: Blockquote element..

		Raises:
			ValueError: Blockquote can be parsed only from same tag.
		"""

		if tag.name != "blockquote":
			raise ValueError("Blockquote can be parsed only from same tag.")

		elements: list[Header | ImageData | Paragraph] = []
		strings: list[NavigableString | Tag] = []

		def flush_strings():
			if not strings: return
			new_paragraph: Tag = self.make_tag("p", tuple(strings))
			elements.extend(self.parse_paragraphs(new_paragraph))
			strings.clear()

		for child in tuple(tag.contents):

			if from_strings and isinstance(child, NavigableString):
				strings.append(child)
				continue

			if not isinstance(child, Tag):
				continue

			if from_strings and child.name in ALLOWED_TAGS.get_category_tags_names(TagCategory.Styling):
				strings.append(child)
				continue

			flush_strings()

			match child.name:

				case "h1"| "h2" | "h3" | "h4" | "h5" | "h6":
					header: Header | None = self.parse_header(child)
					if header: elements.append(header)

				case "img":
					image: ImageData | None = self.parse_image(child)
					if image: elements.append(image)

				case _:

					if child.name not in paragraphs_tags:
						continue

					elements.extend(self.parse_paragraphs(child))

		flush_strings()

		if elements:
			blockquote = Blockquote()
			align: Align | None = self.parse_align(tag)
			blockquote.set_align(align)
			blockquote.set_elements(elements)

			return blockquote

	def parse_header(self, tag: Tag, autolevel: bool = True) -> Header | None:
		"""
		Parse header from HTML tag.

		Args:
			tag (Tag): HTML tag.
			autolevel (bool): If header level is 1 or 2, will be set as 3.

		Raises:
			ValueError: Image can be parsed only from headers tags.
			UnresolvedTagError: Unresolved tag.

		Returns:
			Image | None: Image element or `None` if missing source.
		"""

		if len(tag.name) != 2 and tag.name[0] != "h" and int(tag.name[1]) not in range(1, 7):
			raise ValueError("Image can be parsed only from headers tags.")

		level: int = int(tag.name[1])

		if level not in (3, 4, 5, 6):
			if autolevel:
				level = 3
				tag.name = f"h{level}"
			else:
				raise UnresolvedTagError(tag.name)

		self.unwrap_non_styling_childrens(tag)
		self.clear_attributes(tag)

		align: Align | None = self.parse_align(tag)
		text: str = tag.decode_contents()

		if self.pretty:
			text = self.normalize_text(text)

		if not text:
			return

		header = Header(text, level = level)
		header.set_align(align)

		return header

	def parse_image(self, tag: Tag) -> ImageData | None:
		"""
		Parse image from HTML tag.

		Args:
			tag (Tag): HTML tag.

		Raises:
			ValueError: Image can be parsed only from \"img\" tag.

		Returns:
			ImageData | None: Image data or `None` if missing source.
		"""

		if tag.name != "img":
			raise ValueError("Image can be parsed only from \"img\" tag.")

		source = tag.attrs.get("src")

		if not source:
			return

		image = ImageData(str(source), ImageType.Illustration)

		width, height = tag.attrs.get("width"), tag.attrs.get("height")

		if width and height:
			resolution = ImageResolution(
				width = int(str(width)),
				height = int(str(height)),
			)
			image.set_resolution(resolution)

		return image

	def parse_paragraphs(self, tag: Tag) -> tuple[Paragraph, ...]:
		"""
		Parse paragraphs from HTML tag.

		Args:
			tag (Tag): HTML tag.

		Returns:
			tuple[Paragraph, ...]: Paragraphs elements.
		"""

		inner_paragraphs: tuple[Tag, ...] = self.split(tag)
		paragraphs: list[Paragraph] = []

		for inner_paragraph in inner_paragraphs:

			if not inner_paragraph.get_text().strip():
				continue

			self.unwrap_non_styling_childrens(inner_paragraph)
			self.clear_attributes(inner_paragraph)

			text: str = inner_paragraph.decode_contents()

			if self.pretty:
				text = self.normalize_text(text)

			paragraph = Paragraph(text)
			align: Align | None = self.parse_align(inner_paragraph)
			paragraph.set_align(align)
			paragraphs.append(paragraph)

		return tuple(paragraphs)

	def split(self, tag: Tag) -> tuple[Tag, ...]:
		"""
		Split tag childrens into paragraphs by `<br>` and `\n`.

		If tag doesn't contain splitters, in fact it will be replaced by `p`. If tag has align, all new tags also will be have same align.

		Args:
			tag (Tag): HTML tag.

		Returns:
			tuple[Tag, ...]: Paragraphs tags. Doesn't affined with builder!
		"""

		result: list[Tag] = []
		current_content: list[PageElement] = []

		align: Align | None = self.parse_align(tag)
		attrs: dict[str, AttributeValueList | str] | None = {"style": f"text-align: {align.value}"} if align else None

		def __add_paragraph():
			new_tag = self.make_tag("p", current_content, attrs)
			result.append(new_tag)
			current_content.clear()

		for child in tuple(tag.contents):

			if isinstance(child, Tag) and child.name == "br":

				if current_content:
					__add_paragraph()

			elif isinstance(child, NavigableString) and "\n" in child:
				parts: list[str] = child.split("\n")
				parts_count: int = len(parts)
				last_index: int = parts_count - 1

				for index in range(parts_count):
					current_content.append(NavigableString(parts[index]))

					if index != last_index:
						__add_paragraph()

			else:
				current_content.append(child)

		if current_content:
			__add_paragraph()

		return tuple(result)

	def unwrap_non_styling_childrens(self, tag: Tag) -> tuple[str, ...]:
		"""
		Unwrap non-styling childrens.

		Args:
			tag (Tag): HTML tag.

		Returns:
			tuple[str, ...]: Unwrapped tags names.
		"""

		unwrapped_tags: list[str] = []
		styling_tags_names: tuple[str, ...] = ALLOWED_TAGS.get_category_tags_names(TagCategory.Styling)

		for child in tag.find_all():
			if child.name not in styling_tags_names:
				child.unwrap()

		return tuple(unwrapped_tags)

	@property
	def pretty(self) -> bool:
		"""Condition: is pretty content processing enabled."""

		return self._pretty
