from abc import ABC, abstractmethod
from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ....core import exceptions
from ..formats.base_format.branch import Branch
from ..formats.base_format.data import BaseTitleData
from ..parsers.components.images_downloader import (
	ImageDownloadingResult,
	ImagesDownloader,
)
from ..structs.image import ImageData, ImageType

if TYPE_CHECKING:
	from pydantic import BaseModel

	from dublib.web_requestor import WebRequestor

	from ....core.base.formats.base_format.chapter import BaseChapter
	from ....core.base.formats.base_format.data import BaseTitleData
	from ....core.base.formats.base_format.structs import SavingResult
	from ....core.base.parsers.components.manifest import ParserManifest
	from ....core.base.parsers.components.settings import ParserSettings
	from ....core.system_objects.printer import Portals
	from ..formats.base_format.controller import BaseTitleController
	from ..source_operator import BaseSourceOperator

class BaseParser[SO: "BaseSourceOperator", CSM: "BaseModel", T: "BaseTitleController[BaseTitleData[BaseChapter]]"](ABC):
	"""Base parser."""

	#==========================================================================================#
	# >>>>> PROPERTIES <<<<< #
	#==========================================================================================#

	@property
	def images_downloader(self) -> "ImagesDownloader":
		"""Оператор скачивания изображений."""

		return self._source_operator.images_downloader

	@property
	def manifest(self) -> "ParserManifest":
		"""Манифест парсера."""

		return self._source_operator.manifest

	@property
	def temp_directory(self) -> Path:
		"""Путь ко временному каталогу парсера."""

		return self._source_operator.system_objects.temper.get_parser_temp_directory(self.manifest.parser_name)

	@property
	def portals(self) -> "Portals":
		"""Порталы вывода парсера."""

		return self._source_operator.portals

	@property
	def requestor(self) -> "WebRequestor":
		"""Менеджер запросов."""

		return self._source_operator.requestor

	@property
	def settings(self) -> "ParserSettings[CSM]":
		"""Настройки парсера."""

		return self._source_operator.settings

	@property
	def source_operator(self) -> SO:
		"""Оператор источника."""

		return self._source_operator

	@property
	def title(self) -> T:
		"""
		Title controller.

		Raises:
			TitleNotSetError: Title required, but not set.
		"""

		if not self._title:
			raise exceptions.parsers.TitleNotSetError()

		return self._title

	#==========================================================================================#
	# >>>>> PROTECTED METHODS <<<<< #
	#==========================================================================================#

	def _download_images(self, images_data: Sequence[ImageData], images_type: ImageType, force_mode: bool) -> list[ImageDownloadingResult]:
		"""
		Скачивает изображения тайтла определённого типа.

		:param images_data: Данные изображений.
		:type images_data: Sequence[ImageData]
		:param images_type: Тип изображений.
		:type images_type: ImageType
		:param force_mode: Указывает, перезаписывать ли существующие файлы изображений.
		:type force_mode: bool
		:return: Список результатов скачивания изображений.
		:rtype: list[ImageDownloadingResult]
		"""

		if not images_data:
			return []

		title = self.title

		Results: list = []
		ImagesCount: int = len(images_data)

		for Index in range(ImagesCount):
			CurrentImageData = images_data[Index]

			Future = self.portals.printer.templates.images.start_downloading(CurrentImageData.filename, images_type)
			Result = self._source_operator.images_downloader.download_image_from_data(
				data = CurrentImageData,
				title = title,
				force_mode = force_mode,
			)
			Results.append(Result)

			if Result.resolution:
				CurrentImageData.set_resolution(Result.resolution)

			Future.result(Result)

			if Result.is_already_exists and not Result.is_downloaded:
				continue

		return Results

	def _unstub_covers(self, title: "BaseTitleController[BaseTitleData]", results: list[ImageDownloadingResult]):
		"""
		Обрабатывает результаты скачивания обложек. Если находит отфильтрованные, удаляет их данные.

		:param title: Тайтл.
		:type title: BaseTitleController
		:param results: Список результатов.
		:type results: list[ImageDownloadingResult]
		"""

		for result in results:
			if result.filtered_by:

				if self.source_operator.properties.one_cover:
					self.portals.covers_unstubbed(title)
					return

				title.data.remove_cover(result.url)
				if result.path: result.path.unlink(missing_ok = True)

	def _unstub_persons(self, title_data: "BaseTitleData", results: list[ImageDownloadingResult]):
		"""
		Обрабатывает результаты скачивания изображений персонажей. Если находит отфильтрованные, удаляет их данные.

		:param title_data: Данные тайтла.
		:type title_data: BaseTitleData
		:param results: Список результатов.
		:type results: list[ImageDownloadingResult]
		"""

		for result in results:
			if result.filtered_by:

				for person in title_data.perons:
					person.remove_image(result.url)
					if result.path: result.path.unlink(missing_ok = True)

	#==========================================================================================#
	# >>>>> OVVERRIDABLE METHODS <<<<< #
	#==========================================================================================#

	@abstractmethod
	def _amend(self, branch: Branch, chapter: Any) -> str | None:
		"""
		Amend chapter by content.

		:param branch: Title content branch.
		:type branch: Branch
		:param chapter: Chapter.
		:type chapter: Any
		:return: Optional additional message about amending result or `None`.
		:rtype: str | None
		"""

		pass

	@abstractmethod
	def _parse(self):
		"""Parse title data witchout chapters content."""

		pass

	def _post_init(self):
		"""Execute after instance initialization."""

		pass

	def _pre_saver(self):
		"""Run before title saving in descriptive JSON file."""

		pass

	#==========================================================================================#
	# >>>>> PUBLIC METHODS <<<<< #
	#==========================================================================================#

	def __init__(self, source_operator: SO):
		"""
		Базовый парсер.

		:param source_operator: Оператор источника.
		:type source_operator: source_operator
		"""

		self._source_operator = source_operator

		self._title: T | None = None

		self._post_init()

	def amend(self):
		"""Amend empty chapters with content."""

		title = self.title
		empty_chapters: list[tuple[Branch, BaseChapter]] = []

		for branch in title.data.branches:
			for chapter in branch.chapters:
				if chapter.is_empty:
					empty_chapters.append((branch, chapter))

		amended_chapters_count: int = 0
		empty_chapters_count: int = len(empty_chapters)

		for index in range(empty_chapters_count):
			branch, chapter = empty_chapters[index]
			message: str | None = self._amend(branch, chapter)
			progress: tuple[int, int] = (index + 1, empty_chapters_count)

			if not chapter.is_empty:
				self.portals.printer.templates.parsing.chapter_amended(chapter, progress, message)
				amended_chapters_count += 1

		self.portals.printer.templates.parsing.amending_end(amended_chapters_count)

	def download_images(self, force_mode: bool) -> "tuple[ImageDownloadingResult, ...]":
		"""
		Скачивает обложки и портреты персонажей.

		:param force_mode: Переключает режим перезаписи существующих изображений.
		:type force_mode: bool
		:return: Последовательность результатов скачивания.
		:rtype: tuple[ImageDownloadingResult, ...]
		"""

		covers_results = self._download_images(self.title.data.covers, ImageType.Cover, force_mode)
		self._unstub_covers(self.title, covers_results)

		persons_images: list[ImageData] = []
		for person in self.title.data.perons:
			persons_images += person.images

		persons_results = self._download_images(persons_images, ImageType.Person, force_mode)
		self._unstub_persons(self.title.data, persons_results)

		return tuple(covers_results + persons_results)

	@abstractmethod
	def init_empty_title(self, slug: str) -> "BaseTitleController":
		"""
		Устанавливает пустой тайтл для парсера.

		:param slug: Алиас тайтла.
		:type slug: str
		:return: Тайтл.
		:rtype: BaseTitleController
		"""

		pass

	def parse(self):
		"""Получает основные данные тайтла."""

		self._parse()

	@abstractmethod
	def repair(self, chapter_id: int) -> bool:
		"""
		Восстанавливает содержимое главы, заново получая его из источника.

		:param chapter_id: Уникальный идентификатор целевой главы.
		:type chapter_id: int
		:raises ChapterNotFoundError: В локальном JSON не найдена глава с указанным ID.
		:return: Возвращает `True`, если глава содержит контент после восстановления.
		:rtype: bool
		"""

		pass

	def save(self, sorting: bool = False) -> "SavingResult":
		"""
		Сохраняет тайтл и выгружает его из парсера.

		:param sorting: Указывает, нужно ли провести сортировку глав на основе их нумерации.
		:type sorting: bool
		:return: Результат сохранения тайтла.
		:rtype: SavingResult
		"""

		self._pre_saver()
		result = self.title.save(sorting)
		self._title = None

		return result
