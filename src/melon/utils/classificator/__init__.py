import shlex
from collections.abc import Callable, Sequence
from os import PathLike
from pathlib import Path
from typing import TYPE_CHECKING

from dublib.functions.data.dictionary import deep_merge
from dublib.functions.filesystem import json, text

from ...core import exceptions
from ...core.base.formats.base_format.person import Person
from .enums import AttributeType, Case, Directive, _DirectiveValidationData
from .structs import (
	ExecutableLine,
	Operation,
	ScriptValidationErrorData,
	WorkData,
)

if TYPE_CHECKING:
	from ...core.base.formats.base_format.data import BaseTitleData

class AttributesClassificator:
	"""Attributes classificator."""

	def __init__(self, entry_point: Path):
		"""
		Attributes classificator.

		Args:
			entry_point (Path): Script entry point file path.
		"""

		self.__entry_point: Path = entry_point

		self.__script: tuple[ExecutableLine, ...] = ()
		self.__operations: tuple[Operation, ...] = ()

		self.__register: dict[AttributeType, tuple[str, ...]] = {}

	def compare_with_register(self) -> tuple[Operation, ...]:
		"""
		Compare operations results with register.

		Returns:
			tuple[Operation, ...] | None: Operations that not found in register or `None` if register not loaded.

		Raises:
			MissingRegisterError: Register missing.
		"""

		if not self.register:
			raise exceptions.utils.classificator.MissingRegisterError()

		results: list[Operation] = []

		for operation in self.__operations:

			if operation.is_deleted:
				if operation.in_register:
					results.append(operation)
				continue

			if not operation.in_register:
				results.append(operation)

		return tuple(results)

	def classify(self, target: str, ignore_case: bool = False) -> Operation | None:
		"""
		Classify attribute.

		Args:
			target (str): Target for processing.
			ignore_case (bool): Ignore letters case.

		Returns:
			Operation | None: Classification operation or `None` if not found.
		"""

		if ignore_case:
			operations_cache: dict[str, Operation] = {operation.value.lower(): operation for operation in self.__operations}
		else:
			operations_cache: dict[str, Operation] = {operation.value: operation for operation in self.__operations}

		return operations_cache.get(target.lower() if ignore_case else target)

	def load(self) -> tuple[ScriptValidationErrorData, ...] | None:
		"""
		Load script from entry point file.

		Returns:
			tuple[ScriptValidationErrorData, ...] | None: Script syntax validation errors.

		Raises:
			FileNotFoundError: Entry point not found.
			IsADirectoryError: Given directory instead entry point file.
		"""

		if not self.entry_point.exists():
			raise FileNotFoundError(self.entry_point)

		if not self.entry_point.is_file():
			raise IsADirectoryError(self.entry_point)

		script: list[ExecutableLine] = self.__read_script_file(self.entry_point, entry_point = True)

		if errors := self.__validate_script():
			return errors

		self.__script = tuple(script)
		self.__operations = self.__parse_operations(self.__script)

	def load_register(self, file: PathLike[str] | str):
		"""
		Load attributes register. Also clear exists register data.

		Args:
			file (PathLike[str] | str): Path to register file.
		"""

		data: dict[str, list[str]] = json.read(file)
		self.__register.clear()

		for attribute_type in AttributeType:
			self.__register[attribute_type] = tuple(data.get(attribute_type.value, ()))

	def process_title(self, data: "BaseTitleData"):
		"""
		Process title attributes.

		Args:
			title (BaseTitleController[BaseTitleData]): Title controller.
		"""

		attributes: dict[AttributeType, list[str]] = {}

		deep_merge(attributes, self.__process_title_attributes(data.genres))
		deep_merge(attributes, self.__process_title_attributes(data.tags))

		data.set_genres(attributes.get(AttributeType.genre, ()))
		data.set_tags(attributes.get(AttributeType.tag, ()))
		data.set_franchises(attributes.get(AttributeType.franchise, ()))

		for person_name in attributes.get(AttributeType.person, ()):
			if not data.find_person(person_name):
				data.add_person(Person(person_name))

	@property
	def entry_point(self) -> Path:
		"""Entry point."""

		return self.__entry_point

	@property
	def operations(self) -> tuple[Operation, ...]:
		"""Attributes processing operations."""

		return self.__operations

	@property
	def register(self) -> dict[AttributeType, tuple[str, ...]]:
		"""Classificators register."""

		return self.__register.copy()

	@property
	def work_directory(self) -> Path:
		"""Script work directory."""

		return self.__entry_point.parent

	def __extract_directive_values(self, line: ExecutableLine) -> tuple[str, ...]:
		"""
		Extract directive value.

		Args:
			line (ExecutableLine): Script executable line with directive.

		Returns:
			tuple[str, ...]: Directive values.
		"""

		parts: list[str] = line.value.split("[", maxsplit = 1)

		if len(parts) == 1:
			return ()

		value_string: str = parts[1].rstrip("]")
		value_string_elements: list[str] = value_string.split(",")
		result: list[str] = []

		for element in value_string_elements:
			result.append(element.strip())

		return tuple(result)

	def __include_script(self, line: ExecutableLine) -> list[ExecutableLine]:
		"""
		Process directive: `include`.

		Args:
			line (ExecutableLine): Script executable line.

		Returns:
			list[ExecutableLine]: Included executable lines.

		Raises:
			FileNotFoundError: Script file not found.
		"""

		filename: str = self.__extract_directive_values(line)[0]
		script_file: Path = self.work_directory / f"{filename}.mcs"

		if not script_file.exists():
			raise FileNotFoundError(script_file)

		return self.__read_script_file(script_file, entry_point = False)

	def __parse_operations(self, script: Sequence[ExecutableLine]) -> tuple[Operation, ...]:
		"""
		Parse attributes processing operations.

		Args:
			script (Sequence[ExecutableLine]): Script executable lines.

		Returns:
			tuple[Operation, ...]: Attributes processing operations.
		"""

		operations: list[Operation] = []
		work_data = WorkData()

		directive_processors: dict[Directive, Callable] = {
			Directive.drop: self.__process_directive_drop,
			Directive.case: self.__process_directive_case,
			Directive.delete: self.__process_directive_delete,
			Directive.type: self.__process_directive_type,
		}

		for line in script:

			if line.is_operation:
				operation_line: str = line.value
				parts: list[str] = shlex.split(operation_line)
				value: str = parts[0]
				new_name: str | None = None

				if len(parts) == 3 and parts[1] == ">":
					new_name = parts[2]

				result: str = new_name if new_name else self.__transform_operation_value_case(value, work_data)

				operations.append(Operation(
					value = value,
					type = work_data.current_type,
					is_deleted = work_data.is_delete,
					is_renamed = bool(new_name),
					case = work_data.current_case,
					result = None if work_data.is_delete else result,
					in_register = self.__search_in_register(work_data.current_type, result),
				))

				continue

			for directive in Directive:
				if line.is_directive(directive):
					directive_processors[directive](work_data, line)

		return tuple(operations)

	def __process_directive_case(self, work_data: WorkData, line: ExecutableLine):
		"""
		Process directive: `case`.

		Args:
			work_data (WorkData): Script parsing process data.
			line (ExecutableLine): Script executable line.

		Raises:
			UnknownDirectiveValueError: Unknown value.
		"""

		value = self.__extract_directive_values(line)[0]

		try:
			work_data.current_case = Case(value)
		except ValueError:
			raise exceptions.utils.classificator.UnknownDirectiveValueError(Directive.case, value)

	def __process_directive_delete(self, work_data: WorkData, line: ExecutableLine):  # noqa: ARG002
		"""
		Process directive: `delete`.

		Args:
			work_data (WorkData): Script parsing process data.
			line (ExecutableLine): Script executable line.
		"""

		work_data.is_delete = True

	def __process_directive_drop(self, work_data: WorkData, line: ExecutableLine):
		"""
		Process directive: `drop`.

		Args:
			work_data (WorkData): Script parsing process data.
			line (ExecutableLine): Script executable line.

		Raises:
			UnknownDirectiveValueError: Unknown value.
		"""

		values = self.__extract_directive_values(line)

		# Drop all values by default.
		if not values:
			values = ("type", "case", "delete")

		for value in values:
			match value:
				case "type": work_data.current_type = None
				case "case": work_data.current_case = None
				case "delete": work_data.is_delete = False
				case _: raise exceptions.utils.classificator.UnknownDirectiveValueError(Directive.drop, value)

	def __process_directive_type(self, work_data: WorkData, line: ExecutableLine):
		"""
		Process directive: `type`.

		Args:
			work_data (WorkData): Script parsing process data.
			line (ExecutableLine): Script executable line.

		Raises:
			UnknownDirectiveValueError: Unknown value.
		"""

		value = self.__extract_directive_values(line)[0]

		try:
			work_data.current_type = AttributeType(value)
		except ValueError:
			raise exceptions.utils.classificator.UnknownDirectiveValueError(Directive.type, value)

	def __process_title_attributes(self, classificators: "Sequence[str]") -> dict[AttributeType, list[str]]:
		"""
		Process title classificators.

		Args:
			classificators (Sequence[str]): Classificators.

		Returns:
			dict[AttributeType, list[str]]: Processed classificators.

		Raises:
			exceptions.utils.classificator.ClassificationError: Description.
		"""

		results: dict[AttributeType, list[str]] = {}

		for classificator in classificators:
			result = self.classify(classificator, ignore_case = True)

			if not result or not result.value:
				raise exceptions.utils.classificator.ClassificationError(f"Operation not found for attribute: \"{classificator}\".")

			if not result.result:
				continue

			if result.in_register is False:
				raise exceptions.utils.classificator.ClassificationError(f"Attribute \"{classificator}\" not found in register.")

			if not result.type:
				raise exceptions.utils.classificator.ClassificationError(f"Unknown attribute type: \"{classificator}\".")

			results.setdefault(result.type, []).append(result.result)

		return results

	def __read_script_file(self, script_file: Path, entry_point: bool = True) -> list[ExecutableLine]:
		"""
		Read script file.

		Args:
			script_file (Path): Path to script file.
			entry_point (bool): Is file entry point.

		Returns:
			list[ExecutableLine]: Script executable lines.

		Raises:
			IncludeDirectiveDeniedError: Include directive denied.
			MissingRegisterError: Register missing.
		"""

		script_lines: list[str] = text.read(script_file, split = True, strip_level = 1)
		executable_lines: list[ExecutableLine] = []

		for index in range(len(script_lines)):
			line: str = script_lines[index]
			line_number: int = index + 1

			if not line or line.startswith("#"):
				continue

			buffer = ExecutableLine(script_file.stem, entry_point, line_number, line)

			if not entry_point:
				for directive_type in Directive:
					if buffer.is_directive(directive_type) and directive_type.value.only_in_entry_point:
						raise exceptions.utils.classificator.DirectiveDeniedInNonEntryPointError(script_file, line_number, Directive.include.name)

			if buffer.is_directive(Directive.include):
				executable_lines += self.__include_script(buffer)
				continue

			if buffer.is_directive(Directive.register):
				if not self.register:
					raise exceptions.utils.classificator.MissingRegisterError()
				continue

			executable_lines.append(buffer)

		# Add drop directive at end of file if missing.
		if executable_lines and not executable_lines[-1].is_directive(Directive.drop):
			executable_lines.append(ExecutableLine(script_file.stem, entry_point, -1, f"@{Directive.drop.name}"))

		return executable_lines

	def __search_in_register(self, classificator_type: AttributeType | None, name: str | None) -> bool | None:
		"""
		Search classificator in register.

		Args:
			classificator_type (AttributeType | None): Classificator type.
			name (str | None): Classificator name.

		Returns:
			bool | None: `True` if found in register.
		"""

		if not name or not self.__register:
			return

		if classificator_type:
			return name in self.__register[classificator_type]

		for classificator_type in AttributeType:
			if name in self.__register[classificator_type]:
				return True

		return False

	def __transform_operation_value_case(self, value: str, work_data: WorkData) -> str:
		"""
		Transform operation value case.

		Args:
			value (str): Operation value.
			work_data (WorkData): Script parsing process data.

		Returns:
			str: Operation cased result.
		"""

		match work_data.current_case:
			case Case.low: return value.lower()
			case Case.title: return value.title()
			case Case.up: return value.upper()

		return value

	def __validate_directive(self, line: ExecutableLine) -> list[ScriptValidationErrorData]:
		"""
		Validate directive.

		Args:
			line (ExecutableLine): Script executable line.

		Returns:
			list[ScriptValidationErrorData]: Validation errors.
		"""

		errors: list[ScriptValidationErrorData] = []

		if "[" in line.value and "]" not in line.value:
			errors.append(ScriptValidationErrorData(line, "Unclosed values declaration."))

		if "]" in line.value and "[" not in line.value:
			errors.append(ScriptValidationErrorData(line, "Unopened values array."))

		directive_elements: list[str] = line.value.split("[", maxsplit = 1)
		name: str = directive_elements[0][1:].rstrip()

		if name not in tuple(Element.name for Element in Directive):
			errors.append(ScriptValidationErrorData(line, f"Unknown directive: \"@{name}\"."))
			return errors

		directive: Directive = Directive[name]
		validation_data: _DirectiveValidationData = directive.value
		values: tuple[str, ...] = self.__extract_directive_values(line)

		if not values and not validation_data.allow_empty:
			errors.append(ScriptValidationErrorData(line, f"Directive \"@{directive.name}\" must have values."))

		if len(values) > 1 and not validation_data.allow_list:
			errors.append(ScriptValidationErrorData(line, f"Directive \"@{directive.name}\" must have only one value."))

		if validation_data.values:
			for value in values:
				if value not in validation_data.values:
					errors.append(ScriptValidationErrorData(line, f"Unknown value \"{value}\" for directive \"@{directive.name}\"."))

		if not line.is_entry_point and validation_data.only_in_entry_point:
			errors.append(ScriptValidationErrorData(line, f"Directive \"@{directive.name}\" allowed only in entry point."))

		return errors

	def __validate_operation(self, line: ExecutableLine) -> list[ScriptValidationErrorData]:
		"""
		Validate operation.

		Args:
			line (ExecutableLine): Script executable line.

		Returns:
			list[ScriptValidationErrorData]: Validation errors.
		"""

		errors: list[ScriptValidationErrorData] = []
		operation_parts: tuple[str, ...] = tuple(shlex.split(line.value))
		parts_count: int = len(operation_parts)
		is_renaming_operator_exists: bool = parts_count > 1 and operation_parts[1] == ">"

		if parts_count > 1 and not is_renaming_operator_exists:
			errors.append(ScriptValidationErrorData(line, "Renaming operation without operator."))

		if parts_count == 2 and is_renaming_operator_exists:
			errors.append(ScriptValidationErrorData(line, "Renaming operator requires right side value."))

		if parts_count > 3:
			errors.append(ScriptValidationErrorData(line, "Too many elements in operation."))

		return errors

	def __validate_script(self) -> tuple[ScriptValidationErrorData, ...]:
		"""
		Validate script syntax.

		Returns:
			tuple[ScriptValidationErrorData, ...]: Script validation error.
		"""

		errors: list[ScriptValidationErrorData] = []

		for line in self.__script:
			if line.is_directive(): errors += self.__validate_directive(line)
			elif line.is_operation: errors += self.__validate_operation(line)
			else: errors.append(ScriptValidationErrorData(line, "Unknown string assignment."))

		return tuple(errors)
