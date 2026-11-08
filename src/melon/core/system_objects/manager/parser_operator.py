from pathlib import Path
from typing import TYPE_CHECKING

from ...base.parser.components.manifest import ParserManifest
from ...base.parser.components.settings import ParserSettings
from ...base.source_operator import BaseSourceOperator
from .extensions_manager import ExtensionsManager

if TYPE_CHECKING:
	from importlib.metadata import EntryPoint
	from types import ModuleType

	from .. import SystemObjects
	from . import ParsersManager

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
