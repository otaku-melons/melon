import os
from pathlib import Path
from typing import TYPE_CHECKING

from .....core import exceptions
from .operator import ParserOperator

if TYPE_CHECKING:
	from .. import Manager

class Parsers:
	"""Менеджер парсеров."""

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def installed(self) -> list[str]:
		"""Список названий установленных парсеров."""

		return os.listdir("parsers")

	@property
	def manager(self) -> "Manager":
		"""Системный менеджер."""

		return self.__Manager

	@property
	def root(self) -> Path:
		"""Путь к корневому модулю всех парсеров."""

		return self.__Root

	#==========================================================================================#
	# >>>>> PUBLIC METHODS <<<<< #
	#==========================================================================================#

	def __init__(self, manager: "Manager"):
		"""
		Менеджер парсеров.

		:param manager: Системный менеджер.
		:type manager: Manager
		"""

		self.__Manager = manager

		self.__Root: Path = Path("parsers")
		self.__Root.mkdir(exist_ok = True)

	def get_operator(self, parser_name: str, require_installation: bool = True) -> ParserOperator:
		"""
		Запускает оператор парсера.

		:param parser_name: Имя парсера.
		:type parser_name: str
		:param require_installation: Указывает, проводить ли проверку установки парсера.
		:type require_installation: bool
		:return: Оператор парсера.
		:rtype: ParserOperator
		"""

		if require_installation:
			self.is_installed(parser_name, exception = True)

		return ParserOperator(self, parser_name)

	def is_installed(self, parser_name: str, exception: bool = True) -> bool:
		"""
		Проверяет, установлен ли парсер.

		:param parser_name: Имя парсера.
		:type parser_name: str
		:param exception: Указывает, следует ли выбрасывать исключение при отсутствии парсера.
		:type exception: bool
		:return: Возвращает `True`, если парсер установлен.
		:rtype: bool
		:raises ParserNotFound: Парсер не найден.
		"""

		IsInstalled: bool = parser_name in self.installed

		if not IsInstalled and exception:
			raise exceptions.parsers.ParserNotFound(parser_name)

		return IsInstalled
