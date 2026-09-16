from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from ...base.templates import T_SingleParserRequired
from ._base import CommandProcessorTemplate

if TYPE_CHECKING:
	from dublib.cli.terminalyzer import CommandEntity, CommandModel

	from ...base.structs import PreparedData

@dataclass(frozen = True)
class Parameters(T_SingleParserRequired):
	"""Параметры, требуемые обработчиком."""

	extension_name: str
	command: str

class CommandProcessor(CommandProcessorTemplate[Parameters]):
	"""Обработчик команды."""

	#==========================================================================================#
	# >>>>> ПЕРЕОПРЕДЕЛЯЕМЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	@override
	def _build_model(self, model: "CommandModel") -> "CommandModel":
		"""
		Генерирует модель команды.
		
		:param model: Шаблон модели команды.
		:type model: Command
		:return: Модель команды.
		:rtype: CommandModel
		"""

		self._add_parser_position()

		position = model.create_position("EXTENSION", "Extension name", important = True)
		position.set_argument()

		position = model.create_position("COMMAND", "Extension command", important = True)
		position.set_argument()

		return model

	@override
	def _export_description(self) -> str:
		"""
		Возвращает описание команды.
		
		:return: Описание команды.
		:rtype: str
		"""

		return "Run provided by extension CLI."

	@override
	def _parse_parameters(self, entity: "CommandEntity", prepared_data: "PreparedData") -> Parameters:
		"""
		Парсит данные обработанной команды в структуру **dataclass**.

		:param entity: Сущность команды.
		:type entity: CommandEntity
		:param prepared_data: Подготовленные шаблонные параметры команды.
		:type prepared_data: PreparedData
		:return: Структура **dataclass**.
		:rtype: Parameters
		"""

		return Parameters(
			required_parser = prepared_data.required_parsers[0],
			extension_name = entity.get_position_value("EXTENSION", expected_type = str, important = True),
			command = entity.get_position_value("COMMAND", expected_type = str, important = True),
		)

	@override
	def _process(self, parameters: Parameters) -> bool:
		"""
		Выполняет команду.

		:param parameters: Параметры, требуемые обработчиком.
		:type parameters: Parameters
		:return: Возвращает `True`, если выполнение успешно и прерывание не требуется.
		:rtype: bool
		"""

		source_operator = self._launch_source_operator(parameters.required_parser)
		extension = source_operator.extensions.run_by_name(parameters.extension_name)

		if not extension.cli.is_provided:
			self.printer.error("Extension doesn't provide CLI.")
			return False

		extension.cli.run(parameters.command)

		return True
