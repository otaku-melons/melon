from dataclasses import dataclass
from pathlib import Path

from .enums import Case, ClassificatorType, Directive

@dataclass
class WorkData:
	"""Script parsing process data."""

	current_type: ClassificatorType | None = None
	current_case: Case | None = None
	is_delete: bool = False

@dataclass(frozen = True)
class ProcessingResult:
	"""Classificator processing result."""

	is_operation_found: bool = False
	name: str | None = None
	type: ClassificatorType | None = None
	delete: bool | None = None
	is_renamed: bool | None = None

	def to_dict(self) -> dict:
		"""
		Generate dictionary representation of data.

		Returns:
			dict: Dictionary representation of data..
		"""

		return {
			"is_operation_found": self.is_operation_found,
			"name": self.name,
			"type": self.type.name.lower() if self.type else None,
			"delete": self.delete,
			"is_renamed": self.is_renamed,
		}

@dataclass(frozen = True)
class ExecutableLine:
	"""Script executable line."""

	file: Path
	number: int
	value: str

	@property
	def is_operation(self) -> bool:
		"""Condition: is line operation."""

		return not self.is_directive()

	def is_directive(self, directive: Directive | None = None) -> bool:
		"""
		Check is executable line is directive.

		Args:
			directive (Directive | None): Target direcrive to check.

		Returns:
			bool: `True` if line is representation of directive.
		"""

		if directive:
			return self.value.startswith(f"@{directive.name}")

		return self.value.startswith("@")

@dataclass(frozen = True)
class Operation:
	"""Classificator processing operation."""

	name: str
	type: ClassificatorType | None
	delete: bool | None
	rename: str | None
	case: Case | None

	def process(self, value: str) -> str | None:
		"""
		Обрабатывает значение.

		:param value: Обрабатываемое значение.
		:type value: str
		:return: Результат обработки.
		:rtype: str | None
		"""

		if self.delete:
			return None

		if self.rename:
			return self.rename

		match self.case:
			case Case.low: return value.lower()
			case Case.title: return value.title()
			case Case.up: return value.upper()

		return value

@dataclass(frozen = True)
class ScriptValidationErrorData:
	"""Script validation error data."""

	line: ExecutableLine
	message: str
