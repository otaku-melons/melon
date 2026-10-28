from typing import TYPE_CHECKING, override

from ..base_format.chapter import BaseChapter
from .enums import ChapterType

if TYPE_CHECKING:
	from collections.abc import Sequence

	from ....html.base_elements import BaseElement

class Chapter(BaseChapter):
	"""Глава ранобэ."""

	#==========================================================================================#
	# >>>>> PROPERTIES <<<<< #
	#==========================================================================================#

	@property
	def footnotes(self) -> tuple[str, ...]:
		"""Последовательность заметок."""

		return tuple(self._data["footnotes"])

	@property
	def paragraphs(self) -> tuple[str, ...]:
		"""Последовательность абзацев."""

		return tuple(self._data["paragraphs"])

	@property
	def type(self) -> ChapterType | None:
		"""Тип главы."""

		return ChapterType[self._data["type"]]

	#==========================================================================================#
	# >>>>> OVERRIDABLE METHODS <<<<< #
	#==========================================================================================#

	@override
	def _clear(self):
		"""Очищает контент главы."""

		self._data["paragraphs"] = []
		self._data["footnotes"] = []

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
		self._data["footnotes"] = []

	#==========================================================================================#
	# >>>>> PUBLIC METHODS <<<<< #
	#==========================================================================================#

	def add_element(self, element: "BaseElement"):
		"""
		Добавляет элемент в главу.

		:param element: Элемент главы.
		:type element: BaseElement
		:raise TypeError: Выбрасывается при передаче неподдерживаемого элемента.
		"""

		self._data["paragraphs"].append(element.to_html())

	def set_elements(self, elements: "Sequence[BaseElement]"):
		"""
		Задаёт набор элементов главы.

		:param elements: Набор элементов главы.
		:type elements: Sequence[BaseElement]
		"""

		for Element in elements: self.add_element(Element)

	def set_type(self, chapter_type: ChapterType | None):
		"""
		Задаёт тип главы.

		:param chapter_type: Тип главы.
		:type chapter_type: ChapterType | None
		"""

		self._data["type"] = chapter_type.value if chapter_type else None
