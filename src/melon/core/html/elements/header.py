from typing import Literal, override

from ..base_elements import AlignableElement, TextElement

class Header(AlignableElement, TextElement):
	"""Header."""

	def __init__(self, text: str, level: Literal[3, 4, 5, 6]):
		"""
		Header.

		Args:
			text (str): Header text.
			level (Literal[3, 4, 5, 6]): Header level.
		"""

		self._level: Literal[3, 4, 5, 6] = level

		super().__init__(text)

	@property
	def level(self) -> Literal[3, 4, 5, 6]:
		"""Header level."""

		return self._level

	@override
	def _export_element_tag(self) -> str:
		"""
		Export element main tag name.

		Returns:
			str: Element main tag name.
		"""

		return f"h{self._level}"

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
