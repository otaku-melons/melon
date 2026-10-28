from typing import override

from ..enums import Align
from .base import BaseElement

class AlignableElement(BaseElement):
	"""Alignable element."""

	#==========================================================================================#
	# >>>>> OVERRIDABLE METHODS <<<<< #
	#==========================================================================================#

	@override
	def _post_init(self):
		"""Execute after instance initialization."""

		self._align: Align | None = None

	#==========================================================================================#
	# >>>>> PUBLIC METHODS <<<<< #
	#==========================================================================================#

	def set_align(self, align: Align | None):
		"""
		Set text align.

		Args:
			align (Align | None): Text align.
		"""

		self._align = align
