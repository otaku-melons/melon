from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from pathlib import Path

	from ....utils.classificator import ExecutableLine
	from ....utils.classificator.enums import Directive

class IncludeDirectiveDeniedError(Exception):
	"""Exception: directive `include` denied."""

	def __init__(self, file: "Path", line: int):
		"""
		Exception: directive `include` denied..

		Args:
			file (Path): Path to file with error.
			line (int): Error line number.
		"""

		super().__init__(f"File \"{file}\". Line {line}.")

class ScriptRuntimeError(Exception):
	"""Exception: script runtime error."""

	def __init__(self, line: "ExecutableLine", message: str):
		"""
		Exception: script runtime error.

		Args:
			line (ExecutableLine): Script executable line.
			message (str): Error message.
		"""

		super().__init__(f"[{line.file.name}:{line.number}] {message}")

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
