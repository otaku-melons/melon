import os
from pathlib import Path
from typing import TYPE_CHECKING

from .....core import exceptions
from .operator import ParserOperator

if TYPE_CHECKING:
	from .. import Manager

class Parsers:
	"""Parsers manager."""

	def __init__(self, manager: "Manager"):
		"""
		Parsers manager.

		Args:
			manager (Manager): System manager.
		"""

		self.__manager: Manager = manager

		self.__root: Path = Path("parsers")
		self.__root.mkdir(exist_ok = True)

	def get_operator(self, parser_name: str, require_installation: bool = True) -> ParserOperator:
		"""
		Get parser operator.

		Args:
			parser_name (str): Parser name.
			require_installation (bool): Condition: is installed parser required.

		Returns:
			ParserOperator: Parser operator.
		"""

		if require_installation:
			self.is_installed(parser_name)

		return ParserOperator(self, parser_name)

	def is_installed(self, parser_name: str, raise_error: bool = True) -> bool:
		"""
		Check is parser installed.

		Args:
			parser_name (str): Parser name.
			raise_error (bool): Raise error if parser not installed.

		Returns:
			bool: `True` if parser installed.

		Raises:
			exceptions.parsers.ParserNotFoundError: Parser not found.
			exceptions.parsers.ParserNotInstalledError: Parser not installed.
		"""

		is_installed: bool = parser_name in self.installed

		if not is_installed and raise_error:

			if parser_name in self.manager.repositories.available_parsers:
				raise exceptions.parsers.ParserNotInstalledError(parser_name)
			else:
				raise exceptions.parsers.ParserNotFoundError(parser_name)

		return is_installed

	@property
	def installed(self) -> list[str]:
		"""Installed parsers names."""

		return os.listdir("parsers")

	@property
	def manager(self) -> "Manager":
		"""System manager."""

		return self.__manager

	@property
	def root(self) -> Path:
		"""Path to parsers root directory."""

		return self.__root
