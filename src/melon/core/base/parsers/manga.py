from typing import TYPE_CHECKING, cast, override

from dublib.functions.decorators import run_before_method

from ....core import exceptions
from ..formats.manga.controller import Manga
from .base_parser import BaseParser

if TYPE_CHECKING:
	from pydantic import BaseModel

	from ..formats.manga.chapter import Chapter
	from ..source_operator import BaseSourceOperator

class BaseMangaParser[SO: "BaseSourceOperator", CSM: "BaseModel"](BaseParser[SO, CSM]):
	"""Базовый парсер манги."""

	@override
	def init_empty_title(self, slug: str) -> Manga:
		"""
		Устанавливает пустой тайтл для парсера.

		:param slug: Алиас тайтла.
		:type slug: str
		:return: Тайтл.
		:rtype: Manga
		"""

		self._title = Manga(self, slug)

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

		title = cast("Manga", self._title)

		search_result = title.data.find_chapter(chapter_id)

		if not search_result:
			raise exceptions.parsing.ChapterNotFound(chapter_id)

		chapter = cast("Chapter", search_result.chapter)
		chapter.clear()
		
		self._amend(search_result.branch, chapter)
		
		return bool(chapter.slides)