from typing import TYPE_CHECKING, override

from ....core.system_objects.printer.templates.manager import ParsersTableRow
from ...base import BaseCommandProcessor
from ...base.structs import ProcessorOptions
from ...base.templates import BaseParameters

if TYPE_CHECKING:
	from dublib.cli.terminalyzer import CommandEntity, CommandModel

	from ...base.structs import PreparedData

class CommandProcessor(BaseCommandProcessor[BaseParameters]):
	"""Обработчик команды."""

	#==========================================================================================#
	# >>>>> OVERRIDABLE METHODS <<<<< #
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

		return model

	@override
	def _export_description(self) -> str:
		"""
		Возвращает описание команды.

		:return: Описание команды.
		:rtype: str
		"""

		return "List installed parsers."

	@override
	def _export_options(self) -> ProcessorOptions:
		"""
		Возвращает настройки обработчика.

		:return: Настройки обработчика.
		:rtype: ProcessorOptions
		"""

		return ProcessorOptions(use_timer = False)

	@override
	def _parse_parameters(self, entity: "CommandEntity", prepared_data: "PreparedData") -> BaseParameters:
		"""
		Парсит данные обработанной команды в структуру **dataclass**.

		:param entity: Сущность команды.
		:type entity: CommandEntity
		:param prepared_data: Подготовленные шаблонные параметры команды.
		:type prepared_data: PreparedData
		:return: Структура **dataclass**.
		:rtype: BaseParameters
		"""

		return BaseParameters()

	@override
	def _process(self, parameters: BaseParameters) -> bool:
		"""
		Выполняет команду.

		:param parameters: Required by command processor parameters.
		:type parameters: BaseParameters
		:return: Возвращает `True`, если выполнение успешно и прерывание не требуется.
		:rtype: bool
		"""

		parsers_rows: list[ParsersTableRow] = []

		for parser_name in self.system_objects.manager.parsers.installed:
			parser_operator = self.system_objects.manager.parsers.get_operator(parser_name)
			source_operator = parser_operator.launch()

			buffer = ParsersTableRow(
				name = parser_name,
				version = source_operator.manifest.version,
				content_types = source_operator.manifest.content_types,
				domain = source_operator.manifest.domain,
				collect = source_operator.is_collector_implemented,
			)

			parsers_rows.append(buffer)

		self.printer.templates.manager.parsers_table(parsers_rows)

		return True
