from typing import TYPE_CHECKING, Any, cast

from pydantic import BaseModel, TypeAdapter

from dublib.functions.filesystem import json

if TYPE_CHECKING:
	from pathlib import Path

	from ....core.system_objects import SystemObjects
	from ....core.system_objects.printer.portals import Portals
	from ...system_objects.manager.extensions.registrator import Registrator
	from ..parser.components.manifest import ParserManifest
	from ..source_operator import BaseSourceOperator

class EmptySettingsModel(BaseModel):
	"""Extension empty settings model."""

	pass

class BaseExtension[SO: "BaseSourceOperator", EO: BaseModel = BaseModel]:
	"""Base extension."""

	def __init__(self, registrator: "Registrator", source_operator: SO):
		"""
		Base extension.

		Args:
			registrator (Registrator): Extension methods registrator.
			source_operator (SO): Source operator.
		"""

		self._registrator: Registrator = registrator
		self._source_operator: SO = source_operator

		self._system_objects: SystemObjects = self.source_operator.system_objects
		self._temp_directory: Path = self._system_objects.temper.get_extension_temp_directory(self.source_operator.parser_name, self.name)
		self._settings: EO = self._parse_settings()

		self._post_init()

	def register(self):
		"""Register extension methods execution."""

		self._register()

	@property
	def manifest(self) -> "ParserManifest":
		"""Parser manifest."""

		return self._source_operator.manifest

	@property
	def name(self) -> str:
		"""Extension name."""

		return self._registrator.extension_name

	@property
	def settings(self) -> EO:
		"""Extension settings."""

		return self._settings

	@property
	def portals(self) -> "Portals":
		"""Extension output portals."""

		return self._source_operator.portals

	@property
	def registrator(self) -> "Registrator":
		"""Extensions methods registrator."""

		return self._registrator

	@property
	def source_operator(self) -> SO:
		"""Source operator."""

		return self._source_operator

	@property
	def system_objects(self) -> "SystemObjects":
		"""System objects collection."""

		return self._source_operator.system_objects

	@property
	def temp_directory(self) -> "Path":
		"""Extension temp directory path."""

		return self._temp_directory

	# OVERRIDABLE
	def _export_settings_model(self) -> type[EO]:
		"""
		Export extension options [pydantic](https://github.com/pydantic/pydantic) model.

		:return: Extension options model.
		:rtype: type[BaseModel]
		"""

		# TODO: Resolve cast using.
		return cast("type[EO]", EmptySettingsModel)

	def _parse_settings(self) -> EO:
		"""
		Parse extension settings with **pydantic** model.

		Returns:
			EO: Extension settings.
		"""

		settings_model: type[EO] = self._export_settings_model()
		adapter: TypeAdapter[EO] = TypeAdapter(settings_model)

		return adapter.validate_python(self._read_raw_settings())

	# OVERRIDABLE
	def _post_init(self):
		"""Execute after instance initialization."""

		pass

	def _read_raw_settings(self) -> dict[str, Any]:
		"""
		Read extension raw settings.

		Returns:
			dict[str, Any]: Raw settings.
		"""

		settings_path = self.system_objects.options.CONFIGS_DIR / f"{self.name}.json"

		if not settings_path.exists():
			return {}

		return json.read(settings_path)

	# OVERRIDABLE
	def _register(self):
		"""
		Use `registrator` property to register extension methods execution.

		Methods can accepts arguments injections:
		- parser (`Parser`)
		- title (`Manga` | `Ranobe` | `None`)
		- data (`MangaData` | `RanobeData` | `None`)
		"""

		pass
