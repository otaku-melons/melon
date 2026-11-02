from typing import override

from ..base_elements import AlignableElement, TextElement

class Paragraph(AlignableElement, TextElement):
	"""Paragraph."""

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

		return "p"

	@override
	def _to_html(self) -> str:
		"""
		Convert element to HTML representation.

		Returns:
			str: HTML representation of element.
		"""

		if not self._text:
			return ""

		soup = self._parse("")
		tag = soup.new_tag(self.element_tag)
		inner = self._parse(self._text)

		if self._align:
			tag["style"] = f"text-align: {self._align.value}"

		tag.append(inner)
		soup.append(tag)

		return str(soup)
