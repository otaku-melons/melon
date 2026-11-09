from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import TypeAdapter

from dublib.functions.data import dictionary
from dublib.functions.filesystem import json

from ....base.parser.components.manifest import ParserManifest
from ....base.parser.components.settings import ParserSettings
from ....base.parser.components.settings.models import SettingsModel
from ....base.source_operator import BaseSourceOperator
from ..enums import ExportResult, ExportStrategy
from ..extensions.manager import ExtensionsManager
from ..functions import export_package_settings

if TYPE_CHECKING:
	from importlib.metadata import EntryPoint
	from types import ModuleType

	from ... import SystemObjects
	from .manager import ParsersManager

class ParserOperator:
	"""Parser operator."""

	def __init__(self, parsers_manager: "ParsersManager", entry_point: "EntryPoint"):
		"""
		Parser operator.

		Args:
			parsers_manager (ParsersManager): Parsers manager.
			entry_point (EntryPoint): Parser entry point.
		"""

		self.__parsers_manager: ParsersManager = parsers_manager
		self.__entry_point: EntryPoint = entry_point

		self.__extensions_manager: ExtensionsManager = ExtensionsManager(self)

		self.__manifest: ParserManifest = ParserManifest(self.system_objects, self.name)
		self.__settings: ParserSettings = ParserSettings(self.system_objects, self.name)

	def export_settings(self, strategy: ExportStrategy = ExportStrategy.Skip) -> ExportResult:
		"""
		Export parser settings into configs directory.

		Args:
			strategy (ExportStrategy): Settings export strategy.

		Returns:
			ExportResult: Export result.
		"""

		adapter: TypeAdapter[SettingsModel] = TypeAdapter(SettingsModel)
		base_settings: dict[str, Any] = adapter.dump_python(SettingsModel())

		if self.settings.preset_path.exists():
			buffer: dict[str, Any] = json.read(self.settings.preset_path)
			base_settings = dictionary.deep_merge(base_settings, buffer, uniqueness = True)

		return export_package_settings(self.system_objects, self.name, base_settings, strategy)

	def launch(self) -> "BaseSourceOperator":
		"""
		Launch source operator.

		Returns:
			BaseSourceOperator: Source operator.

		Raises:
			TypeError: Incorrect type of source operator.
		"""

		parser_module: ModuleType = self.__entry_point.load()
		source_operator_type: type[BaseSourceOperator] = parser_module.SourceOperator

		if not issubclass(source_operator_type, BaseSourceOperator):
			raise TypeError(f"Incorrect type of source operator: {source_operator_type}.")

		return source_operator_type(self)

	@property
	def entry_point(self) -> "EntryPoint":
		"""Parser entry point."""

		return self.__entry_point

	@property
	def extensions(self) -> "ExtensionsManager":
		"""Extensions manager."""

		return self.__extensions_manager

	@property
	def manifest(self) -> ParserManifest:
		"""Parser manifest."""

		return self.__manifest

	@property
	def name(self) -> str:
		"""Parser name."""

		return self.__entry_point.name

	@property
	def settings(self) -> ParserSettings:
		"""Parser settings."""

		return self.__settings

	@property
	def system_objects(self) -> "SystemObjects":
		"""System objects collection."""

		return self.__parsers_manager.system_objects

	@property
	def temp_directory(self) -> Path:
		"""Parser temp directory path."""

		return self.__parsers_manager.system_objects.temper.get_parser_temp_directory(self.name)

	@property
	def version(self) -> str | None:
		"""Parser version."""

		if not self.__entry_point.dist:
			return

		return self.__entry_point.dist.version
