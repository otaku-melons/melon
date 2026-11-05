from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from dublib.validators import ValidableType

from ...base import BaseCommandProcessor
from ...base.templates import BaseParameters

if TYPE_CHECKING:
	from dublib.cli.terminalyzer import CommandEntity, CommandModel

	from ...base.structs import PreparedData

@dataclass(frozen = True)
class Parameters(BaseParameters):
	"""Required by command processor parameters."""

	url: str

class CommandProcessor(BaseCommandProcessor[Parameters]):
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

		position = model.create_position("REPOSITORY", "Repository URL.")
		position.set_argument(ValidableType.URL)

		return model

	@override
	def _export_description(self) -> str:
		"""
		Export command description.

		Returns:
			str: Description.
		"""

		return "Add parser repository."

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

		return Parameters(
			url = entity.get_position_value("REPOSITORY", expected_type = str, important = True),
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

		self.system_objects.manager.repositories.add(parameters.url)
