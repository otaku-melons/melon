import os
from typing import TYPE_CHECKING, override

from ..base import BaseCheck
from ..enums import ChecksStatuses

if TYPE_CHECKING:
	from ...operator import ParserOperator

class Check(BaseCheck):
	"""Linter check."""

	@override
	def _check(self, operator: "ParserOperator"):
		"""
		Process linter check. 

		Use `_emit()` or `_ok()` to interrupt checking. If no stop signal raised check considered successfully completed.

		:param operator: Parser operator.
		:type operator: ParserOperator
		"""

		lower_files: list[str] = [file.lower() for file in os.listdir(operator.path)]

		for file in lower_files:
			if file.startswith("readme."):
				self._emit(ChecksStatuses.OK)

		self._emit(ChecksStatuses.Warning, "Readme file not provided.")