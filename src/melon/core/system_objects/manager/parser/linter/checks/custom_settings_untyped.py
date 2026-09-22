import os
from typing import TYPE_CHECKING, override

from dublib.functions.filesystem import json

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

		settings_path: "Path" = operator.path / "settings.json"

		if not settings_path.exists():
			self._emit(ChecksStatuses.Skipped, "Settings defaults not provided.")

		settings: dict = json.read(settings_path)
		files: list[str] = os.listdir(operator.path)

		if settings.get("custom"):
			if "custom.py" not in files:
				self._emit(ChecksStatuses.Error, "Custom settings must provide typing model.")
		
		else:
			self._emit(ChecksStatuses.Skipped, "Custom settings not provided.")
