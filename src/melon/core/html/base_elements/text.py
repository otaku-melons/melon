from typing import TYPE_CHECKING

from bs4 import Tag

from ... import exceptions
from ..allowed_tags import ALLOWED_TAGS
from .base import BaseElement

if TYPE_CHECKING:
	from collections.abc import Sequence

	from ..allowed_tags import TagData
	from ..footnote import Footnote

class TextElement(BaseElement):
	"""Text element."""

	def __init__(self, text: str, allow_footnotes: bool = False):
		"""
		Text element.

		Args:
			text (str): Element text.
			allow_footnotes (bool): Allow footnotes in element text.
		"""

		self._is_footnotes_allowed: bool = allow_footnotes
		self._text: str = self._validate_text(text)

		self._footnotes: list[Footnote] = []

	def set_footnotes(self, footnotes: "Sequence[Footnote]"):
		"""
		Set footnotes and clear exists.

		Args:
			footnotes (Sequence[Footnote]): New footnotes.
		"""

		self._footnotes.clear()
		self._footnotes.extend(footnotes)

	@property
	def footnotes(self) -> tuple["Footnote", ...]:
		"""Footnotes."""

		return tuple(self._footnotes)

	@property
	def is_footnotes_allowed(self) -> bool:
		"""Condition: is footnotes allowed."""

		return self._is_footnotes_allowed

	def _validate_text(self, text: str) -> str:
		"""
		Validate text.

		Args:
			text (str): Validable text.

		Raises:
			ValueError: Invalid text.

		Returns:
			str: Stripped text.
		"""

		soup = self._parse(text)

		if not soup.get_text().strip():
			raise ValueError("Text can't be empty.")

		for child in soup.find_all():

			if isinstance(child, Tag):
				tag_rules: TagData | None = ALLOWED_TAGS.get_tag(child.name)

				if not tag_rules:
					raise exceptions.html.UnresolvedTagError(child.name)

				if child.name == "a":

					if not self.is_footnotes_allowed:
						raise exceptions.html.UnresolvedTagError(child.name)

					elif not child.has_attr("data-footnote"):
						raise exceptions.html.UnresolvedTagError(child.name)

				if not tag_rules.is_styling:
					raise exceptions.html.UnresolvedTagError(child.name)

		return text
