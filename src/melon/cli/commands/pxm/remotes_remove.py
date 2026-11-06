from typing import TYPE_CHECKING, override

from ...base import BaseCommandProcessor
from ...base.structs import ProcessorOptions
from ...base.templates import T_SingleParserRequired

if TYPE_CHECKING:
	from dublib.cli.terminalyzer import CommandEntity, CommandModel

	from ...base.structs import PreparedData

class CommandProcessor(BaseCommandProcessor[T_SingleParserRequired]):
	"""Command processor."""

	@override
	def _build_model(self, model: "CommandModel") -> "CommandModel":
		"""
		Build commands model.

		Args:
			model (CommandModel): Commands model.

		Returns:
			CommandModel: Commands model.
		"""

		self._add_parser_position()

		return model

	@override
	def _export_description(self) -> str:
		"""
		Export command description.

		Returns:
			str: Description.
		"""

		return "Remove parser repository."

	@override
	def _export_options(self) -> ProcessorOptions:
		"""
		Export processor options.

		Returns:
			ProcessorOptions: Processor options.
		"""

		return ProcessorOptions(require_installed_parsers = False)

	@override
	def _parse_parameters(self, entity: "CommandEntity", prepared_data: "PreparedData") -> T_SingleParserRequired:
		"""
		Парсит данные обработанной команды в структуру **dataclass**.

		:param entity: Сущность команды.
		:type entity: CommandEntity
		:param prepared_data: Подготовленные шаблонные параметры команды.
		:type prepared_data: PreparedData
		:return: Структура **dataclass**.
		:rtype: T_SingleParserRequired
		"""

		return T_SingleParserRequired(
			required_parser =  prepared_data.required_parsers[0],
		)

	@override
	def _process(self, parameters: T_SingleParserRequired) -> bool | None:
		"""
		Process command.

		Args:
			parameters (T_SingleParserRequired): Required by command parameters.

		Returns:
			bool | None: `False` if processing failed.
		"""

		self.system_objects.manager.repositories.remove(parameters.required_parser.name)
