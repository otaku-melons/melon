from typing import TYPE_CHECKING

from dulwich import errors, porcelain
from pydantic import TypeAdapter

from dublib.functions.data import to_sequence
from dublib.functions.filesystem import json

from ......core import exceptions
from .enums import ContentTypes, Directives
from .structs import ManifestStruct, StoragedManifestStruct

if TYPE_CHECKING:
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
	def content_types(self) -> tuple[ContentTypes, ...]:
		"""Supported content types."""

		return tuple(self.__manifest.content_types)
	
	@property
	def parent(self) -> str | None:
		"""Parent parser name."""

		return self.__manifest.parent

	@property
	def version(self) -> str | None:
		"""Parser version."""

		return self.__manifest.version

	@property
	def melon_required_version(self) -> str | None:
		"""Melon required version."""

		return self.__manifest.melon_required_version

	#==========================================================================================#
	# >>>>> PRIVATE METHODS <<<<< #
	#==========================================================================================#

	def __parse_melon_required_version(self, buffer: ManifestStruct, parent_manifest: "ParserManifest | None") -> str | None:
		"""
		Parse Melon required version.

		:param buffer: Manifest struct.
		:type buffer: ManifestStruct
		:param parent_manifest: Parent parser manifest.
		:type parent_manifest: ParserManifest | None
		:return: Melon required version.
		:rtype: str | None
		:raises BadManifest: Parent not specified.
		"""

		if buffer.melon_required_version is Directives.from_parent:

			if not parent_manifest:
				raise exceptions.parsers.BadManifest("Parent must be specified if using \"$from_parent\".")

			return parent_manifest.melon_required_version

	def __parse_version(self, buffer: ManifestStruct, parent_manifest: "ParserManifest | None") -> str | None:
		"""
		Parse parser version.

		:param buffer: Manifest struct.
		:type buffer: ManifestStruct
		:param parent_manifest: Parent parser manifest.
		:type parent_manifest: ParserManifest | None
		:return: Parser version.
		:rtype: str | None
		:raises BadManifest: Parent not specified.
		"""

		if buffer.version is Directives.from_parent:
			if not parent_manifest:
				raise exceptions.parsers.BadManifest("Parent must be specified if using \"$from_parent\".")

			return parent_manifest.version

		elif buffer.version is Directives.last_git_tag:
			try:
				parser_tags = porcelain.tag_list(f"parsers/{self.parser_name}")
				if parser_tags:
					return parser_tags[-1].decode().lstrip("v")
			except errors.NotGitRepository: pass

		return None
				
	def __load(self) -> StoragedManifestStruct:
		"""
		Load manifest.

		:return: Storaged manifest struct.
		:rtype: StoragedManifestStruct
		:raises BadManifest: Manifest parsing error.
		"""

		data: dict = json.read(f"parsers/{self.__parser_name}/manifest.json")
		buffer: ManifestStruct = TypeAdapter(ManifestStruct).validate_python(data)
		parent_manifest: ParserManifest | None = None

		if buffer.parent:

			if buffer.parent not in self.__system_objects.manager.parsers.installed:
				raise exceptions.parsers.BadManifest(f"Parent \"{buffer.parent}\" not installed.")

			parent_manifest = self.__system_objects.manager.parsers.get_operator(buffer.parent).load_manifest()

		buffer.melon_required_version = self.__parse_melon_required_version(buffer, parent_manifest)
		buffer.version = self.__parse_version(buffer, parent_manifest)

		return StoragedManifestStruct(
			domain = buffer.domain,
			content_types = to_sequence(buffer.content_types),
			parent = buffer.parent,
			version = buffer.version,
			melon_required_version = buffer.melon_required_version,
		)

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

		self.__manifest: StoragedManifestStruct = self.__load()
		self.__mirror: str | None = None

	def set_mirror(self, mirror: str | None):
		"""
		Set mirror domain and replace original domain in manifest with it.
		
		Doesn't change manifest file!

		:param mirror: Mirror domain.
		:type mirror: str | None
		"""

		self.__mirror = mirror
