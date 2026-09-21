from typing import TYPE_CHECKING, override

from ..base import BaseCheck
from ..enums import ChecksStatuses

if TYPE_CHECKING:
	from pathlib import Path

	from ...operator import ParserOperator

class Check(BaseCheck):
	"""Linter check."""

	@override
	def _check(self, operator: "ParserOperator"):
		"""
		Process linter check. 

		Use `_emit()` or `_ok()` to interrupt checking. If no stop signal rised check considered successfully completed.

		:param operator: Parser operator.
		:type operator: ParserOperator
		"""

		manifest_path: "Path" = operator.path / "manifest.json"

		if not manifest_path.exists():
			self._emit(ChecksStatuses.Error, "Parser must provides manifest.")