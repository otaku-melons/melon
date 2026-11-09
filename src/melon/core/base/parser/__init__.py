from abc import ABC, abstractmethod
from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ....core import exceptions
from ...system_objects.manager.extensions.enums import ParsingStep
from ..formats.base_format.branch import Branch
from ..formats.base_format.data import BaseTitleData
from .components.images_downloader import (
	ImageDownloadingResult,
	ImagesDownloader,
)
from .enums import ContentType, ImagesLevel

if TYPE_CHECKING:
	from pydantic import BaseModel

	from dublib.web_requestor import WebRequestor

	from ....core.base.formats.base_format.chapter import BaseChapter
	from ....core.base.formats.base_format.data import BaseTitleData
	from ....core.base.formats.base_format.structs import SavingResult
	from ....core.system_objects.printer import Portals
	from ..formats.base_format.controller import BaseTitleController
	from ..source_operator import BaseSourceOperator
	from ..structs.image import ImageData
	from .components.manifest import ParserManifest
	from .components.settings import ParserSettings

class BaseParser[SO: "BaseSourceOperator", CSM: "BaseModel", T: "BaseTitleController[BaseTitleData[BaseChapter]]"](ABC):
	"""Base parser."""

	def __init__(self, source_operator: SO, force_mode: bool, images_level: ImagesLevel | None):
		"""
		Base parser.

		Args:
			source_operator (SO): Source operator.
			force_mode (bool): Condition: is file overwriting enabled.
			images_level (ImagesLevel | None): Images downloading level.
		"""

		self._source_operator: SO = source_operator
		self._force_mode: bool = force_mode
		self._images_level: ImagesLevel = images_level or ImagesLevel.NO

		self._title: T | None = None

		self._post_init()

	def amend(self):
		"""Amend empty chapters with content."""

		self._run_extensions_methods(ParsingStep.BeforeAmending)

		empty_chapters: list[tuple[Branch, BaseChapter]] = []

		for branch in self.title.data.branches:
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

				if self._images_level is ImagesLevel.ALL:
					self._download_images(chapter.images, subdir = str(chapter.id))

		self.portals.printer.templates.parsing.amending_end(amended_chapters_count)

		self._run_extensions_methods(ParsingStep.AfterAmending)

	def download_metainfo_images(self) -> "tuple[ImageDownloadingResult, ...]":
		"""
		Download title metainfo images.

		Returns:
			tuple[ImageDownloadingResult, ...]: _description_
		"""

		if self._images_level is ImagesLevel.NO:
			return ()

		covers_results = self._download_images(self.title.data.covers)
		self._unstub_covers(self.title, covers_results)

		persons_images: list[ImageData] = []
		for person in self.title.data.perons:
			persons_images += person.images

		persons_results = self._download_images(persons_images)
		self._unstub_persons(self.title.data, persons_results)

		return tuple(covers_results + persons_results)

	def get_title(self) -> T | None:
		"""
		Get title which is set for parser.

		Returns:
			T | None: Title.
		"""

		return self._title

	def init_empty_title(self, slug: str) -> "BaseTitleController":
		"""
		Устанавливает пустой тайтл для парсера.

		:param slug: Алиас тайтла.
		:type slug: str
		:return: Тайтл.
		:rtype: BaseTitleController
		"""

		self._title = self._export_controller_type()(self, slug)

		return self._title

	def parse(self):
		"""Получает основные данные тайтла."""

		self._run_extensions_methods(ParsingStep.BeforeParsing)

		self._parse()

		self._run_extensions_methods(ParsingStep.AfterParsing)

	def repair(self, chapter_id: int) -> bool:
		"""
		Repair chapter content.

		Args:
			chapter_id (int): Chapter ID.

		Raises:
			ChapterNotFoundError: Target chapter not found.

		Returns:
			bool: `True` if chapter isn't empty after repairing.
		"""

		search_result = self.title.data.find_chapter(chapter_id)

		if not search_result:
			raise exceptions.parsing.ChapterNotFoundError(chapter_id)

		chapter = search_result.chapter
		chapter.clear()

		self._amend(search_result.branch, chapter)

		if not chapter.is_empty and self._images_level is ImagesLevel.ALL:
			self._download_images(chapter.images, str(chapter_id))

		return not chapter.is_empty

	def save(self, sorting: bool = False) -> "SavingResult":
		"""
		Сохраняет тайтл и выгружает его из парсера.

		:param sorting: Указывает, нужно ли провести сортировку глав на основе их нумерации.
		:type sorting: bool
		:return: Результат сохранения тайтла.
		:rtype: SavingResult
		"""

		self._run_extensions_methods(ParsingStep.BeforeSaving)

		self._pre_saver()
		result = self.title.save(sorting)
		self._title = None

		self._run_extensions_methods(ParsingStep.AfterSaving)

		return result

	@property
	def content_type(self) -> ContentType:
		"""Content type."""

		return self._export_content_type()

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

		return self._source_operator.system_objects.temper.get_parser_temp_directory(self._source_operator.parser_name)

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

	@abstractmethod
	def _amend(self, branch: Branch, chapter: Any) -> str | None:
		"""
		Amend chapter content.

		Args:
			branch (Branch): Branch.
			chapter (Any): Chapter

		Returns:
			str | None: Optional additional message about amending result.
		"""

		pass

	def _download_images(self, images_data: Sequence["ImageData"], subdir: str | None = None) -> list[ImageDownloadingResult]:
		"""
		Download images sequence.

		Args:
			images_data (Sequence[ImageData]): Images data.
			subdir (str | None): Subdirectory name to storage files. Required for chapters images.

		Returns:
			list[ImageDownloadingResult]: Images downloadings results.
		"""

		if not images_data:
			return []

		results: list[ImageDownloadingResult] = []
		images_count: int = len(images_data)

		for index in range(images_count):
			image_data = images_data[index]

			future = self.portals.printer.templates.images.start_downloading(image_data.filename, image_data.image_type)
			result = self._source_operator.images_downloader.download_image_from_data(
				data = image_data,
				title = self.title,
				subdir = subdir,
				force_mode = self._force_mode,
			)
			results.append(result)
			future.result(result)

		return results

	@abstractmethod
	def _export_content_type(self) -> ContentType:
		"""
		Export content type.

		Returns:
			ContentType: Content type.
		"""

		pass

	@abstractmethod
	def _export_controller_type(self) -> type[T]:
		"""
		Export chapter controller type.

		Returns:
			type[BaseChapterController]: Chapter controller type.
		"""

		pass

	@abstractmethod
	def _parse(self):
		"""Parse title data witchout chapters content."""

		pass

	# OVERRIDABLE
	def _post_init(self):
		"""Execute after instance initialization."""

		pass

	# OVERRIDABLE
	def _pre_saver(self):
		"""Run before title saving in descriptive JSON file."""

		pass

	def _run_extensions_methods(self, step: ParsingStep):
		"""
		Run registered extensions methods.

		Args:
			step (ParsingStep): Parsing step.
		"""

		self.source_operator.parser_operator.extensions.run_step_methods(step, self)

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
