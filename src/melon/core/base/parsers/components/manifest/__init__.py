from pathlib import Path
from typing import TYPE_CHECKING

from dulwich import errors, porcelain
from packaging.version import Version
from pydantic import TypeAdapter

from dublib.functions.filesystem import json

from .enums import ContentType
from .models import ManifestModel

if TYPE_CHECKING:
	from dulwich.refs import Ref
	from packaging.specifiers import SpecifierSet

	from ......core.system_objects import SystemObjects

class ParserManifest:
	"""Parser manifest."""

	#==========================================================================================#
	# >>>>> PROPERTIES <<<<< #
	#==========================================================================================#

	@property
	def parser_name(self) -> str:
		"""Parser name."""

		return self.__parser_name

	@property
	def original_domain(self) -> str:
		"""Original source domain."""

		return self.__manifest.domain

	@property
	def mirror(self) -> str | None:
		"""Mirror domain."""

		return self.__mirror

	@property
	def domain(self) -> str:
		"""Source domain (can be replaced by mirror)."""

		return self.__mirror or self.original_domain

	@property
	def content_types(self) -> tuple[ContentType, ...]:
		"""Supported content types."""

		return self.__content_types

	@property
	def parent(self) -> str | None:
		"""Parent parser name."""

		return self.__manifest.parent

	@property
	def version(self) -> Version | None:
		"""Parser version."""

		return self.__version

	@property
	def platform(self) -> "SpecifierSet | None":
		"""Melon supported versions range."""

		return self.__manifest.platform

	#==========================================================================================#
	# >>>>> PRIVATE METHODS <<<<< #
	#==========================================================================================#

	def __get_supported_content_types(self) -> tuple[ContentType, ...]:
		"""
		Get supported content types from parser modules.

		:return: Supported content types.
		:rtype: tuple[ContentType, ...]
		"""

		supported_types: set[ContentType] = set()

		for content_type in ContentType:
			module_path: Path = Path(f"parsers/{self.__parser_name}/{content_type.value}.py")

			if module_path.exists():
				supported_types.add(content_type)

		return tuple(supported_types)

	def __get_version(self) -> Version | None:
		"""
		Get parser version from latest Git tag.

		:return: Parser version.
		:rtype: packaging.version.Version | None
		"""

		parser_tags: list[Ref] = []

		try:
			parser_tags = porcelain.tag_list(f"parsers/{self.__parser_name}")
		except errors.NotGitRepository: pass

		if parser_tags:
			last_tag: str = parser_tags[-1].decode()
			return Version(last_tag)

	def __load(self) -> ManifestModel:
		"""
		Load manifest.

		:return: Filled manifest model.
		:rtype: ManifestModel
		"""

		data: dict = json.read(f"parsers/{self.__parser_name}/manifest.json")

		return TypeAdapter(ManifestModel).validate_python(data)

	#==========================================================================================#
	# >>>>> PUBLIC METHODS <<<<< #
	#==========================================================================================#

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

		self.__manifest: ManifestModel = self.__load()
		self.__content_types: tuple[ContentType, ...] = self.__get_supported_content_types()
		self.__version: Version | None = self.__get_version()
		self.__mirror: str | None = None

	def set_mirror(self, mirror: str | None):
		"""
		Set mirror domain and replace original domain in manifest with it.

		Doesn't change manifest file!

		:param mirror: Mirror domain.
		:type mirror: str | None
		"""

		self.__mirror = mirror
