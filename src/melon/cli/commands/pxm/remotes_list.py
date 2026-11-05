from typing import TYPE_CHECKING, override

from rich.table import Table

from ...base import BaseCommandProcessor
from ...base.structs import ProcessorOptions
from ...base.templates import BaseParameters

if TYPE_CHECKING:
	from dublib.cli.terminalyzer import CommandEntity, CommandModel

	from ...base.structs import PreparedData

class CommandProcessor(BaseCommandProcessor[BaseParameters]):
	"""Command processor."""

	#==========================================================================================#
	# >>>>> OVERRIDABLE METHODS <<<<< #
	#==========================================================================================#

	@override
	def _build_model(self, model: "CommandModel") -> "CommandModel":
		"""
		Build commands model.

		Args:
			model (CommandModel): Commands model.

		Returns:
			CommandModel: Commands model.
		"""

		return model

	@override
	def _export_description(self) -> str:
		"""
		Export command description.

		Returns:
			str: Description.
		"""

		return "Show list of repositories."

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
	def _process(self, parameters: BaseParameters) -> bool | None:
		"""
		Process command.

		Args:
			parameters (BaseParameters): Required by command parameters.

		Returns:
			bool | None: `False` if processing failed.
		"""

		installed_parsers: list[str] = self.system_objects.manager.parsers.installed
		table = Table(box = None, header_style = "bold", pad_edge = False)

		table.add_column("Parser")
		table.add_column("Installed", justify = "center")
		table.add_column("Repository", style = "i")

		for parser_name in self.system_objects.manager.repositories.available_parsers:
			repository_url: str = self.system_objects.manager.repositories.get(parser_name, exception = True)
			status: str = "✅" if parser_name in installed_parsers else "❌"
			table.add_row(parser_name, status, repository_url)

		self.printer.table(table)
