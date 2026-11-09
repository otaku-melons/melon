from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from dublib.functions.data import zerotify

from ....core.system_objects.manager.enums import ExportStrategy
from ...base.templates import BaseParameters
from ._base import CommandProcessorTemplate

if TYPE_CHECKING:
	from dublib.cli.terminalyzer import CommandEntity, CommandModel

	from ...base.structs import PreparedData

@dataclass(frozen = True)
class Parameters(BaseParameters):
	"""Required by command processor parameters."""

	package_name: str
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

		position = model.create_position("PACKAGE", "Parser or extension package name.", important = True)
		position.set_argument()

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
			Parameters: Command parameters.
		"""

		strategy: str | None = entity.get_position_value("STRATEGY", expected_type = str)
		if not strategy: strategy = "-s"

		return Parameters(
			package_name = entity.get_position_value("PACKAGE", expected_type = str, important = True),
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

		parser_name: str = parameters.package_name.split("_", maxsplit = 1)[0]
		extension_package_name: str | None = zerotify(parameters.package_name[len(parser_name) + 1:])
		parser_operator = self.system_objects.manager.get_operator(parser_name)

		if extension_package_name:
			result = parser_operator.extensions.export_settings(parameters.package_name, parameters.config_strategy)

		else:
			result = parser_operator.export_settings(parameters.config_strategy)

		self.printer.templates.manager.exported(result)
