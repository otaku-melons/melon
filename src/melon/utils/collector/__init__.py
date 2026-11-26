import os
from collections.abc import Callable, Sequence
from json import JSONDecodeError
from pathlib import Path
from typing import TYPE_CHECKING

from dublib.functions.data import to_sequence
from dublib.functions.filesystem import json, text

from ...core.base.structs.title import TitleDescriptor
from .structs import CollectingResult

if TYPE_CHECKING:
	from ...core.base.source_operator import BaseSourceOperator

class Collector:
	"""Titles slugs collector."""

	def __init__(self, source_operator: "BaseSourceOperator", filename: str | None = None, sync: bool = True):
		"""
		Titles slugs collector.

		Args:
			source_operator (BaseSourceOperator): Source operator.
			filename (str | None): Collection filename. By default `collection`.
			sync (bool): Sync all changes with collection file.
		"""

		self.__source_operator = source_operator
		self.__filename: str = filename or "collection"
		self.__sync: bool = sync

		if self.__filename.endswith(".txt"):
			self.__filename = Path(self.__filename).stem

		self.__collections_directory: Path = self.__source_operator.system_objects.temper.get_parser_collections_directory(self.__source_operator.parser_name)
		self.__collection_file: Path = self.__collections_directory / f"{self.__filename}.txt"
		self.__cache_file: Path = self.__source_operator.temp_directory / f".{self.__filename}.cache.txt"

		self.__collection: list[str] = []

		if self.is_synced:
			self.load()

	def add(self, slugs: str | Sequence[str]) -> int:
		"""
		Add slugs to collection and sorts collection by ascendence.

		Args:
			slugs (str | Sequence[str]): Slugs.

		Returns:
			int: Unique added slugs count.
		"""

		slugs_set: set = to_sequence(slugs, target_type = set)
		collection_set: set = set(self.__collection)
		unique_slugs_set: set = slugs_set - collection_set

		self.__collection = sorted(collection_set | slugs_set)
		if self.is_synced: self.save()

		return len(unique_slugs_set)

	def collect_broken(self) -> CollectingResult:
		"""
		Собирает из локальной директории тайтлов алиасы по правилу: повреждённые файлы.

		Поскольку из повреждённых файлов невозможно извлечь алиас, при использовании ID в качестве имён описательных файлов никогда ничего не добавляет во внутреннюю коллекцию.

		:return: Результат сборки тайтлов из каталога.
		:rtype: CollectingResult
		"""

		Descriptors: tuple[TitleDescriptor, ...] = self.__collect_descriptors()

		for Descriptor in Descriptors:
			if not Descriptor.extra.get("is_broken"):
				self.__try_get_slug_from_file(Descriptor)

		Descriptors = tuple(Descriptor for Descriptor in Descriptors if Descriptor.extra.get("is_broken"))

		return self.__build_result_from_descriptors(Descriptors)

	def collect_local(self) -> CollectingResult:
		"""
		Собирает из локальной директории тайтлов алиасы по правилу: все файлы.

		:return: Результат сборки тайтлов из каталога.
		:rtype: CollectingResult
		"""

		return self.__build_result_from_descriptors(self.__collect_descriptors())

	def collect_not_found(self, autosave: bool = True, callback: Callable[[TitleDescriptor], None] | None = None) -> CollectingResult:
		"""
		Собирает из локальной директории тайтлов алиасы по правилу: не найденные на сервере тайтлы.

		Для проверки использует метод оператора источника `is_title_exists()`. Если алиас найден во внутренней коллекции, проверка будет пропущена.

		В экстра-данные дескрипторов тайтлов добавляет поле _is_title_exists_ со статусом проверки существования.

		:param autosave: Сохраняет файл коллекции после каждого изменения.
		:type autosave: bool
		:param callback: Функция, принимающая проверенный дескриптор.
		:type callback: Callable[[TitleDescriptor], None] | None
		:return: Результат сборки тайтлов из каталога.
		:rtype: CollectingResult
		"""

		NotFoundDescriptors: list[TitleDescriptor] = []
		Added: int = 0

		cached_slugs: tuple[str, ...] = self.__read_cached_slugs()

		for Descriptor in self.__collect_descriptors():
			if not Descriptor.slug or Descriptor.slug in self.__collection: continue
			if Descriptor.slug in cached_slugs: continue

			IsTitleExists: bool | None = self.__source_operator.is_title_exists(Descriptor.slug)
			Descriptor.extra["is_title_exists"] = IsTitleExists

			if IsTitleExists is False:
				NotFoundDescriptors.append(Descriptor)

				if autosave:
					self.add(Descriptor.slug)
					Added += 1

			self.__save_progress_in_cache(Descriptor.slug)
			if callback: callback(Descriptor)

		Slugs = tuple(Descriptor.slug for Descriptor in NotFoundDescriptors if Descriptor.slug)
		self.__clear_cache()

		return CollectingResult(
			slugs = Slugs,
			added = Added if autosave else self.add(Slugs),
			descriptors = tuple(NotFoundDescriptors),
		)

	def clear(self):
		"""Clear collection data and remove file if exists."""

		self.__collection.clear()
		self.__collection_file.unlink(missing_ok = True)

	def load(self) -> int:
		"""
		Load slugs from collection file.

		Returns:
			int: Unique added slugs count.
		"""

		if self.is_collection_file_exists:
			file_slugs: list[str] = text.read(self.__collection_file, split = True, strip_level = 2)
			return self.add(file_slugs)

		return 0

	def replace(self, slug: str, new_slug: str) -> bool:
		"""
		Replace slug by new value.

		Args:
			slug (str): Slug.
			new_slug (str): New slug.

		Returns:
			bool: `True` if slug found and replaced.
		"""

		if slug not in self.__collection:
			return False

		self.__collection.remove(slug)
		self.add(new_slug)
		if self.is_synced: self.save()

		return True

	def save(self):
		"""Save collection to file."""

		text.write(self.__collection_file, self.__collection)

	@property
	def count(self) -> int:
		"""Slugs count."""

		return len(self.__collection)

	@property
	def is_operation_cached(self) -> bool:
		"""
		Condition: is cache used for operations.

		Caching used inly for `collect_not_found()` method.

		Always returns `False` if `MELON_USE_CACHE` option disabled.
		"""

		if not self.__source_operator.system_objects.options.USE_CACHE:
			return False

		return self.__cache_file.exists()

	@property
	def is_collection_file_exists(self) -> bool:
		"""Condition: is collection file exists."""

		return self.__collection_file.exists()

	@property
	def is_synced(self) -> bool:
		"""Condition: is collection synced with file."""

		return self.__sync

	@property
	def name(self) -> str:
		"""Collection name (file name without suffix)."""

		return self.__filename

	@property
	def slugs(self) -> tuple[str, ...]:
		"""Collection slugs."""

		return tuple(self.__collection)

	def __build_result_from_descriptors(self, descriptors: Sequence[TitleDescriptor]) -> CollectingResult:
		"""
		Строит результат коллекционирования из дескрипторов тайтлов.

		:param descriptors: Последовательность дескрипторов тайтлов.
		:type descriptors: Sequence[TitleDescriptor]
		:return: Результат сборки тайтлов из каталога.
		:rtype: CollectingResult
		"""

		Slugs = tuple(Descriptor.slug for Descriptor in descriptors if Descriptor.slug)

		return CollectingResult(
			slugs = Slugs,
			added = self.add(Slugs),
			descriptors = tuple(descriptors),
		)

	def __collect_descriptors(self) -> tuple[TitleDescriptor, ...]:
		"""
		Строит последовательность дескрипторов локальных тайтлов.

		:return: Последовательность дескрипторов локальных тайтлов.
		:rtype: tuple[TitleDescriptor, ...]
		"""

		Directory: Path = self.__source_operator.settings.directories.titles
		Descriptors: list[TitleDescriptor] = []

		for Entry in os.scandir(Directory):
			if Entry.is_file() and Entry.name.endswith(".json"):
				Buffer = TitleDescriptor(self.__source_operator)
				Buffer.set_filename(Entry.name)
				Descriptors.append(Buffer)

		if self.__source_operator.settings.common.use_id_as_filename:
			for Descriptor in Descriptors:
				self.__try_get_slug_from_file(Descriptor)

		return self.__sort_descriptors(Descriptors)

	def __sort_descriptors(self, descriptors: Sequence[TitleDescriptor]) -> tuple[TitleDescriptor, ...]:
		"""
		Сортирует последовательность дескрипторов тайтлов по их алиасам (`None` в начале).

		:param descriptors: Последовательность дескрипторов тайтлов.
		:type descriptors: Sequence[TitleDescriptor]
		:return: Отсортированная последовательность дескрипторов тайтлов.
		:rtype: tuple[TitleDescriptor, ...]
		"""
		return tuple(sorted(descriptors, key = lambda Descriptor: (Descriptor.slug is not None, Descriptor.slug)))

	def __try_get_slug_from_file(self, descriptor: TitleDescriptor):
		"""
		Пытается получить алиас тайтла из ключа _slug_ JSON-файла.

		В экстра-данные дескриптора тайтла добавляет поле _is_broken_ с соответствующим статусом.

		:param descriptor: Дескриптор тайтла.
		:type descriptor: TitleDescriptor
		"""

		if descriptor.slug or not descriptor.path:
			return

		try:
			Title = json.read(descriptor.path)
			descriptor.extra["is_broken"] = False
			Slug = Title.get("slug")
			if Slug: descriptor.set_slug(Slug)

		except JSONDecodeError: descriptor.extra["is_broken"] = True
		except FileNotFoundError: pass

	def __clear_cache(self):
		"""Очищает кэш операции."""

		self.__cache_file.unlink(missing_ok = True)

	def __read_cached_slugs(self) -> tuple[str, ...]:
		"""
		Считывает кэш сборки.

		Отключается переменной среды `MELON_USE_CACHE`.

		:return: Последовательность обработанных алиасов.
		:rtype: tuple[str, ...]
		"""

		if not self.__source_operator.system_objects.options.USE_CACHE:
			return ()

		if not self.is_operation_cached:
			return ()

		return tuple(text.read(self.__cache_file, split = True, strip_level = 2))

	def __save_progress_in_cache(self, checked_slug: str):
		"""
		Сохраняет прогресс сборки коллекции в кэш.

		:param checked_slug: Обработанный алиас.
		:type checked_slug: str
		"""

		if not self.__cache_file.exists():
			with open(self.__cache_file, "w", encoding = "utf-8") as writer:
				writer.write(checked_slug + "\n")

		else:
			with open(self.__cache_file, "a", encoding = "utf-8") as writer:
				writer.write(checked_slug + "\n")

