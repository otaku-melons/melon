from typing import TYPE_CHECKING

from bs4 import Tag

from ...exceptions.html import UnresolvedTagError
from ..allowed_tags import ALLOWED_TAGS
from ..enums import TagCategory
from .base import BaseElement

if TYPE_CHECKING:
	from collections.abc import Sequence

	from ..footnote import Footnote

class TextElement(BaseElement):
	"""Text element."""

	def __init__(self, text: str):
		"""
		Text element.

		Args:
			text (str): Element text.
		"""

		text = self._validate_text(text)

		self._text: str = text
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

		styling_tags_names: tuple[str, ...] = ALLOWED_TAGS.get_category_tags_names(TagCategory.Styling)

		for child in soup.find_all():

			if isinstance(child, Tag):

				if child.name == "a" and child.has_attr("data-footnote") and self.element_tag in ALLOWED_TAGS.get_category_tags_names(TagCategory.Footnotable):
					continue

				if child.name not in styling_tags_names:
					raise UnresolvedTagError(child.name)

		return text
