from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, NoReturn

from ..enums import ChecksStatuses
from .signals import CheckStopSignal
from .structs import CheckResult

if TYPE_CHECKING:
	from ...operator import ParserOperator

class BaseCheck(ABC):
	"""Base linter check."""

	#==========================================================================================#
	# >>>>> PROPERTIES <<<<< #
	#==========================================================================================#

	@property
	def name(self) -> str:
		"""Rule name."""

		return self.__class__.__module__.split(".")[-1]

	#==========================================================================================#
	# >>>>> PROTECTED METHODS <<<<< #
	#==========================================================================================#	

	def _emit(self, status: ChecksStatuses, message: str | None = None) -> NoReturn:
		"""
		Raise lint check stop signal and emit message.

		:param status: Check status.
		:type status: ChecksStatuses
		:param message: Check message.
		:type message: str | None
		:raises CheckStopSignal: Stop checking signal.
		"""

		raise CheckStopSignal(status, message)

	def _ok(self, message: str | None = None) -> NoReturn:
		"""
		Raise lint check stop signal and emit OK message.

		:param message: Check message.
		:type message: str | None
		"""

		self._emit(ChecksStatuses.OK, message)

	#==========================================================================================#
	# >>>>> OVERRIDABLE METHODS <<<<< #
	#==========================================================================================#

	@abstractmethod
	def _check(self, operator: "ParserOperator"):
		"""
		Process linter check. 

		Use `_emit()` or `_ok()` to interrupt checking. If no stop signal rised check considered successfully completed.

		:param operator: Parser operator.
		:type operator: ParserOperator
		"""

		return None

	def _post_init(self):
		"""This method will be executed after instance initialization."""

		pass

	#==========================================================================================#
	# >>>>> PUBLIC METHODS <<<<< #
	#==========================================================================================#

	def __init__(self):
		"""Base linter check."""

		self._post_init()

	def check(self, operator: "ParserOperator") -> CheckResult:
		"""
		Process linter check. 

		:param operator: Parser operator.
		:type operator: ParserOperator
		:return: Check result.
		:rtype: CheckResult
		"""

		try:
			self._check(operator)
		except CheckStopSignal as exception:
			return CheckResult(self.name, exception.status, exception.message)

		return CheckResult(self.name, ChecksStatuses.OK)