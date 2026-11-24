from dataclasses import dataclass

from .enums import AttributeType, Case, Directive

@dataclass
class WorkData:
	"""Script parsing process data."""

	current_type: AttributeType | None = None
	current_case: Case | None = None
	is_delete: bool = False

@dataclass(frozen = True)
class ExecutableLine:
	"""Script executable line."""

	module: str
	is_entry_point: bool
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
	"""Attributes processing operation."""

	value: str

	type: AttributeType | None
	is_deleted: bool
	is_renamed: bool
	case: Case | None

	result: str | None
	in_register: bool | None

	def to_dict(self) -> dict:
		"""
		Generate dictionary representation of data.

		Returns:
			dict: Dictionary representation of data..
		"""

		return {
			"value": self.value,
			"type": self.type.name.lower() if self.type else None,
			"is_deleted": self.is_deleted,
			"is_renamed": self.is_renamed,
			"case": self.case,
			"result": self.result,
			"in_register": self.in_register,
		}

@dataclass(frozen = True)
class ScriptValidationErrorData:
	"""Script validation error data."""

	line: ExecutableLine
	message: str
