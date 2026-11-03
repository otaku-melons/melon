from typing import TYPE_CHECKING, Literal, overload

from bs4 import BeautifulSoup, Tag

from dublib.functions.data import to_sequence

from ...core.base.structs.image import ImageData, ImageType
from .. import exceptions
from .elements.blockquote import Blockquote
from .elements.header import Header
from .elements.paragraph import Paragraph
from .enums import Align

if TYPE_CHECKING:
	from collections.abc import Sequence

	from bs4._typing import AttributeValueList

	from .base_elements import BaseElement
	from .footnote import Footnote

class HyperTextInterpreter:
	"""HTML lines into elements interpreter."""

	def filter_elements[T: "BaseElement | ImageData"](
		self,
		elements: "Sequence[BaseElement | ImageData]",
		target_types: "type[T] | Sequence[type[T]]",
		raise_error: bool = True,
		) -> tuple[T, ...]:
		"""
		Filter elements sequence.

		Args:
			elements (Sequence[BaseElement | ImageData]): Element for filtering.
			target_types (type[T] | Sequence[type[T]]): Target types.
			raise_error (bool): Raise exception if found unresolved element.

		Returns:
			tuple[T, ...]: Filtered elements.

		Raises:
			UnresolvedElementError: Unresolved element found.
		"""

		filtered_elements: list[T] = []
		target_types = to_sequence(target_types)

		for element in elements:
			if isinstance(element, target_types):
				filtered_elements.append(element)
			elif raise_error:
				raise exceptions.html.UnresolvedElementError(element)

		return tuple(filtered_elements)

	def interpret(self, line: str, footnotes: "Sequence[Footnote] | None" = None) -> "BaseElement | ImageData":
		"""
		Interpret HTML line into element.

		Args:
			line (str): HTML line.
			footnotes (Sequence[Footnote] | None): Available footnotes.

		Returns:
			BaseElement | ImageData: HTML element.

		Raises:
			exceptions.html.DecodingError: Unknown root tag.
		"""

		root_tag_name: str = self.__get_root_tag_name(line)
		tag: Tag = self.__to_tag(line, root_tag_name)

		match tag.name:

			case "p":
				align: Align | None = self.parse_align(tag)
				text: str = tag.decode_contents()
				paragraph = Paragraph(text, allow_footnotes = bool(footnotes))
				paragraph.set_align(align)

				if footnotes:
					element_footnotes: tuple[Footnote, ...] = self.__get_element_footnotes(tag, footnotes)
					paragraph.set_footnotes(element_footnotes)

				return paragraph

			case "h3" | "h4" | "h5" | "h6":
				level: Literal[3, 4, 5, 6] = self.__extract_header_level(root_tag_name)
				align: Align | None = self.parse_align(tag)
				text: str = tag.decode_contents()
				header = Header(text, level = level, allow_footnotes = bool(footnotes))
				header.set_align(align)

				if footnotes:
					element_footnotes: tuple[Footnote, ...] = self.__get_element_footnotes(tag, footnotes)
					header.set_footnotes(element_footnotes)

				return header

			case "img":
				src: str = str(tag["src"])
				width: AttributeValueList | str | None = tag.attrs.get("width")
				height: AttributeValueList | str | None = tag.attrs.get("height")
				data_file: AttributeValueList | str | None = tag.attrs.get("data-file")

				image = ImageData(src, ImageType.Illustration)

				if width and height:
					image.create_resolution(int(str(width)), int(str(height)))

				if data_file:
					image.set_file_path(str(data_file))

				return image

			case "blockquote":
				align: Align | None = self.parse_align(tag)
				childrens: tuple[Tag, ...] = tuple(tag.find_all())
				elements: list[BaseElement | ImageData] = []

				for child in childrens:
					elements.append(self.interpret(str(child), footnotes))

				filtered_elements: tuple[Header | ImageData | Paragraph, ...] = self.filter_elements(elements, target_types = (Header, ImageData, Paragraph))
				blockquote = Blockquote()
				blockquote.set_align(align)
				blockquote.set_elements(filtered_elements)

				return blockquote

			case _:
				raise exceptions.html.DecodingError(f"Unknown root tag: \"{root_tag_name}\".")

	@overload
	def interpret_lines[T: BaseElement | ImageData](
		self,
		lines: "Sequence[str]",
		footnotes: "Sequence[Footnote] | None" = None,
		allowed_types: "Sequence[type[T]]" = ...,
	) -> tuple[T, ...]: ...
	@overload
	def interpret_lines(
		self,
		lines: "Sequence[str]",
		footnotes: "Sequence[Footnote] | None" = None,
		allowed_types: None = None,
	) -> "Sequence[BaseElement | ImageData]": ...

	def interpret_lines[T: BaseElement | ImageData](
		self,
		lines: "Sequence[str]",
		footnotes: "Sequence[Footnote] | None" = None,
		allowed_types: "Sequence[type[T]] | None" = None,
		) -> "tuple[T, ...] | Sequence[BaseElement | ImageData]":

		elements: list[BaseElement | ImageData] = [self.interpret(line, footnotes) for line in lines]

		if allowed_types:
			return self.filter_elements(elements, target_types = allowed_types)

		return tuple(elements)

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

	def __extract_header_level(self, header_tag: str) -> Literal[3, 4, 5, 6]:
		"""
		Extract header level from tag name.

		Args:
			header_tag (str): Header tag.

		Returns:
			Literal[3, 4, 5, 6]: Header level.

		Raises:
			exceptions.html.DecodingError: Header level must be from 3 to 6..
		"""

		level: int = int(header_tag.rstrip("h"))

		if level not in (3, 4, 5, 6):
			raise exceptions.html.DecodingError("Header level must be from 3 to 6.")

		return level

	def __get_element_footnotes(self, tag: Tag, footnotes: "Sequence[Footnote]") -> tuple["Footnote", ...]:
		"""
		Get element footnotes.

		Args:
			tag (Tag): HTML tag.
			footnotes (Sequence[Footnote]): Available footnotes.

		Returns:
			tuple["Footnote", ...]: Footnotes for given element.

		Raises:
			exceptions.html.DecodingError: Footnote decoding error.
		"""

		if not footnotes:
			return ()

		footnotes_cache: dict[str, Footnote] = {item.id: item for item in footnotes}
		anchors = tag.find_all("a")

		if not anchors:
			return ()

		results: list[Footnote] = []

		for anchor in anchors:
			footnote_id: AttributeValueList | str | None = anchor.attrs.get("data-footnote")

			if not footnote_id:
				raise exceptions.html.DecodingError("Footnote without ID found.")

			footnote: Footnote | None = footnotes_cache.get(str(footnote_id))

			if not footnote:
				raise exceptions.html.DecodingError("Body for footnote not found.")

			results.append(footnote)

		return tuple(results)

	def __get_root_tag_name(self, line: str) -> str:
		"""
		Get root tag name.

		Args:
			line (str): HTML line.

		Returns:
			str: Root tag name.
		"""

		return line.split(" ", maxsplit = 1)[0].lstrip("<")

	def __to_tag(self, line: str, tag_name: str) -> Tag:
		"""
		Convert HTML line into **BeautifulSoup** tag.

		Args:
			line (str): HTML line.
			tag_name (str): Root tag name.

		Returns:
			Tag: **BeautifulSoup** tag.

		Raises:
			exceptions.html.DecodingError: Can't parse root HTML line tag..
		"""

		soup = BeautifulSoup(line, "html.parser")
		tag: Tag | None = soup.find(tag_name)

		if not tag:
			raise exceptions.html.DecodingError("Can't parse root HTML line tag.")

		return tag
