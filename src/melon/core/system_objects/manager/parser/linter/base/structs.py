from dataclasses import dataclass

from ..enums import ChecksStatuses

@dataclass(frozen = True)
class CheckResult:
	"""Check result."""

	name: str
	status: ChecksStatuses
	message: str | None = None
