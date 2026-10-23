from enum import Enum

class CheckStatus(Enum):
	"""Linter rule check status."""

	OK = 0
	Skipped = 1
	Error = 2
	Warning = 3
