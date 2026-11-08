from typing import TYPE_CHECKING, Any

from dublib.functions.filesystem import json

from ...base.extensions import BaseExtension

if TYPE_CHECKING:
	from importlib.metadata import EntryPoint
	from pathlib import Path

	from ...base.source_operator import BaseSourceOperator
	from .extensions_manager import ExtensionsManager

class ExtensionOperator:
	"""Extension operator."""

	def __init__(self, extensions_manager: "ExtensionsManager", entry_point: "EntryPoint"):
		"""
		Extension operator.

		Args:
			extensions_manager (ExtensionsManager): Extensions manager.
			entry_point (EntryPoint): Extension entry point.
		"""

		self.__extensions_manager: ExtensionsManager = extensions_manager
		self.__entry_point: EntryPoint = entry_point

		self.__raw_settings: dict[str, Any] = self.__read_settings()

	def launch(self, source_operator: "BaseSourceOperator") -> BaseExtension | None:
		"""
		Launch extension.

		Args:
			source_operator (BaseSourceOperator): Source operator.

		Returns:
			BaseExtension | None: Extension or `None` if disabled.
		"""

		return self.__extensions_manager.launch(source_operator, self.__entry_point.name)

	@property
	def name(self) -> str:
		"""Extension name."""

		return self.__entry_point.name

	@property
	def raw_settings(self) -> dict[str, Any]:
		"""Raw extension settings."""

		return self.__raw_settings

	@property
	def temp_directory(self) -> "Path":
		"""Extension temp directory path."""

		return self.__extensions_manager.system_objects.temper.get_parser_temp_directory(self.name)

	def __read_settings(self) -> dict[str, Any]:
		"""
		Read extension raw settings.

		Returns:
			dict[str, Any]: Raw settings.
		"""

		settings_path = self.__extensions_manager.system_objects.options.CONFIGS_DIR / f"{self.name}.json"

		if not settings_path.exists():
			return {}

		return json.read(settings_path)
