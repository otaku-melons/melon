from ..enums import CheckStatus

class CheckStopSignalError(Exception):
	"""Checking stop signal."""

	@property
	def message(self) -> str | None:
		"""Check message."""

		return self._message

	@property
	def status(self) -> CheckStatus:
		"""Check status."""

		return self._status

	def __init__(self, status: CheckStatus, message: str | None):
		"""
		Checking stop signal.

		:param status: Check status.
		:type status: CheckStatus
		:param message: Check message.
		:type message: str | None
		"""

		self._status: CheckStatus = status
		self._message: str | None = message
