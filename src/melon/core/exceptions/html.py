from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from ..base.structs.image import ImageData
	from ..html.base_elements import BaseElement

class CompositingError(Exception):
	"""Exception: compositing error."""

	def __init__(self, message: str):
		"""
		Exception: compositing error.

		:param message: Error message.
		:type message: str
		"""

		super().__init__(message)

class UnresolvedElementError(Exception):
	"""Exception: unresolved element."""

	def __init__(self, element: "type[BaseElement | ImageData] | BaseElement | ImageData"):
		"""
		Exception: unresolved element.

		:param element: Element.
		:type element: type[BaseElement | ImageData] | BaseElement | ImageData
		"""

		if not isinstance(element, type):
			element = type(element)

		super().__init__(element)

class UnresolvedTagError(Exception):
	"""Exception: unresolved tag."""

	def __init__(self, tag: str):
		"""
		Exception: unresolved tag.

		:param tag: Tag name.
		:type tag: str
		"""

		super().__init__(tag)
