from typing import TYPE_CHECKING, override

from ...base import BaseCommandProcessor
from ...base.templates import T_MultipleParsersRequired

if TYPE_CHECKING:
	from dublib.cli.terminalyzer import CommandEntity, CommandModel

	from ....core.system_objects.manager.parser.operator import DependencyError
	from ...base.structs import PreparedData

class CommandProcessor(BaseCommandProcessor[T_MultipleParsersRequired]):
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

		self._add_parser_position(multiple = True)

		return model

	@override
	def _export_description(self) -> str:
		"""
		Export command description.

		Returns:
			str: Description.
		"""

		return "Show parsers dependencies."

	@override
	def _parse_parameters(self, entity: "CommandEntity", prepared_data: "PreparedData") -> T_MultipleParsersRequired:
		"""
		Parse command parameters.

		Args:
			entity (CommandEntity): Command entity.
			prepared_data (T_MultipleParsersRequired): Prepared from templates data.

		Returns:
			PARAMS: Command parameters.
		"""

		return T_MultipleParsersRequired(
			required_parsers =  prepared_data.required_parsers,
		)

	@override
	def _process(self, parameters: T_MultipleParsersRequired) -> bool | None:
		"""
		Process command.

		Args:
			parameters (T_MultipleParsersRequired): Required by command parameters.

		Returns:
			bool | None: `False` if processing failed.
		"""

		has_errors: bool = False

		for parser_operator in parameters.required_parsers:
			dependency_error: DependencyError | None = parser_operator.check_dependencies()

			if dependency_error:
				has_errors = True
				self.printer.templates.manager.dependency_error(dependency_error)

		if not has_errors:
			self.printer.emit("All dependencies satisfied.")
