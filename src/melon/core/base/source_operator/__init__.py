import importlib
from abc import ABC, abstractmethod
from collections.abc import Sequence
from os import PathLike
from pathlib import Path
from typing import TYPE_CHECKING, Self

from dublib.functions.filesystem import json
from dublib.validators import types
from dublib.web_requestor import WebConfig, WebLib, WebRequestor
from dublib.web_requestor.exceptions import TokenExpiredError

from ..parser.components.images_downloader import (
	ImageDownloadingResult,
	ImagesDownloader,
)
from ..parser.components.manifest import ParserManifest
from ..parser.components.settings import ParserSettings
from ..parser.enums import ContentType, ImagesLevel
from ..structs.title import TitleDescriptor
from .properties import SourceProperties

if TYPE_CHECKING:
	from types import ModuleType

	from pydantic import BaseModel

	from ...system_objects import SystemObjects
	from ...system_objects.manager.parser_operator import ParserOperator
	from ...system_objects.printer import Portals
	from ...system_objects.temper import SharedData
	from ..formats.base_format.controller import BaseTitleController
	from ..parser import BaseParser

__all__ = ["BaseSourceOperator", "SourceProperties"]

class BaseSourceOperator[CSM: "BaseModel"](ABC):
	"""Base source operator."""

	def __init__(self, parser_operator: "ParserOperator"):
		"""
		Base source operator.

		Args:
			parser_operator (ParserOperator): Parser operator.
		"""

		self._parser_operator: ParserOperator = parser_operator

		self._settings: ParserSettings[CSM] = ParserSettings(self.system_objects, self.parser_name)
		self._settings.parse_custom_settings(self._export_custom_settings_model())

		self._properties: SourceProperties = self._export_source_properties()
		self._requestor: WebRequestor = self._initialize_requestor()
		self._shared_data: SharedData = self.system_objects.temper.load_parser_shared_data(self.parser_name)
		self._portals: Portals = self.system_objects.printer.get_parser_portals(self.parser_name)

		try:
			self._authorize()
		except TokenExpiredError as exception:
			self.portals.printer.error(f"Token expired: {exception}.")

		self._images_downloader: ImagesDownloader = ImagesDownloader(self)

		self._parser_operator.extensions.register_methods(self)

		self._post_init()

	def collect_slugs(self, period: int | None = None, filters: str | None = None, pages: int | None = None) -> tuple[str, ...]:
		"""
		Collect slugs by parameters.

		Args:
			period (int | None): Period in hours.
			filters (str | None): Filters, specified by parser.
			pages (int | None, optional): Catalog pages count.

		Returns:
			tuple[str, ...]: Collected slugs.
		"""

		return tuple(self._collect_slugs(period, filters, pages))

	def download_image(self,
		url: str,
		directory: str | PathLike[str] | None = None,
		filename: str | None = None,
		is_full_filename: bool = False,
		force_mode: bool = False,
		) -> ImageDownloadingResult:
		"""
		Download image.

		Args:
			url (str): Image URL.
			directory (str | PathLike[str] | None): Directory for image saving. By default parser temporary directory.
			filename (str | None): Image filename.
			is_full_filename (bool): Condition: is given full filename. If disabled suffix will be received from URL.
			force_mode (bool): Condition: is image overwriting enabled.

		Returns:
			ImageDownloadingResult: Image downloading result.
		"""

		url = types.URL.parse(url)
		ImageTargetPath = self.images_downloader.build_target_path(url, directory, filename, is_full_filename)
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
			self.images_downloader.move_from_temp(directory, Result.path.name, filename, is_full_filename, force_mode)
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

	def extract_slug_from_string(self, string: str) -> str | None:
		"""
		Extract title slug from string.

		Args:
			string (str): String data.

		Returns:
			str | None: Title slug.
		"""

		return self._extract_slug_from_string(string)

	def get_content_type_by_file(self, filename: str) -> TitleDescriptor:
		"""
		Get content type by file.

		Args:
			filename (str): Title filename.

		Returns:
			TitleDescriptor: Title descriptor.
		"""

		if not filename.endswith(".json"):
			filename += ".json"

		file = self.settings.directories.titles / filename
		title_data = json.read(file)
		title_format: str = title_data["format"]
		type_name: str = title_format.split("-")[1]

		descriptor = TitleDescriptor(self)
		descriptor.set_slug(title_data["slug"])
		descriptor.set_content_type(ContentType(type_name))

		return descriptor

	def get_content_type_by_slug(self, slug: str) -> ContentType:
		"""
		Get content type by title slug.

		Args:
			slug (str): Title slug.

		Returns:
			ContentType: Content type.
		"""

		return self._get_content_type_by_slug(slug)

	def is_title_exists(self, slug: str) -> bool | None:
		"""
		Check is title exists.

		Args:
			slug (str): Title slug.

		Returns:
			bool | None: Title existing status or `None` if unable check.
		"""

		return self._is_title_exists(slug)

	def launch_parser(self, content_type: ContentType, force_mode: bool = False, images_level: ImagesLevel = ImagesLevel.NO) -> "BaseParser":
		"""
		Launch parser.

		Args:
			content_type (ContentType): Content type.
			force_mode (bool): Condition: is file overwriting enabled.
			images_level (ImagesLevel): Images downloading level.

		Returns:
			BaseParser: Parser.
		"""

		module: ModuleType = importlib.import_module(f"{self.parser_operator.entry_point.module}.{content_type.value}")
		parser_type: type[BaseParser[Self, BaseModel, BaseTitleController]] = module.Parser

		return parser_type(self, force_mode, images_level)

	def set_mirror(self, mirror: str | None) -> bool:
		"""
		Set mirror in manifest instead domain. Don't save manifest file!

		Args:
			mirror (str | None): Mirror domain. If `None` default domain will be restored.

		Returns:
			bool: `True` if domain changed.
		"""

		if mirror:
			mirror = types.Domain.parse(mirror)

		if mirror == self.manifest.original_domain or mirror == self.manifest.mirror:
			return False

		self.manifest.set_mirror(mirror)
		self.requestor.config.headers.set("referer", f"https://{self.manifest.domain}/")
		self._post_mirror_changing(mirror)

		return True

	@property
	def images_downloader(self) -> ImagesDownloader:
		"""Images downloading operator."""

		return self._images_downloader

	@property
	def is_collector_implemented(self) -> bool:
		"""Condition: is `_collect_slugs()` method overridden."""

		return type(self)._collect_slugs is not BaseSourceOperator._collect_slugs

	@property
	def manifest(self) -> ParserManifest:
		"""Parser manifest."""

		return self._parser_operator.manifest

	@property
	def parser_name(self) -> str:
		"""Parser name."""

		return self._parser_operator.name

	@property
	def parser_operator(self) -> "ParserOperator":
		"""Parser operator."""

		return self._parser_operator

	@property
	def portals(self) -> "Portals":
		"""Parser output portals."""

		return self._portals

	@property
	def properties(self) -> SourceProperties:
		"""Source properties."""

		return self._properties

	@property
	def requestor(self) -> WebRequestor:
		"""Requests manager."""

		return self._requestor

	@property
	def settings(self) -> ParserSettings[CSM]:
		"""Parser settings."""

		return self._settings

	@property
	def shared_data(self) -> "SharedData":
		"""Parser shared data."""

		return self._shared_data

	@property
	def system_objects(self) -> "SystemObjects":
		"""System objects collection."""

		return self._parser_operator.system_objects

	@property
	def temp_directory(self) -> Path:
		"""Path to parser temp directory."""

		return self._parser_operator.temp_directory

	def _authorize(self):
		"""
		It is executed after `_InitializeRequestor()` and wrapped to catch `TokenExpiredError` exceptions.

		Used to set up authorization based on the _Authorization_ header.
		"""

		pass

	def _collect_slugs(self, period: int | None = None, filters: str | None = None, pages: int | None = None) -> Sequence[str]:  # noqa: ARG002
		"""
		Collect slugs by parameters.

		Args:
			period (int | None): Period in hours.
			filters (str | None): Filters, specified by parser.
			pages (int | None, optional): Catalog pages count.

		Returns:
			Sequence[str]: Collected slugs.
		"""

		return ()

	@abstractmethod
	def _export_custom_settings_model(self) -> type[CSM]:
		"""
		Export custom parser settings [pydantic](https://github.com/pydantic/pydantic) model.

		Returns:
			type[BaseModel]: Custom parser settings model.
		"""

		pass

	# OVERRIDABLE
	def _export_source_properties(self) -> SourceProperties:
		"""
		Export source properties.

		Returns:
			SourceProperties: Source properties.
		"""

		return SourceProperties(
			one_cover = True,
		)

	# OVERRIDABLE
	def _extract_slug_from_string(self, string: str) -> str | None:
		"""
		Extract title slug from string.

		Args:
			string (str): String data.

		Returns:
			str | None: Title slug.
		"""

		return string

	@abstractmethod
	def _get_content_type_by_slug(self, slug: str) -> ContentType:
		"""
		Get content type by title slug.

		Args:
			slug (str): Title slug.

		Returns:
			ContentType: Content type.
		"""

		pass

	# OVERRIDABLE
	def _initialize_requestor(self) -> WebRequestor:
		"""
		Initialize requests operator.

		Returns:
			WebRequestor: Requests operator.
		"""

		Config = WebConfig()
		Config.select_lib(WebLib.requests)
		Config.set_retries_count(self.settings.network.retries)
		Config.set_delay(self.settings.network.delay)
		Config.enable_proxy_protocol_switching(True)

		Config.headers.generate_user_agent(("desktop",))
		Config.headers.automatically_accept_client_hints(True)
		Config.headers.add("referer", f"https://{self.manifest.domain}/")

		WebRequestorObject = WebRequestor(Config)
		WebRequestorObject.add_proxies(self.settings.network.proxies)

		return WebRequestorObject

	# OVERRIDABLE
	def _is_title_exists(self, slug: str) -> bool | None:  # noqa: ARG002
		"""
		Check is title exists.

		Args:
			slug (str): Title slug.

		Returns:
			bool | None: Title existing status or `None` if unable check.
		"""

		return None

	# OVERRIDABLE
	def _post_init(self):
		"""Execute after instance initialization."""

		pass

	# OVERRIDABLE
	def _post_mirror_changing(self, mirror: str | None):
		"""
		Execute after mirror changing.

		:param mirror: Mirror domain.
		:type mirror: str | None
		"""

		pass

	# OVERRIDABLE
	def _temp_image(self, url: str, force_mode: bool = False) -> ImageDownloadingResult:
		"""
		Download image into parser temporary directory.

		Args:
			url (str): Image URL.
			force_mode (bool): Condition: is image overwriting enabled.

		Returns:
			ImageDownloadingResult: Image downloading result.
		"""

		return self.images_downloader.temp_image(url, force_mode = force_mode)
