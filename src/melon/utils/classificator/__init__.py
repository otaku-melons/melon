import shlex
from collections.abc import Callable, Sequence
from os import PathLike
from pathlib import Path
from typing import cast

from dublib.functions.filesystem import text

from ...core import exceptions
from .enums import Case, ClassificatorType, Directive
from .structs import (
	ExecutableLine,
	Operation,
	ProcessingResult,
	ScriptValidationErrorData,
	WorkData,
)

class ClassificatorsProcessor:
	"""Classificators processor."""

	def __init__(self, entry_point: PathLike[str] | str):
		"""
		Classificators processor.

		Args:
			entry_point (PathLike[str] | str): Classificators processing script entry point.
		"""

		self.__entry_point: Path = Path(entry_point)

		self.__operations: tuple[Operation, ...] = ()

		self.__check_entry_point()

	def classify(self, target: str, ignore_case: bool = False) -> ProcessingResult:
		"""
		Process classificator.

		Args:
			target (str): Target for processing.
			ignore_case (bool): Ignore letters case.

		Returns:
			ProcessingResult: Classification result.
		"""

		if ignore_case:
			operations_cache = {operation.name.lower(): operation for operation in self.operations}
		else:
			operations_cache = {operation.name: operation for operation in self.operations}

		target_operation: Operation | None = operations_cache.get(target.lower() if ignore_case else target)
		if not target_operation:
			return ProcessingResult()

		name: str | None = target_operation.process(target)
		is_renamed: bool | None = not target == name
		if target_operation.delete: is_renamed = None

		return ProcessingResult(
			is_operation_found = True,
			name = name,
			type = target_operation.type,
			delete = target_operation.delete,
			is_renamed = is_renamed,
		)

	def load(self) -> tuple[ScriptValidationErrorData, ...] | None:
		"""
		Load and validate script.

		Returns:
			tuple[ScriptValidationErrorData, ...] | None: Script validation errors or `None` if no errors.
		"""

		script: tuple[ExecutableLine, ...] = tuple(self.__read_script_file(self.entry_point, entry_point = True))

		if errors := self.__validate_script(script):
			return errors

		self.__operations = self.__parse_operations(script)

	@property
	def entry_point(self) -> Path:
		"""Entry point."""

		return self.__entry_point

	@property
	def operations(self) -> tuple[Operation, ...]:
		"""Classificators processing operations."""

		return self.__operations

	@property
	def work_directory(self) -> Path:
		"""Script work directory."""

		return self.__entry_point.parent

	def __check_entry_point(self):
		"""
		Check entry point.

		Raises:
			FileNotFoundError: Entry point not found.
			IsADirectoryError: Given directory instead entry point file.
		"""

		if not self.__entry_point.exists():
			raise FileNotFoundError(self.__entry_point)

		if not self.__entry_point.is_file():
			raise IsADirectoryError(self.__entry_point)

	def __extract_directive_values(self, line: ExecutableLine) -> str | tuple[str, ...]:
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

		if not filename.endswith(".ini"):
			filename += ".ini"

		script_file: Path = self.work_directory / filename

		if not script_file.exists():
			raise FileNotFoundError(script_file)

		return self.__read_script_file(script_file, entry_point = False)

	def __parse_operations(self, script: Sequence[ExecutableLine]) -> tuple[Operation, ...]:
		"""
		Parse classificators processing operations.

		Args:
			script (Sequence[ExecutableLine]): Script executable lines.

		Returns:
			tuple[Operation, ...]: Classificators processing operations.
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
				rename: str | None = None

				if len(parts) == 3 and parts[1] == ">":
					rename = parts[2]

				operations.append(Operation(
					name = parts[0],
					type = work_data.current_type,
					delete = work_data.is_delete,
					rename = rename,
					case = work_data.current_case,
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
			work_data.current_type = ClassificatorType(value)
		except ValueError:
			raise exceptions.utils.classificator.UnknownDirectiveValueError(Directive.type, value)

	def __read_script_file(self, script_file: Path, entry_point: bool = True) -> list[ExecutableLine]:
		"""
		Read script file.

		Args:
			script_file (Path): Path to script file.
			entry_point (bool): Is file entry point.

		Returns:
			list[ExecutableLine]: Script executable lines.

		Raises:
			exceptions.utils.classificator.IncludeDirectiveDeniedError: Include directive denied.
		"""

		script_lines: list[str] = text.read(script_file, split = True, strip_level = 2)
		executable_lines: list[ExecutableLine] = []

		for index in range(len(script_lines)):
			line: str = script_lines[index]
			line_number: int = index + 1

			if line.startswith("#"):
				continue

			if line.startswith(f"@{Directive.include.name}"):

				if not entry_point:
					raise exceptions.utils.classificator.IncludeDirectiveDeniedError(script_file, line_number)

				buffer = ExecutableLine(script_file, line_number, line)
				executable_lines += self.__include_script(buffer)
				continue

			executable_lines.append(ExecutableLine(script_file, line_number, line))

		drop_directive: str = f"@{Directive.drop.name}"

		# Add drop directive at end of file if missing.
		if executable_lines and executable_lines[-1].value != drop_directive:
			executable_lines.append(ExecutableLine(script_file, -1, drop_directive))

		return executable_lines

	def __validate_directive(self, line: ExecutableLine) -> list[ScriptValidationErrorData]:
		"""
		Validate directive.

		Args:
			line (ExecutableLine): Script executable line.

		Returns:
			list[ScriptValidationErrorData]: Validation errors.
		"""

		ERRORS: list[ScriptValidationErrorData] = []

		if "[" in line.value and "]" not in line.value:
			ERRORS.append(ScriptValidationErrorData(line, "Unclosed values declaration."))
		if "]" in line.value and "[" not in line.value:
			ERRORS.append(ScriptValidationErrorData(line, "Unopened values array."))

		DirectiveElements: list[str] = line.value.split("[", maxsplit = 1)

		Name = DirectiveElements[0][1:].rstrip()

		if Name not in tuple(Element.name for Element in Directive):
			ERRORS.append(ScriptValidationErrorData(line, f"Unknown directive: \"@{Name}\"."))
			return ERRORS

		directive: Directive | None = None

		for Element in Directive:
			if Element.name == Name:
				directive = Element
				break

		directive = cast("Directive", directive)

		ValidationData = directive.value
		Values = self.__extract_directive_values(line)

		if not Values and not ValidationData.allow_empty:
			ERRORS.append(ScriptValidationErrorData(line, f"Directive \"@{directive.name}\" must have values."))

		if len(Values) > 1 and not ValidationData.allow_list:
			ERRORS.append(ScriptValidationErrorData(line, f"Directive \"@{directive.name}\" must have only one value."))

		if ValidationData.values:
			for Value in Values:
				if Value not in ValidationData.values:
					ERRORS.append(ScriptValidationErrorData(line, f"Unknown value \"{Value}\" for directive \"@{directive.name}\"."))

		return ERRORS

	def __validate_operation(self, line: ExecutableLine) -> list[ScriptValidationErrorData]:
		"""
		Validate operation.

		Args:
			line (ExecutableLine): Script executable line.

		Returns:
			list[ScriptValidationErrorData]: Validation errors.
		"""

		ERRORS: list[ScriptValidationErrorData] = []

		OperationString: str = line.value.lstrip("*").lstrip()
		OperationParts: tuple[str, ...] = tuple(shlex.split(OperationString))

		if len(OperationParts) == 2:

			if OperationParts[1] not in ("-", ">"):
				Operator: str = OperationParts[1]
				ERRORS.append(ScriptValidationErrorData(line, f"Unknown operator: \"{Operator}\"."))

			if OperationParts[1] == ">":
				ERRORS.append(ScriptValidationErrorData(line, "Renaming operator requires value."))

		elif len(OperationParts) == 3:

			if OperationParts[1] != ">":
				ERRORS.append(ScriptValidationErrorData(line, "Only renaming operator supports two values."))

		return ERRORS

	def __validate_script(self, script: Sequence[ExecutableLine]) -> tuple[ScriptValidationErrorData, ...]:
		"""
		Validate script.

		Args:
			script (Sequence[ExecutableLine]): Script executable lines.

		Returns:
			tuple[ScriptValidationErrorData, ...]: Script validation error.
		"""

		errors: list[ScriptValidationErrorData] = []

		for line in script:
			if line.is_directive(): errors += self.__validate_directive(line)
			elif line.is_operation: errors += self.__validate_operation(line)
			else: errors.append(ScriptValidationErrorData(line, "Unknown string assignment."))

		return tuple(errors)
