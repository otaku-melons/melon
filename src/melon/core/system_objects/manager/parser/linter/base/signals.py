from ..enums import ChecksStatuses

class CheckStopSignal(Exception):
	"""Checking stop signal."""

	@property
	def message(self) -> str | None:
		"""Check message."""

		return self._message

	@property
	def status(self) -> ChecksStatuses:
		"""Check status."""

		return self._status

	def __init__(self, status: ChecksStatuses, message: str | None):
		"""
		Checking stop signal.

		:param status: Check status.
		:type status: ChecksStatuses
		:param message: Check message.
		:type message: str | None
		"""

		self._status: ChecksStatuses = status
		self._message: str | None = message
