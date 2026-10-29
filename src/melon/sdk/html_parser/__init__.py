from typing import TYPE_CHECKING

from bs4 import BeautifulSoup, NavigableString, PageElement, Tag

from dublib.functions.data import to_sequence
from dublib.functions.data.string import remove_recurring_substrings

from ...core.exceptions.html import UnresolvedTagError
from ...core.html.allowed_tags import ALLOWED_TAGS
from ...core.html.elements import Paragraph
from ...core.html.enums import Align, TagCategory

if TYPE_CHECKING:
	from collections.abc import Sequence

	from bs4._typing import AttributeValueList

class HyperTextParser:
	"""HTML elements parser."""

	#==========================================================================================#
	# >>>>> PROPERTIES <<<<< #
	#==========================================================================================#

	@property
	def pretty(self) -> bool:
		"""Condition: is pretty content processing enabled."""

		return self._pretty

	#==========================================================================================#
	# >>>>> PUBLIC METHODS <<<<< #
	#==========================================================================================#

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

		targets: list[Tag] = [child for child in tag.contents if isinstance(child, Tag)]
		targets.append(tag)

		for target in targets:
			tag_data = ALLOWED_TAGS.get_tag(target.name)
			attributes: dict = target.attrs.copy()

			if not tag_data:
				raise UnresolvedTagError(target.name)

			for attribute in target.attrs:

				if tag_data.is_support_data and attribute.startswith("data-"):
					continue

				if attribute == "style" and tag_data.styles:
					continue

				if attribute not in tag_data.attributes:
					del attributes[attribute]
					removed.append(attribute)

			target.attrs = attributes

		return tuple(removed)

	def clear_styles(self, tag: Tag) -> tuple[str, ...]:
		"""
		Clear unresolved styles for tag and inner tags.

		Args:
			tag (Tag): HTML tag.

		Raises:
			UnresolvedTagError: Unresolved tag.

		Returns:
			tuple[str, ...]: Removed styles names.
		"""

		removed: list[str] = []

		targets: list[Tag] = [child for child in tag.contents if isinstance(child, Tag)]
		targets.append(tag)

		for target in targets:
			tag_data = ALLOWED_TAGS.get_tag(target.name)

			if not tag_data:
				raise UnresolvedTagError(target.name)

			style: AttributeValueList | str | None = target.attrs.get("style")

			if not style:
				continue

			style = str(style)
			styles: list[str] = style.split(";")
			filtered_styles: dict[str, str] = {}

			for current_style in styles:
				name, value = current_style.split(":")
				name: str = name.strip()
				value: str = value.strip()

				if name in tag_data.styles:
					filtered_styles[name] = value
				else:
					removed.append(name)

			if filtered_styles:
				target["style"] = ";".join(f"{name}: {value}" for name, value in filtered_styles.items())
			else:
				del target["style"]

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

		- Strip.
		- Replace no-break spaces with normal.
		- Replace recurring spaces.

		Args:
			text (str): Normalizable text.

		Returns:
			str: Normalized text.
		"""

		text = text.strip()
		text = text.replace("\u00a0", " ")
		text = remove_recurring_substrings(text, " ")

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

	#==========================================================================================#
	# >>>>> PUBLIC ELEMENTS PARSING METHODS <<<<< #
	#==========================================================================================#

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
			self.clear_styles(inner_paragraph)

			text: str = inner_paragraph.decode_contents()

			if self.pretty:
				text = self.normalize_text(text)

			paragraph = Paragraph(text)
			align: Align | None = self.parse_align(inner_paragraph)
			paragraph.set_align(align)
			paragraphs.append(paragraph)

		return tuple(paragraphs)
