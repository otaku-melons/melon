from typing import TYPE_CHECKING, override

from ..base_elements import AlignableElement

if TYPE_CHECKING:
	from .header import Header
	from .paragraph import Paragraph

class Blockquote(AlignableElement):
	"""Blockquote."""

	#==========================================================================================#
	# >>>>> PROPERTIES <<<<< #
	#==========================================================================================#

	@property
	def elements(self) -> tuple["Header | Paragraph", ...]:
		"""Blockquote elements."""

		return tuple(self._elements)

	#==========================================================================================#
	# >>>>> OVERRIDDEN METHODS <<<<< #
	#==========================================================================================#

	@override
	def _export_element_tag(self) -> str:
		"""
		Export element main tag name.

		Returns:
			str: Element main tag name.
		"""

		return "blockquote"

	@override
	def _post_init(self):
		"""Execute after instance initialization."""

		super()._post_init()

		self._elements: list[Header | Paragraph] = []

	@override
	def _to_html(self) -> str:
		"""
		Convert element to HTML representation.

		Returns:
			str: HTML representation of element.
		"""

		if not self._elements:
			return ""

		content: str = "".join(element.to_html() for element in self._elements)
		align: str = f" style=\"text-align: {self._align.value}\"" if self._align else ""

		return f"<{self.element_tag}{align}>{content}</{self.element_tag}>"

	#==========================================================================================#
	# >>>>> PUBLIC METHODS <<<<< #
	#==========================================================================================#

	def append_element(self, element: "Header | Paragraph"):
		"""
		Append element.

		Args:
			element (Header | Paragraph): New element.
		"""

		self._elements.append(element)

	def clear(self):
		"""Remove all elements."""

		self._elements.clear()
