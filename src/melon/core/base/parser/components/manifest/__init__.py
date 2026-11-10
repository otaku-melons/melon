from importlib import resources
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import TypeAdapter

from dublib.functions.filesystem import json

from .models import ManifestModel

if TYPE_CHECKING:
	from ......core.system_objects import SystemObjects

class ParserManifest:
	"""Parser manifest."""

	def __init__(self, system_objects: "SystemObjects", parser_name: str):
		"""
		Parser manifest.

		:param system_objects: System objects collection.
		:type system_objects: SystemObjects
		:param parser_name: Parser name.
		:type parser_name: str
		"""

		self.__system_objects: SystemObjects = system_objects
		self.__parser_name: str = parser_name
		self.__manifest_path: Path = Path(str(resources.files(parser_name) / "manifest.json"))

		self.reload()

	def reload(self):
		"""Reload manifest."""

		self.__manifest: ManifestModel = self.__load()
		self.__mirror: str | None = None

	def set_mirror(self, mirror: str | None):
		"""
		Set mirror domain and replace original domain in manifest with it.

		Doesn't change manifest file!

		:param mirror: Mirror domain.
		:type mirror: str | None
		"""

		self.__mirror = mirror

	@property
	def domain(self) -> str:
		"""Source domain (can be replaced by mirror)."""

		return self.__mirror or self.original_domain

	@property
	def mirror(self) -> str | None:
		"""Mirror domain."""

		return self.__mirror

	@property
	def original_domain(self) -> str:
		"""Original source domain."""

		return self.__manifest.domain

	@property
	def parser_name(self) -> str:
		"""Parser name."""

		return self.__parser_name

	def __load(self) -> ManifestModel:
		"""
		Load manifest.

		:return: Filled manifest model.
		:rtype: ManifestModel
		"""

		data: dict = json.read(self.__manifest_path)

		return TypeAdapter(ManifestModel).validate_python(data)
