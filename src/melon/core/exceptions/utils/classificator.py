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

class IncludeDirectiveDeniedError(Exception):
	"""Exception: directive `include` denied."""

	def __init__(self, file: "Path", line: int):
		"""
		Exception: directive `include` denied.

		Args:
			file (Path): Path to file with error.
			line (int): Error line number.
		"""

		super().__init__(f"File \"{file}\". Line {line}.")

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
