import inspect
from importlib import resources
from importlib.metadata import EntryPoint, entry_points
from pathlib import Path
from typing import TYPE_CHECKING, Any

from dublib.functions.data import dictionary
from dublib.functions.filesystem import json

from .... import exceptions
from ..enums import ExportResult, ExportStrategy
from ..functions import export_package_settings
from .enums import ParsingStep
from .registrator import Registrator

if TYPE_CHECKING:
	from collections.abc import Callable
	from types import ModuleType

	from ....base.extensions import BaseExtension
	from ....base.formats.base_format.controller import BaseTitleController
	from ....base.parser import BaseParser
	from ....base.source_operator import BaseSourceOperator
	from ... import SystemObjects
	from ..parsers.operator import ParserOperator

class ExtensionsManager:
	"""Extensions manager."""

	def __init__(self, parser_operator: "ParserOperator"):
		"""
		Extensions manager.

		Args:
			parser_operator (ParserOperator): Parser operator.
		"""

		self.__parser_operator: ParserOperator = parser_operator

		self.__entry_points: dict[str, EntryPoint] = {point.name: point for point in entry_points(group = f"melon.parsers.{self.__parser_operator.name}.extensions")}
		self.__registrators: dict[str, Registrator] = {}

	def export_settings(self, extension_name: str, strategy: ExportStrategy = ExportStrategy.Skip) -> ExportResult:
		"""
		Export extension settings into configs directory.

		Args:
			extension_name (str): Extension name.
			strategy (ExportStrategy): Settings export strategy.

		Returns:
			ExportResult: Export result.

		Raises:
			ExtensionNotFoundError: Extension not found.
		"""

		if extension_name not in self.__entry_points:
			raise exceptions.extensions.ExtensionNotFoundError(extension_name)

		preset_path: Path = Path(str(resources.files(extension_name) / "settings" / "settings.json"))
		base_settings: dict[str, Any] = {}

		if preset_path.exists():
			buffer: dict[str, Any] = json.read(preset_path)
			base_settings = dictionary.deep_merge(base_settings, buffer, uniqueness = True)

		return export_package_settings(self.system_objects, extension_name, base_settings, strategy)

	def get_extension_registrator(self, extension_name: str) -> Registrator:
		"""
		Get extension methods registrator.

		Args:
			extension_name (str): Extension name.

		Returns:
			Registrator: Extension methods registrator.
		"""

		if extension_name not in self.__registrators:
			self.__registrators[extension_name] = Registrator(extension_name)

		return self.__registrators[extension_name]

	def is_available(self, extension_name: str) -> bool:
		"""
		Check is extension installed and enabled.

		Args:
			extension_name (str): Extension name.

		Returns:
			bool: Extension available status.
		"""

		if not self.is_installed(extension_name, raise_error = False):
			return False

		return bool(self.is_enabled(extension_name))

	def is_enabled(self, extension_name: str) -> bool | None:  # noqa: ARG002
		"""
		Check is extension enabled.

		Args:
			extension_name (str): Extension name.

		Returns:
			bool | None: Extension state or `None` if extension not found.
		"""

		# TODO: Get from extension settings.
		return True

	def is_installed(self, extension_name: str, raise_error: bool = True) -> bool:
		"""
		Check is extension installed.

		Args:
			extension_name (str): Extension name.
			raise_error (bool): Condition: raise error if extension not installed.

		Returns:
			bool: `True` if parser installed.

		Raises:
			ExtensionNotFoundError: Extension not found.
		"""

		is_installed: bool = extension_name in self.__entry_points

		if not is_installed and raise_error:
			raise exceptions.extensions.ExtensionNotFoundError(extension_name)

		return is_installed

	def register_methods(self, source_operator: "BaseSourceOperator"):
		"""
		Register available extensions methods.

		Args:
			source_operator (BaseSourceOperator): Description.
		"""

		for name in self.__entry_points.keys():

			if not self.is_enabled(name):
				continue

			extension_module: ModuleType = self.__entry_points[name].load()
			extension_type: type[BaseExtension] = extension_module.Extension
			registrator: Registrator = self.get_extension_registrator(name)
			extension_type(registrator, source_operator).register()

	def run_step_methods(self, step: ParsingStep, parser: "BaseParser"):
		"""
		Run extensions methods, registeret for the parsing step.

		Args:
			step (ParsingStep): Parsing step.
			parser (BaseParser): Parser.
		"""

		for registrator in self.__registrators.values():
			for method in registrator.get_step_methods(step):
				self.__run_method(method, parser)

	@property
	def entry_points(self) -> tuple[EntryPoint, ...]:
		"""Extensions entry points."""

		return tuple(self.__entry_points.values())

	@property
	def system_objects(self) -> "SystemObjects":
		"""System objects collection."""

		return self.__parser_operator.system_objects

	def __run_method(self, method: "Callable", parser: "BaseParser"):
		"""
		Run method with arguments injection.

		Args:
			method (Callable): Extension method.
			parser (BaseParser): Parser.
		"""

		title: BaseTitleController | None = parser.get_title()

		injections: dict[str, Any] = {
			"parser": parser,
			"title": title,
			"data": title.data if title else None,
		}

		method_signatire = inspect.signature(method)
		kwargs: dict[str, Any] = {
			name: injections[name]
			for name in method_signatire.parameters
			if name in injections
		}

		method(**kwargs)
