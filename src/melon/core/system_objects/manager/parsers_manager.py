from importlib.metadata import EntryPoint, entry_points
from typing import TYPE_CHECKING

from ... import exceptions
from .parser_operator import ParserOperator

if TYPE_CHECKING:
	from .. import SystemObjects

class ParsersManager:
	"""Parsers manager."""

	def __init__(self, system_objects: "SystemObjects"):
		"""
		Parsers manager.

		Args:
			system_objects (SystemObjects): System objects collection.
		"""

		self.__system_objects: SystemObjects = system_objects

		self.__entry_points: dict[str, EntryPoint] = {point.name: point for point in entry_points(group = "melon.parsers")}

	def get_operator(self, parser_name: str) -> ParserOperator:
		"""
		Get parser operator.

		Args:
			parser_name (str): Parser name.

		Returns:
			ParserOperator: Parser operator.
		"""

		self.is_installed(parser_name)

		return ParserOperator(self, self.__entry_points[parser_name])

	def is_installed(self, parser_name: str, raise_error: bool = True) -> bool:
		"""
		Check is parser installed.

		Args:
			parser_name (str): Parser name.
			raise_error (bool): Condition: raise error if parser not installed.

		Returns:
			bool: `True` if parser installed.

		Raises:
			ParserNotFoundError: Parser not found.
		"""

		is_installed: bool = parser_name in self.__entry_points

		if not is_installed and raise_error:
			raise exceptions.parsers.ParserNotFoundError(parser_name)

		return is_installed

	@property
	def entry_points(self) -> tuple[EntryPoint, ...]:
		"""Parsers entry points."""

		return tuple(self.__entry_points.values())

	@property
	def installed_parsers_names(self) -> tuple[str, ...]:
		"""Installed parsers names."""

		return tuple(point.name for point in self.__entry_points.values())

	@property
	def system_objects(self) -> "SystemObjects":
		"""System objects collection."""

		return self.__system_objects
