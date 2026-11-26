import hashlib
import os
import shutil
from abc import ABC, abstractmethod
from json import JSONDecodeError
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, cast

import orjson

from dublib.functions.data import zerotify
from dublib.functions.filesystem import json

from ....html.interpreter import HyperTextInterpreter
from ...structs.image import ImageType
from .enums import By
from .structs import SavingResult

if TYPE_CHECKING:
	from os import PathLike

	from pydantic import BaseModel

	from ....system_objects.temper.journal import Journal
	from ...parser import BaseParser
	from ...source_operator import BaseSourceOperator
	from .data import BaseTitleData

class BaseTitleController[TD: "BaseTitleData"](ABC):
	"""Base title controller."""

	def __init__(self, parser: "BaseParser", slug: str):

		self._parser: BaseParser[BaseSourceOperator, BaseModel, BaseTitleController] = parser
		self._slug: str = slug

		self._interpreter: HyperTextInterpreter = HyperTextInterpreter()

		self._data: TD = self._export_data_type()(
			title_controller = self,
			title_format = "melon-" + type(self).__name__.lower(),
		)
		self._data.set_domain(self._parser.manifest.domain)
		self._data.set_slug(self._slug)

		self._local_file_path: Path | None = None

		self._post_init()

	def get_images_type_directory(self, images_type: ImageType, create: bool = True) -> Path:
		"""
		Возвращает путь к директории типа изображений, автоматически создаёт её.

		:param images_type: Тип изображений.
		:type images_type: ImageType
		:param create: Указывает, пытаться ли создавать директорию.
		:type create: bool
		:return: Путь к существующей директории типа изображений.
		:rtype: Path
		"""

		directory = self.images_directory / images_type.value
		if create: directory.mkdir(exist_ok = True)

		return directory

	def load(self, identifier: int | str, selector_type: By = By.Slug) -> bool:
		"""
		Load title data from descriptive JSON file.

		Args:
			identifier (int | str): Title identifier.
			selector_type (By): Identifier type.

		Returns:
			bool: `True` if data loaded.
		"""

		data: dict | None = self._load_raw_data(identifier, selector_type)

		if data:
			self._data.from_dict(data)

		return bool(data)

	def merge(self) -> int:  # noqa: C901
		"""
		Merge title chapters content from descriptive file if exists.

		Returns:
			int: Count of merged chapters.
		"""

		data: dict | None = self._load_raw_data(self._slug)

		if not data:
			return 0

		#---> Слияние размеров обложек.
		#==========================================================================================#
		CoversData: list[dict] = data["covers"]

		for CoverData in CoversData:
			Link = CoverData["link"]
			TargetCover = self._data.find_cover(Link)

			if TargetCover:
				TargetCover.create_resolution(CoverData.get("width"), CoverData.get("height"))

		#---> Слияние размеров портретов персонажей.
		#==========================================================================================#
		PersonsData: list[dict] | None = data.get("persons")

		if PersonsData:
			for PersonData in PersonsData:
				PersonObject = self._data.find_person(PersonData["name"])
				if not PersonObject: continue

				for CurrentImage in cast("list[dict]", PersonData["images"]):
					Link = CurrentImage["link"]
					TargetImage = PersonObject.find_image(Link)

					if TargetImage:
						TargetImage.create_resolution(CurrentImage.get("width"), CurrentImage.get("height"))

		#---> Слияние контента глав.
		#==========================================================================================#
		ContentData: dict[str, dict] = data["content"]
		MergedChaptersCount: int = 0

		for BranchKey in ContentData.keys():
			for ChapterData in ContentData[BranchKey]:
				ChapterID = int(ChapterData["id"])

				SearchResult = self._data.find_chapter(ChapterID)

				if SearchResult and SearchResult.chapter.is_empty:
					SearchResult.chapter.from_dict(ChapterData)
					MergedChaptersCount += 1

		return MergedChaptersCount

	def remove_images_type_directory(self, images_type: ImageType):
		"""
		Удаляет директорию типа изображений со всем содержимым.

		:param images_type: Тип изображений.
		:type images_type: ImageType
		"""

		directory = self.get_images_type_directory(images_type, create = False)

		if directory.exists():
			shutil.rmtree(directory)

	def save(self, sorting: bool = False) -> SavingResult:
		"""
		Сохраняет данные тайтла в локальный файл JSON.

		:param sorting: Указывает, нужно ли провести сортировку глав на основе их нумерации.
		:type sorting: bool
		:return: Результат сохранения тайтла.
		:rtype: SavingResult
		"""

		self._sort_attributes()
		data: dict[str, Any] = self._data.to_dict(sorting)

		is_local_file_equal: bool = self._is_local_file_equal(data)
		is_slug_changed: bool = False
		is_local_file_renamed: bool = False

		if self._data.slug != self._slug:
			is_slug_changed = True

		if not is_local_file_equal:
			json.write(self.path, data, atomic = self._parser.portals.printer.system_objects.options.ATOMIC_WRITE)

		if not self._parser.settings.common.use_id_as_filename and is_slug_changed:
			original_path = self.path
			new_path = original_path.with_stem(self._data.slug)
			original_path.rename(new_path)
			self._slug = self._data.slug
			is_local_file_renamed = True

		self._update_journal()

		return SavingResult(
			is_saved = not is_local_file_equal,
			is_slug_changed = self.data.slug if is_slug_changed else None,
			is_local_file_renamed = is_local_file_renamed,
			unused_images_removed = self._clear_unused_images(),
		)

	@property
	def chapters_count(self) -> int:
		"""Chapters count in all branches."""

		return sum(branch.chapters_count for branch in self.data.branches)

	@property
	def data(self) -> TD:
		"""Title data."""

		return self._data

	@property
	def empty_chapters_count(self) -> int:
		"""Empty chapters count in all branches."""

		return sum(branch.empty_chapters_count for branch in self._data.branches)

	@property
	def html_interpreter(self) -> HyperTextInterpreter:
		"""HTML lines into elements interpreter."""

		return self._interpreter

	@property
	def images_directory(self) -> Path:
		"""Путь к директории изображений тайтла."""

		directory = self._parser.settings.directories.images / self.used_filename
		directory.mkdir(exist_ok = True)

		return directory

	@property
	def is_local_file_loaded(self) -> bool:
		"""Состояние: считывались ли данные из локального файла."""

		return bool(self._local_file_path)

	@property
	def parser(self) -> "BaseParser":
		"""Парсер."""

		return self._parser

	@property
	def path(self) -> Path:
		"""Путь к файлу."""

		return self._parser.settings.directories.titles / f"{self.used_filename}.json"

	@property
	def used_filename(self) -> str:
		"""Используемое имя файла."""

		if self._parser.settings.common.use_id_as_filename and self._data.id is not None:
			return str(self._data.id)

		return self._slug

	def _clear_unused_images(self) -> int:
		"""
		Удаляет неиспользуемые файлы изображений в стандартных каталогах и пустые папки.

		:return: Количество удалённых файлов.
		:rtype: int
		"""

		unused_files_removed: int = self._clear_unused_covers_images()
		unused_files_removed += self._clear_unused_persons_images()
		self._remove_empty_images_directories()

		return unused_files_removed

	def _clear_unused_covers_images(self) -> int:
		"""
		Удаляет неиспользуемые изображения обложек.

		:return: Количество удалённых файлов.
		:rtype: int
		"""

		covers_directory = self.images_directory / "covers"

		if not covers_directory.exists():
			return 0

		used_files: tuple[str, ...] = tuple(cover.filename for cover in self.data.covers)
		unused_files_count: int = 0

		for file in os.listdir(covers_directory):
			if file not in used_files:
				unused_files_count += 1
				unused_file = covers_directory / file
				unused_file.unlink(missing_ok = True)

		return unused_files_count

	def _clear_unused_persons_images(self) -> int:
		"""
		Удаляет неиспользуемые изображения персонажей.

		:return: Количество удалённых файлов.
		:rtype: int
		"""

		persons_directory = self.images_directory / "persons"

		if not persons_directory.exists():
			return 0

		used_files: list[str] = []
		unused_files_count: int = 0

		for person in self.data.perons:
			for image in person.images:
				used_files.append(image.filename)

		for file in os.listdir(persons_directory):
			if file not in used_files:
				unused_files_count += 1
				unused_file = persons_directory / file
				unused_file.unlink(missing_ok = True)

		return unused_files_count

	@abstractmethod
	def _export_data_type(self) -> type[TD]:
		"""
		Экспортирует тип данных тайтла.

		:return: Тип данных тайтла.
		:rtype: type[BaseTitleData]
		"""

		pass

	def _is_local_file_equal(self, data: dict) -> bool:
		"""
		Проверяет, идентичны ли данные тайтла локальным данным.

		:param data: Словарное представление данных тайтла.
		:type data: dict
		:return: Возвращает `True`, если данные идентичны, или `False` в противном случа и при отсутствии локального файла.
		:rtype: bool
		"""

		if not self.path.exists():
			return False

		try:
			local_hash = hashlib.sha256(orjson.dumps(json.read(self.path)))
			memore_hash = hashlib.sha256(orjson.dumps(data))

		except orjson.JSONDecodeError:
			return False

		return local_hash.hexdigest() == memore_hash.hexdigest()

	def _load_data_by_filename(self, filename: str) -> dict | None:

		Filename: str = filename if filename.endswith(".json") else f"{filename}.json"
		FilePath = self._parser.settings.directories.titles / Filename

		if FilePath.exists():
			self._local_file_path = FilePath
			return json.read(FilePath)

	def _load_data_by_id(self, title_id: int) -> dict | None:

		Journal = self._parser.source_operator.shared_data.journal
		TitlesDirectory = self._parser.settings.directories.titles

		if not self._parser.settings.common.use_id_as_filename:
			Slug = Journal.get_slug_by_id(title_id)

			if Slug:
				FilePath = TitlesDirectory / f"{Slug}.json"
				if FilePath.exists(): return json.read(FilePath)

		else:
			FilePath = TitlesDirectory / f"{title_id}.json"
			if FilePath.exists(): return json.read(FilePath)

		return self._search_file_in_directory(TitlesDirectory, title_id, By.ID) or {}

	def _load_data_by_slug(self, slug: str) -> dict | None:
		"""
		Load title raw data by slug.

		Args:
			slug (str): Title slug.

		Returns:
			dict | None: Title raw data or `None` if unable.
		"""

		journal: Journal = self._parser.source_operator.shared_data.journal
		titles_directory: Path = self._parser.settings.directories.titles

		if self._parser.settings.common.use_id_as_filename:
			title_id: int | None = journal.get_id_by_slug(slug)

			if title_id:
				file_path: Path = titles_directory / f"{title_id}.json"

				if file_path.exists():
					return json.read(file_path)

		else:
			file_path: Path = titles_directory / f"{slug}.json"

			if file_path.exists():
				return json.read(file_path)

		return self._search_file_in_directory(titles_directory, slug, By.Slug)

	def _load_raw_data(self, identifier: int | str, selector_type: By = By.Slug) -> dict | None:
		"""
		Load title raw data from descriptive JSON file.

		Args:
			identifier (int | str): Title identifier: slug or ID.
			selector_type (By): Selector type for title loading.

		Returns:
			dict | None: Loaded raw data or `None` if not found.

		Raises:
			TypeError: Identifier type isn't correct for selector.
		"""

		data: dict | None = None

		match selector_type:

			case By.Filename:

				if not isinstance(identifier, str):
					raise TypeError("Filename must be str.")

				data = self._load_data_by_filename(identifier)

			case By.Slug:

				if not isinstance(identifier, str):
					raise TypeError("Slug must be str.")

				data = self._load_data_by_slug(identifier)

			case By.ID:

				if not isinstance(identifier, int):
					raise TypeError("ID must be int.")

				data = self._load_data_by_id(identifier)

		return zerotify(data)

	# OVERRIDABLE
	def _post_init(self):
		"""Execute after instance initialization."""

		pass

	def _remove_empty_images_directories(self):
		"""Удаляет пустые каталоги в директории изображений тайтла и саму директорию, если пуста."""

		images_directory = self.images_directory

		for entry_point in os.scandir(images_directory):
			if not entry_point.is_dir(): continue
			directory = Path(entry_point.path)

			if not any(directory.iterdir()):
				directory.rmdir()

		if not any(images_directory.iterdir()):
			images_directory.rmdir()

	def _search_file_in_directory(self, directory: Path, identifier: int | str, identifier_type: Literal[By.ID, By.Slug]) -> dict | None:
		"""
		Search descriptive file in directory and read it's content.

		If `MELON_USE_CACHE` options enabled, always return `None`.

		Args:
			directory (Path): Directory path.
			identifier (int | str): Title identifier: slug or ID.
			identifier_type (Literal[By.ID, By.Slug]): Supported selector type for loading.

		Returns:
			dict | None: Title data or `None` if not found.
		"""

		if self._parser.source_operator.system_objects.options.USE_CACHE:
			return

		for entry in os.scandir(directory):

			if not entry.is_file() or not entry.name.endswith(".json"):
				continue

			data: dict | None = self._try_read_json(entry.path)

			if not data:
				continue

			if data.get(identifier_type.value) == identifier:
				self._local_file_path = Path(entry.path)
				return data

	def _sort_attributes(self):
		"""Sort title attributes."""

		self._data.set_genres(sorted(self._data.genres))
		self._data.set_tags(sorted(self._data.tags))
		self._data.set_franchises(sorted(self._data.franchises))

		self._data.set_persons(
			sorted(self._data.perons, key = lambda person: person.name),
		)

	def _try_read_json(self, file: "PathLike[str] | str") -> dict | None:
		"""
		Try read JSON file (only dictionary-like).

		Args:
			file (PathLike[str] | str): Path to JSON file.

		Returns:
			dict | None: JSON data or `None` if not found or broken.
		"""

		if Path(file).exists():
			try:
				return json.read(file)
			except JSONDecodeError:
				pass

	def _update_journal(self):
		"""Обновляет кэш пары алиас-ID."""

		if self._data.id:
			self._parser.source_operator.shared_data.journal.update(self._data.id, self._data.slug)
