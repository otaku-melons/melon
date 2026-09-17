from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from ...base.structs import ProcessorOptions
from ...base.templates import T_SingleParserRequired
from ._base import CommandProcessorTemplate

if TYPE_CHECKING:
	from dublib.cli.terminalyzer import CommandEntity, CommandModel

	from ...base.structs import PreparedData

@dataclass(frozen = True)
class Parameters(T_SingleParserRequired):
	"""Параметры, требуемые обработчиком."""

	extension_name: str
	command: str | None
	help: str | None
	list: bool

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

		position = model.create_position("OPERATION", "Extension with extension CLI.", important = True)
		position.add_key("--command", description = "Run command.")
		position.add_key("--help", description = "Print command info.")
		position.add_flag("-l", aliases = ("--list"), description = "Print list of available commands.")

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
	def _export_options(self) -> ProcessorOptions:
		"""
		Возвращает настройки обработчика.

		:return: Настройки обработчика.
		:rtype: ProcessorOptions
		"""

		return ProcessorOptions(use_timer = False)

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
			command = entity.get_key_value("--command", expected_type = str, not_found_error = False),
			help = entity.get_key_value("--help", expected_type = str, not_found_error = False),
			list = entity.check_flag("-l")
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

		if parameters.extension_name not in parameters.required_parser.extensions_names:
			self.printer.error(f"Extension \"{parameters.extension_name}\" not found for parser \"{parameters.required_parser.name}\".")
			return False

		extension = source_operator.extensions.run_by_name(parameters.extension_name)

		if not extension.cli.is_provided:
			self.printer.error("Extension doesn't provide CLI.")
			return False

		if parameters.list:
			extension.cli.list()

		elif parameters.help:
			extension.cli.help(parameters.help)

		elif parameters.command:
			extension.cli.run(parameters.command)

		return True
