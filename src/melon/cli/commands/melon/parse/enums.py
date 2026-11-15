from enum import Enum

class ParsingSignal(Enum):
	"""Parsing signal."""

	OK = 0
	Break = 1
	NotFound = 2
	Error = 3
