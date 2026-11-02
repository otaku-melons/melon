from typing import TYPE_CHECKING, override

from ....html.base_elements import BaseElement, TextElement
from ...structs.image import ImageData
from ..base_format.chapter import BaseChapter
from .enums import ChapterType

if TYPE_CHECKING:
	from collections.abc import Sequence

	from ....html.footnote import Footnote

class Chapter(BaseChapter):
	"""Ranobe chapter."""

	def add_element(self, element: "BaseElement | ImageData"):
		"""
		Добавляет элемент в главу.

		:param element: Элемент главы.
		:type element: BaseElement | ImageData
		:raise TypeError: Выбрасывается при передаче неподдерживаемого элемента.
		"""

		if isinstance(element, ImageData):
			self.__images.append(element)

		elif isinstance(element, TextElement):
			for footnote in element.footnotes:
				self.__footnotes.append(footnote)
				self.__images.extend(footnote.images)

		self._data["paragraphs"].append(element.to_html())

	def set_elements(self, elements: "Sequence[BaseElement | ImageData]"):
		"""
		Задаёт набор элементов главы.

		:param elements: Набор элементов главы.
		:type elements: Sequence[BaseElement | ImageData]
		"""

		for element in elements:
			self.add_element(element)

	def set_type(self, chapter_type: ChapterType | None):
		"""
		Задаёт тип главы.

		:param chapter_type: Тип главы.
		:type chapter_type: ChapterType | None
		"""

		self._data["type"] = chapter_type.value if chapter_type else None

	@property
	def paragraphs(self) -> tuple[str, ...]:
		"""Paragraphs."""

		return tuple(self._data["paragraphs"])

	@property
	def type(self) -> ChapterType | None:
		"""Chapter type."""

		return ChapterType[self._data["type"]]

	@override
	def _clear(self):
		"""Очищает контент главы."""

		self._data["paragraphs"] = []

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
		Проверяет, пустая ли глава.

		:return: Состояние: пуста ли глава.
		:rtype: bool
		"""

		return not bool(self._data["paragraphs"])

	@override
	def _from_dict(self, data: dict):
		"""
		Заполняет данные главы из словаря.

		:param data: Словарь данных главы.
		:type data: dict
		"""

		self._data = self._data | data

	@override
	def _post_init(self):
		"""Execute after instance initialization."""

		self._data["paragraphs"] = []
		self._data["footnotes"] = {}

		self.__footnotes: list[Footnote] = []
		self.__images: list[ImageData] = []

	@override
	def _pre_formatter(self):
		"""Execute before chapter data conversion into dictionary."""

		footnotes: dict[str, list[str]] = {}

		for footnote in self.__footnotes:
			html_elements: list[str] = [element.to_html() for element in footnote.elements]
			footnotes[footnote.id] = html_elements

		self._data["footnotes"] = footnotes
