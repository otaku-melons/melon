from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from ...base.structs import ProcessorOptions
from ...base.templates import T_SingleParserRequired
from ._base import CommandProcessorTemplate

if TYPE_CHECKING:
	from dublib.cli.terminalyzer import CommandEntity, CommandModel

	from ...base.structs import PreparedData

@dataclass(frozen = True)
class Parameters(T_SingleParserRequired):
	"""Required by command processor parameters."""

	extension_name: str
	command: str | None
	help: str | None
	list: bool

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

		position = model.create_position("EXTENSION", "Extension name", important = True)
		position.set_argument()

		position = model.create_position("OPERATION", "Extension with extension CLI.", important = True)
		position.add_key("--command", description = "Run command.")
		position.add_key("--help", description = "Print command info.")
		position.add_flag("-l", aliases = ("--list"), description = "Print list of available commands.")

		return model

	@override
	def _export_description(self) -> str:
		"""
		Export command description.

		Returns:
			str: Description.
		"""

		return "Run provided by extension CLI."

	@override
	def _export_options(self) -> ProcessorOptions:
		"""
		Export processor options.

		Returns:
			ProcessorOptions: Processor options.
		"""

		return ProcessorOptions(use_timer = False)

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
			extension_name = entity.get_position_value("EXTENSION", expected_type = str, important = True),
			command = entity.get_key_value("--command", expected_type = str, not_found_error = False),
			help = entity.get_key_value("--help", expected_type = str, not_found_error = False),
			list = entity.check_flag("-l"),
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

		if parameters.extension_name not in parameters.required_parser.extensions.names:
			self.printer.error(f"Extension \"{parameters.extension_name}\" not found for parser \"{parameters.required_parser.name}\".")
			return False

		# TODO: If extension disabled print info message instead force launch.
		extension = source_operator.run_extension(parameters.extension_name, force = True)

		if not extension.cli.is_provided:
			self.printer.error("Extension doesn't provide CLI.")
			return False

		if parameters.list:
			extension.cli.list()

		elif parameters.help:
			extension.cli.help(parameters.help)

		elif parameters.command:
			extension.cli.run(parameters.command)
