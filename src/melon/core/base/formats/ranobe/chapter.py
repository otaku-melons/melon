from typing import TYPE_CHECKING, override

from ....html.base_elements import BaseElement, TextElement
from ....html.elements.paragraph import Paragraph
from ....html.footnote import Footnote
from ...structs.image import ImageData
from ..base_format.chapter import BaseChapter
from .enums import ChapterType

if TYPE_CHECKING:
	from collections.abc import Sequence

class Chapter(BaseChapter):
	"""Ranobe chapter."""

	def add_element(self, element: "BaseElement | ImageData"):
		"""
		Add element to chapter.

		Args:
			element (BaseElement | ImageData): HTML element.
		"""

		if isinstance(element, ImageData):
			self.__images.append(element)

		elif isinstance(element, TextElement):
			for footnote in element.footnotes:
				self.__footnotes.append(footnote)
				self.__images.extend(footnote.images)

		self.__elements.append(element)

	def set_elements(self, elements: "Sequence[BaseElement | ImageData]"):
		"""
		Clear exists elements and set new.

		Args:
			elements (Sequence[BaseElement | ImageData]): New elements.
		"""

		self._clear_content()

		for element in elements:
			self.add_element(element)

	def set_chapter_type(self, chapter_type: ChapterType | None):
		"""
		Set chapter type.

		Args:
			chapter_type (ChapterType | None): Chapter type.
		"""

		self._data["type"] = chapter_type.value if chapter_type else None

	@property
	def elements(self) -> tuple["BaseElement | ImageData", ...]:
		"""Elements."""

		return tuple(self.__elements)

	@property
	def footnote(self) -> tuple["Footnote", ...]:
		"""Footnotes."""

		return tuple(self.__footnotes)

	@property
	def paragraphs(self) -> tuple[str, ...]:
		"""Paragraphs."""

		return self.__build_paragraphs()

	@property
	def type(self) -> ChapterType | None:
		"""Chapter type."""

		return ChapterType(self._data["type"])

	@override
	def _clear_content(self):
		"""Clear chapter content."""

		self.__elements.clear()
		self.__footnotes.clear()
		self.__images.clear()

	@override
	def _from_dict(self, data: dict):
		"""
		Parse chapter dictionary from descriptive file and fill instance attributes.

		Args:
			data (dict): Chapter data.
		"""

		self._data = self._data | data

		footnotes: tuple[Footnote, ...] = self.__parse_footnotes(self._data["footnotes"])
		lines: list[str] = self._data["paragraphs"]
		elements = self._parser.title.html_interpreter.interpret_lines(lines, footnotes)

		self.set_elements(elements)

	@override
	def _get_chapter_images(self) -> "Sequence[ImageData]":
		"""
		Get chapter-associated images.

		Returns:
			Sequence[ImageData]: Chapter images.
		"""

		return self.__images

	@override
	def _is_empty(self) -> bool:
		"""
		Check is chapter empty.

		Returns:
			bool: Condition: is chapter empty.
		"""

		return not bool(self.__elements)

	@override
	def _post_init(self):
		"""Execute after instance initialization."""

		self._data["type"] = None
		self._data["paragraphs"] = []
		self._data["footnotes"] = {}

		self.__elements: list[BaseElement | ImageData] = []
		self.__footnotes: list[Footnote] = []
		self.__images: list[ImageData] = []

	@override
	def _pre_formatter(self):
		"""Execute before chapter data conversion into dictionary."""

		self._data["paragraphs"] = self.__build_paragraphs()

		footnotes: dict[str, list[str]] = {}

		for footnote in self.__footnotes:
			html_elements: list[str] = [element.to_html() for element in footnote.elements]
			footnotes[footnote.id] = html_elements

		self._data["footnotes"] = footnotes

	def __build_paragraphs(self) -> tuple[str, ...]:
		"""
		Build paragraphs HTML lines from chapter elements..

		Returns:
			tuple[str, ...]: HTML lines.
		"""

		return tuple(element.to_html() for element in self.__elements)

	def __parse_footnotes(self, footnotes_data: dict[str, list[str]]) -> tuple[Footnote, ...]:
		"""
		Parse footnotes from data dictionary.

		Args:
			footnotes_data (dict[str, list[str]]): Dictionary in which key is footnote ID and value is HTML lines.

		Returns:
			tuple[Footnote, ...]: Chapter footnotes.
		"""

		footnotes: list[Footnote] = []

		for footnote_id, lines in footnotes_data.items():
			elements = self._parser.title.html_interpreter.interpret_lines(lines, allowed_types = (ImageData, Paragraph))
			buffer = Footnote(elements, id = footnote_id)
			footnotes.append(buffer)

		return tuple(footnotes)
