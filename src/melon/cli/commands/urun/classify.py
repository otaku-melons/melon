from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, override

from dublib.validators import ValidableType

from ....utils.classificator import ClassificatorsProcessor, ProcessingResult
from ...base.templates import T_SingleParserRequired
from ..melon._base import CommandProcessorTemplate

if TYPE_CHECKING:
	from dublib.cli.terminalyzer import CommandEntity, CommandModel

	from ...base.structs import PreparedData

@dataclass(frozen = True)
class Parameters(T_SingleParserRequired):
	"""Required by command processor parameters."""

	target: str
	is_output_json: bool
	is_ignore_case: bool
	register: Path | None

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


		position = model.create_position("VALUE", "Input value to classification.", important = True)
		position.set_argument()

		self._add_parser_position("--use")
		self._add_json_output_flag()

		model.base.add_flag("-i", aliases = ("--ignorecase",), description = "Ignore characters case in procedures searching.")
		model.base.add_key("--register", value_type = ValidableType.ExistingFilePath, description = "Classificators register file.")

		return model

	@override
	def _export_description(self) -> str:
		"""
		Export command description.

		Returns:
			str: Description.
		"""

		return "Process titles classificators."

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
			target = entity.get_position_value("VALUE", expected_type = str, important = True),
			is_output_json = entity.check_flag("-j"),
			is_ignore_case = entity.check_flag("-i"),
			register = entity.get_key_value("--register", expected_type = Path),
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

		entry_point: Path = self.system_objects.options.CONFIGS_DIR / parameters.required_parser.name / "classificator" / "main.mcs"

		try:
			classificator = ClassificatorsProcessor(entry_point)
		except FileNotFoundError as exception_data:
			self.printer.critical(f"Script entry point \"{exception_data}\" doesn't exists.")

		if validation_errors := classificator.load():
			for error_data in validation_errors:
				origin: str = f"{error_data.line.file.name}:{error_data.line.number}"
				self.printer.error(f"{error_data.message}", origin = origin)

			self.printer.critical("Script failure due to validation errors.")

		if parameters.register:
			classificator.load_register(parameters.register)

		classification_result = classificator.classify(parameters.target, ignore_case = parameters.is_ignore_case)

		if parameters.is_output_json:
			self.printer.json(classification_result.to_dict())
		else:
			self.__print_result(classification_result)

	def __print_result(self, result: "ProcessingResult"):
		"""
		Print result.

		Args:
			result (ProcessingResult): Classificator processing result.
		"""

		if not result.is_operation_found:
			self.printer.error("Operation not found.")
			return

		if result.is_found_in_register is not None:
			self.printer.debug("Register checked.")

		if result.is_found_in_register is False:
			self.printer.error("Classificator not found in gerister.")
			return

		if result.delete:
			self.printer.emit("Classificator must be deleted.")
			return

		self.printer.emit(f"Name: [i]{result.name}[/i]")
		is_renamed: str = str(result.is_renamed).lower()
		self.printer.emit(f"Renamed: {is_renamed}")
		classificator_type :str = result.type.name.lower() if result.type else "[red]null[/red]"
		self.printer.emit(f"Type: {classificator_type}")
