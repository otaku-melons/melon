from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from ....core.system_objects.manager.parser.enums import ExportStrategy
from ...base.templates import T_SingleParserRequired
from ._base import CommandProcessorTemplate

if TYPE_CHECKING:
	from dublib.cli.terminalyzer import CommandEntity, CommandModel

	from ...base.structs import PreparedData

@dataclass(frozen = True)
class Parameters(T_SingleParserRequired):
	"""Required by command processor parameters."""

	config_strategy: ExportStrategy

class CommandProcessor(CommandProcessorTemplate[Parameters]):
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
		self._add_settings_export_strategy_position()

		return model

	@override
	def _export_description(self) -> str:
		"""
		Export command description.

		Returns:
			str: Description.
		"""

		return "Export and merge parser config."

	@override
	def _parse_parameters(self, entity: "CommandEntity", prepared_data: "PreparedData") -> Parameters:
		"""
		Parse command parameters.

		Args:
			entity (CommandEntity): Command entity.
			prepared_data (PreparedData): Prepared from templates data.

		Returns:
			PARAMS: Command parameters.
		"""

		strategy: str | None = entity.get_position_value("STRATEGY", expected_type = str)
		if not strategy: strategy = "-s"

		return Parameters(
			required_parser = prepared_data.required_parsers[0],
			config_strategy = ExportStrategy(strategy),
		)

	@override
	def _process(self, parameters: Parameters) -> bool | None:
		"""
		Process command.

		Args:
			parameters (Parameters): Required by command parameters.

		Returns:
			bool | None: `False` if processing failed.
		"""

		result = parameters.required_parser.export_settings(parameters.config_strategy)
		self.printer.templates.manager.exported(result)
