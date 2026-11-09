from importlib import resources
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, TypeAdapter

from dublib.functions.data import dictionary
from dublib.functions.filesystem import json

from .models import SettingsModel
from .sections import Common, Directories, Filters, Network

if TYPE_CHECKING:
	from ......core.system_objects import SystemObjects

class ParserSettings[T: BaseModel]:
	"""Parser settings."""

	def __init__(self, system_objects: "SystemObjects", parser_name: str):
		"""
		Parser settings.

		Args:
			system_objects (SystemObjects): System objects collection.
			parser_name (str): Parser name.
		"""

		self.__system_objects: SystemObjects = system_objects
		self.__parser_name: str = parser_name

		self.__adapter: TypeAdapter[SettingsModel] = TypeAdapter(SettingsModel)
		self.__settings_preset_path: Path = Path(str(resources.files(self.__parser_name) / "settings" / "settings.json"))

		self.reload()

	def parse_custom_settings(self, model: type[T]):
		"""
		Parse custom settings with [pydantic](https://github.com/pydantic/pydantic) model and save in settings instance.
		Also replace model config with `ConfigDict(frozen=True)`.

		Args:
			model (type[BaseModel]): Pydantic model.
		"""

		model.model_config = ConfigDict(frozen = True)
		self.__custom = model.model_validate(self.__data.custom)

	def reload(self):
		"""Reload settings."""

		raw_settings: dict = self.__read_raw_data()

		self.__data: SettingsModel = self.__adapter.validate_python(raw_settings)

		self.__common: Common = Common(self.__data.common)
		self.__directories = Directories(self.__data.directories, self.__system_objects, self.__parser_name)
		self.__filters = Filters(self.__data.filters)
		self.__network: Network = Network(self.__data.network)

		self.__custom: T | None = None

	@property
	def common(self) -> Common:
		"""Settings section: common."""

		return self.__common

	@property
	def custom(self) -> T:
		"""Settings section: custom."""

		if self.__custom is None:
			# TODO: Use custom exception.
			raise ValueError("Custom settings required, but unparsed.")

		return self.__custom

	@property
	def directories(self) -> Directories:
		"""Settings section: directories.."""

		return self.__directories

	@property
	def filters(self) -> Filters:
		"""Settings section: filters."""

		return self.__filters

	@property
	def network(self) -> Network:
		"""Settings section: network."""

		return self.__network

	@property
	def preset_path(self) -> Path:
		"""Settings preset path."""

		return self.__settings_preset_path

	def __read_raw_data(self) -> dict:
		"""
		Read raw settings from configs directory and parser defaults and merge.

		Returns:
			dict: Raw settings.
		"""

		base_settings: dict = self.__adapter.dump_python(SettingsModel())

		settings_paths: tuple[Path, Path] = (
			self.preset_path,
			self.__system_objects.options.CONFIGS_DIR / f"{self.__parser_name}.json",
		)

		for settings_path in settings_paths:
			if settings_path.exists():
				buffer: dict = json.read(settings_path)
				base_settings = dictionary.deep_merge(base_settings, buffer, uniqueness = True)

		return base_settings
