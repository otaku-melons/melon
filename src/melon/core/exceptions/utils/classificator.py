from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from pathlib import Path

	from ....utils.classificator.enums import Directive

class ClassificationError(Exception):
	"""Exception: classification error."""

	def __init__(self, message: str):
		"""
		Exception: classification error.

		Args:
			message (str): Error message.
		"""

		super().__init__(message)

class DirectiveDeniedInNonEntryPointError(Exception):
	"""Exception: directive denied in non entry point."""

	def __init__(self, file: "Path", line: int, directive: str):
		"""
		Exception: directive denied in non entry point.

		Args:
			file (Path): Path to file with error.
			line (int): Error line number.
			directive (str): Directive name.
		"""

		super().__init__(f"File \"{file}\". Directive \"@{directive}\" at line {line}.")

class MissingRegisterError(Exception):
	"""Exception: register missing."""

	def __init__(self, register_path: "Path"):
		"""
		Exception: register missing.

		Args:
			register_path (Path): Register file path.
		"""

		super().__init__(register_path)

class UnknownDirectiveValueError(Exception):
	"""Exception: unknown directive value."""

	def __init__(self, directive: "Directive", value: str):
		"""
		Exception: script runtime error.

		Args:
			directive (Directive): Directive.
			value (str): Unknown value.
		"""

		super().__init__(f"\"{value}\" for \"@{directive.name}\".")
