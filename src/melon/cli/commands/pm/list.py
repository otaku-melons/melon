from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from rich.table import Table

from ...base import BaseCommandProcessor
from ...base.structs import ProcessorOptions
from ...base.templates import BaseParameters

if TYPE_CHECKING:
	from dublib.cli.terminalyzer import CommandEntity, CommandModel

	from ...base.structs import PreparedData

@dataclass(frozen = True)
class Parameters(BaseParameters):
	"""Required by command processor parameters."""

	is_extensions: bool

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

		model.base.add_flag("-e", description = "Print extensions list.")

		return model

	@override
	def _export_description(self) -> str:
		"""
		Export command description.

		Returns:
			str: Description.
		"""

		return "List installed parsers."

	@override
	def _export_options(self) -> ProcessorOptions:
		"""
		Export processor options.

		Returns:
			ProcessorOptions: Processor options.
		"""

		return ProcessorOptions(use_timer = False, check_parsers_dependencies = False)

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

		return Parameters(
			is_extensions = entity.check_flag("-e"),
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

		if parameters.is_extensions:
			pass

		else:
			self.__print_parsers_table()

	def __print_parsers_table(self):
		"""Print parsers table."""

		table = Table(box = None, header_style = "bold")

		for column in ("Name", "Version", "Content", "Source", "collect"):
			table.add_column(column)

		for entry_point in self.system_objects.manager.entry_points:
			parser_operator = self.system_objects.manager.get_operator(entry_point.name)
			source_operator = parser_operator.launch()

			version: str | None = entry_point.dist.version if entry_point.dist else None
			content: str = ", ".join(content_type.value[0] for content_type in parser_operator.manifest.content_types)
			source: str = f"https://{parser_operator.manifest.domain}"
			collect: str = "[green]true[/green]" if source_operator.is_collector_implemented else "[red]false[/red]"

			table.add_row(entry_point.name, version, content, source, collect)

		self.printer.table(table)

