from typing import TYPE_CHECKING, override

from .... import utils
from ...base.templates import T_MultipleParsersRequired
from ..melon._base import CommandProcessorTemplate

if TYPE_CHECKING:
	from dublib.cli.terminalyzer import CommandEntity, CommandModel

	from ...base.structs import PreparedData

class CommandProcessor(CommandProcessorTemplate[T_MultipleParsersRequired]):
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

		self._add_parser_position(key = "--use", multiple = True)

		return model

	@override
	def _export_description(self) -> str:
		"""
		Export command description.

		Returns:
			str: Description.
		"""

		return "Run ID-slug caching."

	@override
	def _parse_parameters(self, entity: "CommandEntity", prepared_data: "PreparedData") -> T_MultipleParsersRequired:
		"""
		Парсит данные обработанной команды в структуру **dataclass**.

		:param entity: Сущность команды.
		:type entity: CommandEntity
		:param prepared_data: Подготовленные шаблонные параметры команды.
		:type prepared_data: PreparedData
		:return: Структура **dataclass**.
		:rtype: T_MultipleParsersRequired
		"""

		return T_MultipleParsersRequired(prepared_data.required_parsers)

	@override
	def _process(self, parameters: T_MultipleParsersRequired) -> bool | None:
		"""
		Process command.

		Args:
			parameters (T_MultipleParsersRequired): Required by command parameters.

		Returns:
			bool | None: `False` if processing failed.
		"""

		for parser_operator in parameters.required_parsers:
			self.printer.emit(f"Caching titles for [b]{parser_operator.name}[/]…")
			Cacher = utils.Cacher(self._launch_source_operator(parser_operator))

			result = Cacher.cache_parser_output()
			self.printer.templates.cacher.result(result)
