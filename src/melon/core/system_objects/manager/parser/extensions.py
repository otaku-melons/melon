import importlib
import os
from typing import TYPE_CHECKING, Literal, overload

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
	def enabled(self) -> tuple[str, ...]:
		"""Enabled extensions names."""

		return tuple(name for name, state in self.__states.items() if state)

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
		:raises ExtensionNotFoundError: Extension not found.
		"""

		if extension_name not in self.__available_extensions:
			raise exceptions.extensions.ExtensionNotFoundError(extension_name)

	def __init__(self, parser_operator: "ParserOperator", manager: "Manager"):

		self.__parser_operator: ParserOperator = parser_operator
		self.__manager: Manager = manager

		self.__directory: Path = self.__parser_operator.path / "extensions"
		self.__available_extensions: tuple[str, ...] = tuple(sorted(
			entry.name
			for entry in os.scandir(self.__directory)
			if entry.is_dir() and not entry.name.startswith("__")),
		) if self.__directory.exists() else ()

		self.__activation_file: Path = self.temp_directory / "enabled.json"
		self.__states: dict[str, bool] = {}

		self.load_states()

	def disable(self, extension_name: str) -> bool:
		"""
		Disable extension.

		:param extension_name: Extension name.
		:type extension_name: str
		:return: Return `True` if state changed.
		:rtype: bool
		"""

		return self.set_state(extension_name, False)

	def enable(self, extension_name: str):
		"""
		Enable extension.

		:param extension_name: Extension name.
		:type extension_name: str
		:return: Return `True` if state changed.
		:rtype: bool
		"""

		return self.set_state(extension_name, True)

	def is_enabled[E: "BaseExtension"](self, extension: str | type[E]) -> bool:
		"""
		Check is extension enabled.

		Args:
			extension (str | type[BaseExtension]): Extension class or name.

		Returns:
			bool: State: is extension enabled.
		"""

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

		options_file: Path = self.__parser_operator.path / "extensions" / extension_name / "options.py"

		return options_file.exists()

	def load_states(self):
		"""Load extensions activation states from `enabled.json` file in extensions temporary directory."""

		self.__states: dict[str, bool] = dict.fromkeys(self.names, False)

		if not self.__activation_file.exists():
			return

		file_states: dict = json.read(self.__activation_file)

		for name in self.names:
			is_enabled = file_states.get(name, False)
			self.__states[name] = is_enabled

	@overload
	def run[E: "BaseExtension"](self, source_operator: "BaseSourceOperator", extension: type[E], force: Literal[False] = False) -> E | None: ...
	@overload
	def run[E: "BaseExtension"](self, source_operator: "BaseSourceOperator", extension: type[E], force: Literal[True]) -> E: ...
	@overload
	def run(self, source_operator: "BaseSourceOperator", extension: str, force: Literal[False] = False) -> "BaseExtension | None": ...
	@overload
	def run(self, source_operator: "BaseSourceOperator", extension: str, force: Literal[True]) -> "BaseExtension": ...

	def run[E: "BaseExtension"](self, source_operator: "BaseSourceOperator", extension: str | type[E], force: bool = False) -> "BaseExtension | E | None":
		"""
		Run extension by class or name (in this case untyped).

		Args:
			source_operator (BaseSourceOperator): Source operator.
			extension (str | type[E]): Extension class or name.
			force (bool): Ignore extension state.

		Returns:
			BaseExtension | E | None: Extension or `None` if disabled.
		"""

		if not self.is_enabled(extension) and not force:
			return

		if not isinstance(extension, str):
			return extension(source_operator)

		module_path = f"parsers.{self.__parser_operator.name}.extensions.{extension}"
		module = importlib.import_module(module_path)

		return module.Extension(source_operator)

	def save_states(self):
		"""Save extensions activation states in `enabled.json` file in extensions temporary directory."""

		json.write(self.__activation_file, self.__states)

	def set_state(self, extension_name: str, state: bool, not_found_error: bool = True) -> bool:
		"""
		Set extension activation state.

		:param extension_name: Extension name.
		:type extension_name: str
		:param state: Activation state.
		:type state: bool
		:param not_found_error: Raise exception if extension not found.
		:type not_found_error: bool
		:return: Return `True` if state changed.
		:rtype: bool
		"""

		if not_found_error:
			self.__check_extension(extension_name)

		if self.__states.get(extension_name) == state:
			return False

		self.__states[extension_name] = state

		return True
