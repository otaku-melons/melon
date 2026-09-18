import importlib
import os
from typing import TYPE_CHECKING

from dublib.functions.filesystem import json

from .... import exceptions

if TYPE_CHECKING:
	from pathlib import Path

	from ....base.extensions import BaseExtension
	from ....base.source_operator import BaseSourceOperator
	from .. import Manager
	from .operator import ParserOperator

class ExtensionsOperator:
	"""Parser extensions operator."""

	@property
	def names(self) -> tuple[str, ...]:
		"""Последовательность имён расширений парсера."""

		return self.__available_extensions

	@property
	def temp_directory(self) -> "Path":
		"""Extensions temp directory path."""

		return self.__manager.system_objects.temper.get_parser_temp_directory(self.__parser_operator.name) / "extensions"

	def __check_extension(self, extension_name: str):
		"""
		Raise exception if extension not found.

		:param extension_name: Extension name.
		:type extension_name: str
		:raises ExtensionNotFound: Extension not found.
		"""

		if extension_name not in self.__available_extensions:
			raise exceptions.extensions.ExtensionNotFound(extension_name)

	def __init__(self, parser_operator: "ParserOperator", manager: "Manager"):

		self.__parser_operator: "ParserOperator" = parser_operator
		self.__manager: "Manager" = manager

		self.__directory: "Path" = self.__parser_operator.path / "extensions"
		self.__available_extensions: tuple[str, ...] = tuple(sorted(
			entry.name
			for entry in os.scandir(self.__directory)
			if entry.is_dir() and not entry.name.startswith("__"))
		) if self.__directory.exists() else ()

		self.__activation_file: "Path" = self.temp_directory / "enabled.json"
		self.__states: dict[str, bool] = {}

		self.load_states()

	def disable(self, extension_name: str):
		"""
		Disable extension.

		:param extension_name: Extension name.
		:type extension_name: str
		"""

		self.set_extension_state(extension_name, False)

	def enable(self, extension_name: str):
		"""
		Enable extension.

		:param extension_name: Extension name.
		:type extension_name: str
		"""

		self.set_extension_state(extension_name, True)

	def is_enabled[E: "BaseExtension | str"](self, extension: type[E]) -> bool:
		"""
		Check if extension enabled.

		:param extension: Extension class or name.
		:type extension: type[BaseExtension | str]
		:return: Return `True` if extension enabled.
		:rtype: bool
		:raises ExtensionNotFound: Extension not found.
		"""

		extension_name: str = ""

		if isinstance(extension, str):
			extension_name = extension
		else:
			extension_name = extension.__module__.split(".")[-1]

		self.__check_extension(extension_name)

		return self.__states[extension_name]

	def is_has_options(self, extension_name: str) -> bool:
		"""
		Check if extension provides options by checking `options.py` file existing.

		:param extension_name: Extension name.
		:type extension_name: str
		:return: Return `True` if extension provides options.
		:rtype: bool
		"""

		self.__check_extension(extension_name)

		options_file: "Path" = self.__parser_operator.path / "extensions" / extension_name / "options.py"

		return options_file.exists()

	def load_states(self):
		"""Load extensions activation states from `enabled.json` file in extensions temporary directory."""

		self.__activation_states: dict[str, bool] = dict.fromkeys(self.names, False)

		if not self.__activation_file.exists():
			return

		file_states: dict = json.read(self.__activation_file)
		
		for name in self.names:
			is_enabled = file_states.get(name, False)
			self.__activation_states[name] = is_enabled

	def run[E: "BaseExtension"](self, source_operator: "BaseSourceOperator", extension: type[E]) -> E:
		"""
		Run typed extension by it class.

		:param source_operator: Source operator.
		:type source_operator: type[BaseExtension]
		:param extension: Extension class.
		:type extension: type[BaseExtension]
		:return: Extension.
		:rtype: BaseExtension
		"""

		return extension(source_operator)

	def run_by_name(self, source_operator: "BaseSourceOperator", extension_name: str) -> "BaseExtension":
		"""
		Run untyped extension by it name.

		:param source_operator: Source operator.
		:type source_operator: type[BaseExtension]
		:param extension_name: Extension name.
		:type extension_name: str
		:return: Extension.
		:rtype: BaseExtension
		"""

		module_path = f"parsers.{self.__parser_operator.name}.extensions.{extension_name}"
		module = importlib.import_module(module_path)

		return module.Extension(source_operator)

	def save_states(self):
		"""Save extensions activation states in `enabled.json` file in extensions temporary directory."""

		json.write(self.__activation_file, self.__states)

	def set_extension_state(self, extension_name: str, state: bool):
		"""
		Set extension activation state.

		:param extension_name: Extension name.
		:type extension_name: str
		:param state: Activation state.
		:type state: bool
		"""

		self.__check_extension(extension_name)

		if self.__states[extension_name] == state:
			return

		self.__states[extension_name] = state
		self.save_states()