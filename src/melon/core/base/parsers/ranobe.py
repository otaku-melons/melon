from typing import TYPE_CHECKING, cast, override

from dublib.functions.decorators import run_before_method

from ....core import exceptions
from ..formats import Ranobe
from .base_parser import BaseParser

if TYPE_CHECKING:
	from pydantic import BaseModel

	from ..formats.ranobe.chapter import Chapter
	from ..source_operator import BaseSourceOperator

class BaseRanobeParser[SO: "BaseSourceOperator", CSM: "BaseModel"](BaseParser[SO, CSM]):
	"""Базовый парсер ранобэ."""

	@override
	def init_empty_title(self, slug: str) -> Ranobe:
		"""
		Устанавливает пустой тайтл для парсера.

		:param slug: Алиас тайтла.
		:type slug: str
		:return: Тайтл.
		:rtype: Ranobe
		"""

		self._title = Ranobe(self, slug)

		return self._title

	@override
	@run_before_method("_require_title")
	def repair(self, chapter_id: int) -> bool:
		"""
		Восстанавливает содержимое главы, заново получая его из источника.

		:param chapter_id: Уникальный идентификатор целевой главы.
		:type chapter_id: int
		:raises ChapterNotFound: В локальном JSON не найдена глава с указанным ID.
		:return: Возвращает `True`, если глава содержит контент после восстановления.
		:rtype: bool
		"""

		Title = cast("Ranobe", self._title)

		SearchResult = Title.data.find_chapter(chapter_id)

		if not SearchResult:
			raise exceptions.parsing.ChapterNotFound(chapter_id)

		AmendedChapter = cast("Chapter", SearchResult.chapter)
		AmendedChapter.clear()
		self._amend(SearchResult.branch, AmendedChapter)
		
		return bool(AmendedChapter.paragraphs)