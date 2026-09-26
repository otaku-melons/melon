import shutil
from typing import TYPE_CHECKING

from pydantic import TypeAdapter

from dublib.engine.patcher import Patch
from dublib.functions.filesystem import json

from ...core import exceptions
from ...core.base.parsers.components.manifest import StoragedManifestStruct
from ...core.base.parsers.components.manifest.enums import ContentTypes, Directives
from .structs import ExtensionData, ParserData

if TYPE_CHECKING:
	from pathlib import Path

	from ...core.system_objects import SystemObjects
	from ...core.system_objects.manager.packager import Packager

class Assistant:
	"""Development assistant."""

	@property
	def is_template_installed(self) -> bool:
		"""Is parser template directory exists."""

		return self.__template_path.exists()

	def __create_manifest(self, parser_data: ParserData):
		"""
		Create manifest.

		:param parser_data: Parser initialization data.
		:type parser_data: ParserData
		"""

		manifest = StoragedManifestStruct(
			domain = parser_data.domain,
			content_types = tuple(parser_data.content_types),
			parent = None,
			version = Directives.last_git_tag.value,
			melon_required_version = self.__system_objects.MELON_VERSION,
		)

		manifest_data: dict = TypeAdapter(StoragedManifestStruct).dump_python(manifest)
		manifest_data["content_types"] = tuple(element.value for element in manifest.content_types)

		json.write(self.__template_path / "manifest.json", manifest_data)

	def __clone_template(self):
		"""Clone parser template from Gir repository (provided by environment variable `MELON_TEMPLATE_REPOS`)."""

		if self.is_template_installed:
			shutil.rmtree(self.__template_path)

		self.__template_path.mkdir(exist_ok = True)

		self.__packager.clone(
			directory = self.__template_path,
			remote = self.__system_objects.options.TEMPLATE_REPOS.value,
		)

	def __is_parser_exists(self, parser_name: str):
		"""
		Check is parser installed or available in repositories.

		:param parser_name: Parser name.
		:type parser_name: str
		:raises exceptions.parsers.ParserAlreadyExists: Parser installed or found in repositories.
		"""

		if any((
			self.__system_objects.manager.parsers.is_installed(parser_name, exception = False),
			parser_name in self.__system_objects.manager.repositories.available_parsers,
		)):
			raise exceptions.parsers.ParserAlreadyExists(parser_name)

	def __replace_placeholders(self, file: "Path", data: ExtensionData | ParserData):
		"""
		Replace placeholders in file. Available placeholders:

		- `{PARSER_NAME}`
		- `{DOMAIN}`
		- `{EXTENSION_NAME}`

		:param file: Path to file.
		:type file: Path
		:param data: Parser or extension initialization data.
		:type data: ExtensionData | ParserData
		"""

		if isinstance(data, ParserData):
			placeholders: dict[str, str] = {
				"DOMAIN": data.domain,
				"PARSER_NAME": data.name,
			}
		else:
			manifest = self.__system_objects.manager.parsers.get_operator(data.parser_name).load_manifest()
			placeholders: dict[str, str] = {
				"DOMAIN": manifest.domain,
				"EXTENSION_NAME": data.name,
				"PARSER_NAME": data.parser_name,
			} 

		patch = Patch(file)

		for placeholder, value in placeholders.items():
			placeholder = "{" + placeholder + "}"
			patch.replace(placeholder, value)

		patch.save()

	def __init__(self, system_objects: "SystemObjects"):
		"""
		Development assistant.

		:param system_objects: System objects collection.
		:type system_objects: SystemObjects
		"""

		self.__system_objects: SystemObjects = system_objects

		self.__template_path: Path = system_objects.options.TEMP_DIR.value / ".template"
		self.__packager: Packager = system_objects.manager.packager

	def initialize_parser(self, parser_data: ParserData):
		"""
		Initialize new parser from development template.

		:param parser_data: Parser initialization data.
		:type parser_data: ParserData
		"""

		self.__is_parser_exists(parser_data.name)
		parser_operator = self.__system_objects.manager.parsers.get_operator(parser_data.name, require_installation = False)

		self.__clone_template()
		self.__replace_placeholders(self.__template_path / "README.md", parser_data)
		self.__create_manifest(parser_data)

		for content_type in ContentTypes:
			if content_type not in parser_data.content_types:
				submodule_name = self.__template_path / f"{content_type.value}.py"
				submodule_name.unlink()

		extensions_path = self.__template_path / "extensions"
		if extensions_path.exists():
			shutil.rmtree(extensions_path)

		shutil.move(self.__template_path, parser_operator.path)
