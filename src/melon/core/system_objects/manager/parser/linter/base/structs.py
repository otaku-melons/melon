from dataclasses import dataclass

from ..enums import CheckStatus

@dataclass(frozen = True)
class CheckResult:
	"""Check result."""

	name: str
	status: CheckStatus
	message: str | None = None
