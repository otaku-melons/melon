from importlib.metadata import EntryPoint, entry_points
from typing import TYPE_CHECKING, overload

from ... import exceptions
from .extension_operator import ExtensionOperator

if TYPE_CHECKING:
	from types import ModuleType

	from ...base.extensions import BaseExtension
	from ...base.source_operator import BaseSourceOperator
	from .. import SystemObjects
	from .parser_operator import ParserOperator

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

	def get_operator(self, extension_name: str) -> ExtensionOperator:
		"""
		Get extension operator.

		Args:
			extension_name (str): Extension name.

		Returns:
			ExtensionOperator: Extension operator.
		"""

		self.is_installed(extension_name)

		return ExtensionOperator(self, self.__entry_points[extension_name])

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

	@overload
	def launch[E: "BaseExtension"](self, source_operator: "BaseSourceOperator", extension: type[E]) -> E | None: ...
	@overload
	def launch(self, source_operator: "BaseSourceOperator", extension: str) -> "BaseExtension | None": ...

	def launch[E: "BaseExtension"](self, source_operator: "BaseSourceOperator", extension: str | type[E], raise_error: bool = True) -> "BaseExtension | E | None":
		"""
		Run extension by class or name (in this case untyped).

		Args:
			source_operator (BaseSourceOperator): Source operator.
			extension (str | type[E]): Extension class or name.
			raise_error (bool): Condition: raise error if extension not installed.

		Returns:
			BaseExtension | E | None: Extension or `None` if disabled.

		Raises:
			TypeError: Incorrect type of extension.
		"""

		extension_name: str | None = None
		extension_type: type[BaseExtension| E] | None = None

		if not isinstance(extension, str):
			extension_name = extension.__module__.split(".")[-1]
			extension_type = extension

		else:
			extension_name = extension
			extension_module: ModuleType = self.__entry_points[extension].load()
			extension_type: type[BaseExtension] = extension_module.Extension

		try:
			operator: ExtensionOperator = self.get_operator(extension_name)
		except exceptions.extensions.ExtensionNotFoundError:
			if raise_error:
				raise
			else:
				return

		return extension_type(operator, source_operator)

	@property
	def entry_points(self) -> tuple[EntryPoint, ...]:
		"""Extensions entry points."""

		return tuple(self.__entry_points.values())

	@property
	def system_objects(self) -> "SystemObjects":
		"""System objects collection."""

		return self.__parser_operator.system_objects
