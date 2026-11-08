from typing import TYPE_CHECKING, cast

from pydantic import BaseModel, TypeAdapter

if TYPE_CHECKING:
	from pathlib import Path

	from ....core.system_objects import SystemObjects
	from ....core.system_objects.printer import Portals
	from ...system_objects.manager.extension_operator import ExtensionOperator
	from ..source_operator import BaseSourceOperator, ParserManifest

class EmptySettingsModel(BaseModel):
	"""Extension empty settings model."""

	pass

class BaseExtension[SO: "BaseSourceOperator", EO: BaseModel = BaseModel]:
	"""Base extension."""

	def __init__(self, extension_operator: "ExtensionOperator", source_operator: SO):
		"""
		Base extension.

		Args:
			extension_operator (ExtensionOperator): Extension manager.
			source_operator (SO): Source operator.
		"""

		self._extension_operator: ExtensionOperator = extension_operator
		self._source_operator: SO = source_operator

		self._settings: EO = self._parse_settings()

		self._post_init()

	@property
	def manifest(self) -> "ParserManifest":
		"""Parser manifest."""

		return self._source_operator.manifest

	@property
	def name(self) -> str:
		"""Extension name."""

		return self._extension_operator.name

	@property
	def settings(self) -> EO:
		"""Extension settings."""

		return self._settings

	@property
	def portals(self) -> "Portals":
		"""Extension output portals."""

		return self._source_operator.portals

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

		return self._extension_operator.temp_directory

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

		return adapter.validate_python(self._extension_operator.raw_settings)

	# OVERRIDABLE
	def _post_init(self):
		"""Execute after instance initialization."""

		pass
