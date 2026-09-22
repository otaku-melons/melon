from typing import TYPE_CHECKING, cast

from pydantic import BaseModel
from pydantic_core import ValidationError

from .cli import BaseExtensionCLI

if TYPE_CHECKING:
	from pathlib import Path

	from ....core.system_objects import SystemObjects
	from ....core.system_objects.printer import Portals
	from ..source_operator import BaseSourceOperator, ParserManifest

class ModelStub(BaseModel):
	"""Extension options model stub"""

	pass

class BaseExtension[SO: "BaseSourceOperator", EO: BaseModel = BaseModel]:
	"""Базовое расширение."""

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def cli(self) -> BaseExtensionCLI:
		"""Оператор CLI расширения."""

		return self._cli

	@property
	def manifest(self) -> "ParserManifest":
		"""Манифест парсера."""

		return self._source_operator.manifest

	@property
	def name(self) -> str:
		"""Имя расширения."""

		return self._name

	@property
	def options(self) -> EO:
		"""Настройки расширения."""

		return self._options

	@property
	def portals(self) -> "Portals":
		"""Порталы вывода парсера."""

		return self._source_operator.portals

	@property
	def source_operator(self) -> SO:
		"""Оператор источника."""

		return self._source_operator

	@property
	def system_objects(self) -> "SystemObjects":
		"""Коллекция системных объектов."""

		return self._source_operator.system_objects

	@property
	def temp_directory(self) -> "Path":
		"""Путь ко временной директории расширения."""

		return self._temp_directory

	#==========================================================================================#
	# >>>>> НАСЛЕДУЕМЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def _parse_options(self) -> EO:
		"""
		Парсит настройки расширения.

		В случае ошибоки валидации словаря настроек выводит подробности в терминал и завершает работу.

		:return: Настройки расширения.
		:rtype: EO
		"""

		try:
			return self.source_operator.settings.extensions.get(self._name, self._export_options_model())

		except ValidationError as exception:

			for error in exception.errors():
				error_type: str = error["type"].lower()
				field: str = "/".join(str(key) for key in error["loc"])
				self.portals.printer.error(f"Field <b>{field}</b> error: <i>{error_type}</i>.", origin = self._name)

			self.portals.printer.critical("Unable parse extension options.", end_work = True)

	#==========================================================================================#
	# >>>>> ПЕРЕОПРЕДЕЛЯЕМЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def _export_options_model(self) -> type[EO]:
		"""
		Export extension options [pydantic](https://github.com/pydantic/pydantic) model. 

		:return: Extension options model.
		:rtype: type[BaseModel]
		"""

		return cast("type[EO]", ModelStub)

	def _post_init(self):
		"""Метод, выполняющийся после инициализации объекта."""

		pass

	def _provide_cli(self) -> type[BaseExtensionCLI]:
		"""
		Возвращает класс-обработчик CLI.

		:return: Класс-обработчик CLI.
		:rtype: type[BaseExtensionCLI]
		"""

		return BaseExtensionCLI

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self, source_operator: SO):
		"""
		Базовое расширение.

		:param source_operator: Оператор источника.
		:type source_operator: BaseSourceOperator
		:param name: Имя расширения.
		:type name: str
		:raises FileNotFoundError: Каталог расширения не найден.
		"""

		self._source_operator: SO = source_operator
		self._name: str = self.__module__.split(".")[-1]
		
		self._cli: BaseExtensionCLI = self._provide_cli()(self)
		self._options: EO = self._parse_options()
		self._temp_directory: "Path" = self._source_operator.system_objects.temper.get_extension_temp_directory(self._source_operator.parser_name, self._name)

		self._post_init()