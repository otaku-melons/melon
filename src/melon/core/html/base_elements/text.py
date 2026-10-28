from bs4 import Tag

from ...exceptions.html import UnresolvedTagError
from ..allowed_tags import ALLOWED_TAGS
from ..enums import TagCategory
from .base import BaseElement

class TextElement(BaseElement):
	"""Text element."""

    #==========================================================================================#
	# >>>>> PROTECTED METHODS <<<<< #
	#==========================================================================================#

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
			if isinstance(child, Tag) and child.name not in styling_tags_names:
				raise UnresolvedTagError(child.name)

		return text

    #==========================================================================================#
	# >>>>> PUBLIC METHODS <<<<< #
	#==========================================================================================#

	def __init__(self, text: str):
		"""
		Text element.

		Args:
			text (str): Element text.
		"""

		text = self._validate_text(text)

		self._text: str = text
