from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from ....utils.collector import Collector
from ...base.templates import T_SingleParserRequired
from ..melon._base import CommandProcessorTemplate

if TYPE_CHECKING:
	from dublib.cli.terminalyzer import CommandEntity, CommandModel

	from ...base.structs import PreparedData

@dataclass(frozen = True)
class Parameters(T_SingleParserRequired):
	"""Required by command processor parameters."""

	slug: str
	collection: str | None

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

		position = model.create_position("SLUG", "Title slug.", important = True)
		position.set_argument()

		self._add_parser_position(key = "--use")

		model.base.add_key("--collection", description = "Collection name. By default [i]collection[/].")

		return model

	@override
	def _export_description(self) -> str:
		"""
		Export command description.

		Returns:
			str: Description.
		"""

		return "Merge slugs collections."

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
			required_parser = prepared_data.required_parsers[0],
			slug = entity.get_position_value("SLUG", expected_type = str, important = True),
			collection = entity.get_key_value("--collection", expected_type = str, not_found_error = False),
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

		source_operator = self._launch_source_operator(parameters.required_parser)

		collector = Collector(source_operator, parameters.collection)
		collector.load()

		if parameters.slug not in collector.slugs:
			collector.add(parameters.slug)
			self.printer.emit(f"Slug added in [b]{collector.name}[/] collection.")

		else:
			self.printer.emit("Slug already in collection.")
