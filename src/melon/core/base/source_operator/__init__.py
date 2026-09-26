import importlib
from abc import ABC, abstractmethod
from collections.abc import Sequence
from os import PathLike
from pathlib import Path
from typing import TYPE_CHECKING, overload

from dublib.exceptions.web_requestor import TokenExpiredError
from dublib.functions.filesystem import json
from dublib.validators import types
from dublib.web_requestor import WebConfig, WebLibs, WebRequestor

from ... import exceptions
from ..parsers.components.images_downloader import (
	ImageDownloadingResult,
	ImagesDownloader,
)
from ..parsers.components.manifest import ContentTypes, ParserManifest
from ..parsers.components.settings import ParserSettings
from ..structs.title import TitleDescriptor
from .properties import SourceProperties

if TYPE_CHECKING:
	from pydantic import BaseModel

	from ...system_objects import SystemObjects
	from ...system_objects.manager.parser.extensions import ExtensionsOperator
	from ...system_objects.printer import Portals
	from ...system_objects.temper import SharedData
	from ..extensions import BaseExtension
	from ..parsers.base_parser import BaseParser

__all__ = ["BaseSourceOperator", "SourceProperties"]

class BaseSourceOperator[CSM: "BaseModel"](ABC):
	"""Базовый оператор источника."""

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def extensions(self) -> "ExtensionsOperator":
		"""Оператор расширений."""

		return self._parser_operator.extensions

	@property
	def images_downloader(self) -> ImagesDownloader:
		"""Оператор скачивания изображений."""

		return self._ImagesDownloader

	@property
	def is_collector_implemented(self) -> bool:
		"""Состояние: переопределён ли метод `_CollectSlugs()`."""

		return type(self)._collect_slugs is not BaseSourceOperator._collect_slugs

	@property
	def manifest(self) -> ParserManifest:
		"""Манифест парсера."""

		return self._Manifest

	@property
	def parser_name(self) -> str:
		"""Имя парсера."""

		return self._Manifest.parser_name

	@property
	def portals(self) -> "Portals":
		"""Порталы вывода парсера."""

		return self._Portals

	@property
	def properties(self) -> SourceProperties:
		"""Свойства источника."""

		return self._Properties

	@property
	def requestor(self) -> WebRequestor:
		"""Менеджер запросов."""

		return self._Requestor

	@property
	def settings(self) -> ParserSettings[CSM]:
		"""Настройки парсера."""

		return self._Settings
	
	@property
	def shared_data(self) -> "SharedData":
		"""Разделяемые в контексте сессий одного парсера данные."""
		
		return self._SharedData

	@property
	def system_objects(self) -> "SystemObjects":
		"""Коллекция системных объектов."""

		return self._SystemObjects

	@property
	def temp_directory(self) -> Path:
		"""Путь ко временному каталогу парсера.."""
		
		return self._Temper.get_parser_temp_directory(self._Manifest.parser_name)

	#==========================================================================================#
	# >>>>> OVERRIDABLE METHODS <<<<< #
	#==========================================================================================#

	def _authorize(self):
		"""
		It is executed after `_InitializeRequestor()` and wrapped to catch `TokenExpiredError` exceptions.

		Used to set up authorization based on the _Authorization_ header.
		"""

		pass

	def _collect_slugs(self, period: int | None = None, filters: str | None = None, pages: int | None = None) -> Sequence[str]:  # noqa: ARG002
		"""
		Collect titles slug by parameters.

		:param period: Number of hours until the current moment, which constitutes the data parsing period.
		:type period: int | None
		:param filters: Filtering parameters. For more details see parser *README.md*.
		:type filters: str | None
		:param pages: Количество запрашиваемых страниц каталога.
		:type pages: int | None
		:return: Number of requested catalog pages.
		:rtype: Sequence[str]
		"""

		return ()

	@abstractmethod
	def _export_custom_settings_model(self) -> type[CSM]:
		"""
		Export custom parser settings [pydantic](https://github.com/pydantic/pydantic) model.

		:return: Custom parser settings model.
		:rtype: type[BaseModel]
		"""

		pass

	def _export_source_properties(self) -> SourceProperties:
		"""
		Export source properties.

		:return: Source properties.
		:rtype: SourceProperties
		"""

		return SourceProperties(
			one_cover = True,
		)

	def _extract_slug_from_string(self, string: str) -> str | None:
		"""
		Extract title slug from string. Can be used to extract slugs from links.

		:param string: String to extraction.
		:type string: str
		:return: Title slug or `None` if extracting failed or not implemented.
		:rtype: str | None
		"""

		return string

	def _initialize_requestor(self) -> WebRequestor:
		"""
		Initialize requests operator.

		:return: Requests operator.
		:rtype: WebRequestor
		"""

		Config = WebConfig()
		Config.select_lib(WebLibs.requests)
		Config.set_retries_count(self.settings.network.retries)
		Config.set_delay(self.settings.network.delay)
		Config.enable_proxy_protocol_switching(True)

		Config.headers.generate_user_agent(("desktop",))
		Config.headers.automatically_accept_client_hints(True)
		Config.headers.add("referer", f"https://{self.manifest.domain}/")
		
		WebRequestorObject = WebRequestor(Config)
		WebRequestorObject.add_proxies(self.settings.network.proxies)
		
		return WebRequestorObject

	def _is_title_exists(self, slug: str) -> bool | None:  # noqa: ARG002
		"""
		Check if title exists in source.

		:param slug: Title slug.
		:type slug: str
		:return: Return `True` if title exists in source or `None` if checking failed or not implemented.
		:rtype: bool | None
		"""

		return None

	def _post_init(self):
		"""Execute after instance initialization."""

		pass

	def _post_mirror_changing(self, mirror: str | None):
		"""
		Execute after mirror changing.

		:param mirror: Mirror domain.
		:type mirror: str | None
		"""

		pass

	def _temp_image(self, url: str, force_mode: bool = False) -> ImageDownloadingResult:
		"""
		Download image into parser temporary directory.

		:param url: Link to image.
		:type url: str
		:param force_mode: Enable images overwriting mode.
		:type force_mode: bool
		:return: Image downloading result.
		:rtype: ImageDownloadingResult
		"""

		return self._ImagesDownloader.temp_image(url, force_mode = force_mode)

	#==========================================================================================#
	# >>>>> PUBLIC METHODS <<<<< #
	#==========================================================================================#

	def __init__(self, system_objects: "SystemObjects", manifest: "ParserManifest"):
		"""
		Базовый оператор источника.

		:param system_objects: Коллекция системных объектов.
		:type system_objects: SystemObjects
		:param manifest: Манифест парсера.
		:type manifest: ParserManifest
		"""

		self._SystemObjects = system_objects
		self._Manifest = manifest

		self._Printer = self._SystemObjects.printer
		self._Temper = self._SystemObjects.temper
		
		self._Settings: ParserSettings[CSM] = ParserSettings(self._SystemObjects, self._Manifest.parser_name)
		self._Settings.parse_custom_settings(self._export_custom_settings_model())

		self._Properties = self._export_source_properties()
		self._Requestor = self._initialize_requestor()

		try:
			self._authorize()
		except TokenExpiredError as ExceptionData:
			self._Printer.error(f"Token expired: {ExceptionData}.")

		self._ImagesDownloader = ImagesDownloader(self)
		self._Portals = self._SystemObjects.printer.get_parser_portals(self._Manifest.parser_name)
		self._SharedData = self._SystemObjects.temper.load_parser_shared_data(self._Manifest.parser_name)
		
		self._parser_operator = self._SystemObjects.manager.parsers.get_operator(self.parser_name)

		self._post_init()

	def collect_slugs(self, period: int | None = None, filters: str | None = None, pages: int | None = None) -> tuple[str, ...]:
		"""
		Собирает список алиасов тайтлов по заданным параметрам.

		:param period: Количество часов до текущего момента, составляющее период получения данных.
		:type period: int | None
		:param filters: Строка, описывающая параметры фильтрации.
		:type filters: str | None
		:param pages: Количество запрашиваемых страниц каталога.
		:type pages: int | None
		:return: Набор собранных алиасов.
		:rtype: tuple[str, ...]
		"""

		return tuple(self._collect_slugs(period, filters, pages))
	
	def download_image(self, url: str, directory: str | PathLike[str] | None = None, filename: str | None = None, is_full_filename: bool = False, force_mode: bool = False) -> ImageDownloadingResult:
		"""
		Скачивает изображение.

		:param url: Ссылка на изображение.
		:type url: str
		:param directory: Путь к каталогу, в который нужно сохранить файл. По умолчанию будет использован временный каталог парсера.
		:type directory: str | PathLike[str] | None
		:param filename: Имя файла. По умолчанию будет сгенерировано на основе URL.
		:type filename: str | None
		:param is_full_filename: Указывает, является ли имя файла полным. Если имя неполное, то расширение для файла будет сгенерировано автоматически (например, для имени *image* будет создан файл *image.jpg* на основе ссылки), в ином случае имя файла задаётся жёстко. 
		:type is_full_filename: bool
		:param force_mode: Переключает режим перезаписи существующих изображений.
		:type force_mode: bool
		:return: Результат скачивания изображения.
		:rtype: ImageDownloadingResult
		"""

		url = types.URL.parse(url)
		ImageTargetPath = self._ImagesDownloader.build_target_path(url, directory, filename, is_full_filename)
		IsTargetPathExists: bool = ImageTargetPath.exists()

		#---> Пропуск скачивания уже существующего изображения.
		#==========================================================================================#
		if IsTargetPathExists and not force_mode:
			return ImageDownloadingResult(
				url = url,
				is_already_exists = True,
				is_downloaded = False,
				resolution = None,
				path = ImageTargetPath,
				error_message = None,
			)

		#---> Скачивание изображения во временный каталог парсера.
		#==========================================================================================#
		Result = self._temp_image(url, force_mode)
		if Result.error_message or Result.filtered_by or not Result.path:
			return Result

		#---> Перемещение изображения в целевой каталог.
		#==========================================================================================#
		if directory:
			self._ImagesDownloader.move_from_temp(directory, Result.path.name, filename, is_full_filename, force_mode)
		else:
			Result.path.replace(ImageTargetPath)
		
		return ImageDownloadingResult(
			url = url,
			is_already_exists = IsTargetPathExists,
			is_downloaded = True,
			filtered_by = Result.filtered_by,
			resolution = Result.resolution,
			path = ImageTargetPath,
			error_message = None,
		)

	def get_content_type_by_file(self, filename: str) -> TitleDescriptor:
		"""
		Определяет тип контента по файлу.

		:param filename: Имя файла с расширением или без него.
		:type filename: str
		:return: Дескриптор тайтла.
		:rtype: TitleDescriptor
		"""

		if not filename.endswith(".json"):
			filename += ".json"

		file = self.settings.directories.titles / filename
		title_data = json.read(file)
		title_format: str = title_data["format"]
		type_name: str = title_format.split("-")[1]
		
		descriptor = TitleDescriptor(self)
		descriptor.set_slug(title_data["slug"])
		descriptor.set_content_type(ContentTypes(type_name))

		return descriptor

	def get_content_type_by_slug(self, slug: str) -> ContentTypes:  # noqa: ARG002
		"""
		Определяет тип контента по алиасу тайтла.

		:param slug: Алиас тайтла.
		:type slug: str
		:return: Тип контента.
		:rtype: ContentTypes
		"""
		
		# To-Do: метод для определения типа контента по алиасу.
		return self._Manifest.content_types[0]

	def is_title_exists(self, slug: str) -> bool | None:
		"""
		Проверяет, существует ли тайтл на сервере.

		:param slug: Алиас тайтла.
		:type slug: str
		:return: Возвращает статус существования файла на сервере или `None` при невозможности проверки.
		:rtype: bool | None
		"""

		return self._is_title_exists(slug)

	def launch_parser(self, content_type: ContentTypes | None = None) -> "BaseParser":
		"""
		Инициализирует парсер для контента определённого типа.

		:param content_type: Тип контента. По умолчанию берётся первый описанный.
		:type content_type: ContentTypes | None
		:raises UnsupportedContent: Неподдерживаемый тип контента.
		:return: Парсер.
		:rtype: BaseParser
		"""

		if not content_type:
			content_type = self._Manifest.content_types[0]
		elif content_type not in self._Manifest.content_types:
			raise exceptions.parsers.UnsupportedContent(content_type)

		Module = importlib.import_module(f"parsers.{self._Manifest.parser_name}.{content_type.value}")
		Parser: BaseParser = Module.Parser(self)

		return Parser

	def parse_slug_from_string(self, string: str) -> str | None:
		"""
		Парсит алиас тайтла из переданной строки. Может использоваться для обработки тайтлов по ссылкам.

		:param string: Строка, из которой требуется получить алиас.
		:type string: str
		:return: Алиас или `None` в случае неудачи или отсутствия имплементации.
		:rtype: str | None
		"""

		return self._extract_slug_from_string(string)

	@overload
	def run_extension[T: "BaseExtension"](self, extension: type[T]) -> T: ...
	@overload
	def run_extension(self, extension: str) -> "BaseExtension": ...

	def run_extension[T: "BaseExtension"](self, extension: type[T] | str) -> "T | BaseExtension":
		"""
		Run extension by it class or name. If ran by name return untyped base extension for external using.

		:return: Extension.
		:rtype: BaseExtension
		"""

		if isinstance(extension, str):
			return self.extensions.run_by_name(self, extension)
		else:
			return self.extensions.run(self, extension)

	def set_mirror(self, mirror: str | None) -> bool:
		"""
		Задаёт домен зеркала, подменяя его в манифесте. Не сохраняет изменения в файл.
		
		:param mirror: Домен зеркала.
		:type mirror: str | None
		:raises ValidationError: Некорректный домен зеркала.
		:return: Возвращает `True`, если зеркало было изменено.
		:rtype: bool
		"""

		if mirror:
			mirror = types.Domain.parse(mirror)

		if mirror == self.manifest.original_domain or mirror == self.manifest.mirror:
			return False

		self.manifest.set_mirror(mirror)
		self.requestor.config.headers.set("referer", f"https://{self._Manifest.domain}/")
		self._post_mirror_changing(mirror)

		return True