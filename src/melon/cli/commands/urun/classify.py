from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, override

from dublib.validators import ValidableType

from ....core import exceptions
from ....utils.classificator import AttributesClassificator, Operation
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

		model.base.add_flag("-i", description = "Ignore characters case in procedures searching.")
		model.base.add_key("--register", value_type = ValidableType.ExistingFilePath, description = "Attributes register file.")

		return model

	@override
	def _export_description(self) -> str:
		"""
		Export command description.

		Returns:
			str: Description.
		"""

		return "Classify titles attributes."

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

		classificator: AttributesClassificator = self.__initialize_classificator(parameters)
		self.__compare(classificator)
		operation: Operation | None = classificator.classify(parameters.target, ignore_case = parameters.is_ignore_case)

		if not operation:
			self.printer.error("Operation not found.")
			return

		if parameters.is_output_json:
			self.printer.json(operation.to_dict())
		else:
			self.__print_result(operation)

	def __compare(self, classificator: AttributesClassificator):
		"""
		Compare operations with register.

		Args:
			classificator (AttributesClassificator): Attributes classificator.
		"""

		if not classificator.register:
			return

		if operations := classificator.compare_with_register():
			for not_found_operation in operations:
				type_name: str = not_found_operation.type.name.title() if not_found_operation.type else "Attribute"

				if not_found_operation.is_deleted:
					self.printer.error(f"{type_name} deleted, but it's processing result found in register: \"{not_found_operation.value}\".")
					continue

				self.printer.error(f"{type_name} not found in register: \"{not_found_operation.result}\".")

			self.printer.critical("Script failure due to register comparing errors.")

	def __initialize_classificator(self, parameters: Parameters) -> AttributesClassificator:
		"""
		Initialize attributes classificator.

		Args:
			parameters (Parameters): Required by command parameters.

		Returns:
			AttributesClassificator: Attributes classificator.
		"""

		entry_point: Path = self.system_objects.options.CONFIGS_DIR / parameters.required_parser.name / "classificator" / "main.mcs"

		if not entry_point.exists():
			self.printer.critical(f"Script entry point not found: \"{entry_point}\".")

		classificator = AttributesClassificator(entry_point)
		self.__load_register(parameters, classificator)

		try:
			if validation_errors := classificator.load():
				for error_data in validation_errors:
					origin: str = f"{error_data.line.module}.{error_data.line.number}"
					self.printer.error(f"{error_data.message}", origin = origin)

				self.printer.critical("Script failure due to syntax validation errors.")

		except exceptions.utils.classificator.MissingRegisterError as exception:
			self.printer.critical(str(exception))

		return classificator

	def __load_register(self, parameters: Parameters, classificator: AttributesClassificator):
		"""
		Loag register if available.

		Args:
			parameters (Parameters): Required by command parameters.
			classificator (AttributesClassificator): Attributes classificator.
		"""

		is_environment: bool = bool(self.system_objects.options.REGISTER)
		message: str | None = None

		if parameters.register:
			override_part: str = "(environment option overridden)" if is_environment else ""
			message = f"Register loaded from key{override_part}."
			classificator.load_register(parameters.register)

		elif is_environment:
			message = "Register loaded from environment option."
			classificator.load_register(self.system_objects.options.REGISTER)

		if not parameters.is_output_json and message:
			self.printer.debug(message)

	def __print_result(self, operation: "Operation"):
		"""
		Print attribute classification result.

		Args:
			result (Operation): Attribute classification result.
		"""

		if operation.in_register is False:
			self.printer.error("Attribute not found in register.")
			return

		if not operation.result:
			self.printer.emit("Attribute must be deleted.")
			return

		self.printer.emit(f"Result: [i]{operation.result}[/i]")
		classificator_type :str = operation.type.name.lower() if operation.type else "[red]null[/red]"
		self.printer.emit(f"Type: {classificator_type}")
