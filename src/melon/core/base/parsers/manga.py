from typing import TYPE_CHECKING, cast, override

from ....core import exceptions
from ..formats.manga.controller import Manga
from .base_parser import BaseParser

if TYPE_CHECKING:
	from pydantic import BaseModel

	from ..formats.base_format.controller import BaseTitleController
	from ..formats.manga.chapter import Chapter
	from ..source_operator import BaseSourceOperator

class BaseMangaParser[SO: "BaseSourceOperator", CSM: "BaseModel"](BaseParser[SO, CSM, Manga]):
	"""Базовый парсер манги."""

	@override
	def init_empty_title(self, slug: str) -> "BaseTitleController":
		"""
		Устанавливает пустой тайтл для парсера.

		:param slug: Алиас тайтла.
		:type slug: str
		:return: Тайтл.
		:rtype: BaseTitleController
		"""

		self._title = Manga(self, slug)

		return self._title

	@override
	def repair(self, chapter_id: int) -> bool:
		"""
		Восстанавливает содержимое главы, заново получая его из источника.

		:param chapter_id: Уникальный идентификатор целевой главы.
		:type chapter_id: int
		:raises ChapterNotFoundError: В локальном JSON не найдена глава с указанным ID.
		:return: Возвращает `True`, если глава содержит контент после восстановления.
		:rtype: bool
		"""

		search_result = self.title.data.find_chapter(chapter_id)

		if not search_result:
			raise exceptions.parsing.ChapterNotFoundError(chapter_id)

		chapter = cast("Chapter", search_result.chapter)
		chapter.clear()

		self._amend(search_result.branch, chapter)

		return bool(chapter.slides)
