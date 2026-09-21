from enum import Enum

class ChecksStatuses(Enum):
	"""Checks statuses enumeration."""

	OK = 0
	Skipped = 1
	Error = 2
	Warning = 3