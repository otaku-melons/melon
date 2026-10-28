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
		Clear unresolved tag attributes.

		Args:
			tag (Tag): HTML tag.

		Raises:
			UnresolvedTagError: Unresolved tag.

		Returns:
			tuple[str, ...]: Removed attributes.
		"""

		attributes: dict = tag.attrs.copy()
		tag_data = ALLOWED_TAGS.get_tag(tag.name)

		if not tag_data:
			raise UnresolvedTagError(tag.name)

		removed: list[str] = []

		for attribute in tag.attrs:

			if tag_data.is_support_data and attribute.startswith("data-"):
				continue

			if attribute not in tag_data.attributes:
				del attributes[attribute]
				removed.append(attribute)

		tag.attrs = attributes

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

	def make_tag(self, name: str, content: "PageElement | Sequence[PageElement] | str") -> Tag:
		"""
		Make tag without builder.

		Args:
			name (str): Tag name.
			content (PageElement | Sequence[PageElement] | str): Tag content.

		Returns:
			Tag: New tag.
		"""

		new_tag = Tag(name = name)

		if isinstance(content, str):
			content = BeautifulSoup(content, "html.parser").contents

		for item in to_sequence(content):
			new_tag.append(item)

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

		align: Align | None = None

		if "align" in tag.attrs:
			value: str = str(tag.attrs["align"])
			align = Align(value)

		elif "style" in tag.attrs:
			values: list[str] = str(tag.attrs["style"]).split(";")

			for style in values:
				name, value = style.split(":")
				name = name.strip()

				if name == "text-align":
					value = value.strip()
					align = Align(value)
					break

		return align

	def split(self, tag: Tag) -> tuple[Tag, ...]:
		"""
		Split tag childrens into paragraphs by `<br>` and `\n`.

		If tag doesn't contain splitters, in fact it will be replaced by `p`.

		Args:
			tag (Tag): HTML tag.

		Returns:
			tuple[Tag, ...]: Paragraphs.
		"""

		result: list[Tag] = []
		current_content: list[PageElement] = []

		def __add_paragraph():
			new_tag = self.make_tag("p", current_content)
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

			text: str = inner_paragraph.decode_contents()

			if self.pretty:
				text = self.normalize_text(text)

			paragraph = Paragraph(text)
			align: Align | None = self.parse_align(inner_paragraph)
			paragraph.set_align(align)
			paragraphs.append(paragraph)

		return tuple(paragraphs)
