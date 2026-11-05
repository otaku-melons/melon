from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from ..base.structs.image import ImageData
	from ..html.base_elements import BaseElement

class EncodingError(Exception):
	"""Exception: HTML element into line encoding error."""

	def __init__(self, message: str):
		"""
		Exception: HTML element into line encoding error.

		:param message: Error message.
		:type message: str
		"""

		super().__init__(message)

class DecodingError(Exception):
	"""Exception: HTML line into element decoding error."""

	def __init__(self, message: str):
		"""
		Exception: HTML line into element decoding error.

		:param message: Error message.
		:type message: str
		"""

		super().__init__(message)

class UnresolvedAttributeError(Exception):
	"""Exception: unresolved attribute element."""

	def __init__(self, attribute: str):
		"""
		Exception: unresolved attribute element.

		:param attribute: Attribute name.
		:type attribute: str
		"""

		super().__init__(attribute)

class UnresolvedElementError(Exception):
	"""Exception: unresolved child element."""

	def __init__(self, element: "type[BaseElement | ImageData] | BaseElement | ImageData"):
		"""
		Exception: unresolved child element.

		:param element: Element or it's type.
		:type element: type[BaseElement | ImageData] | BaseElement | ImageData
		"""

		if not isinstance(element, type):
			element = type(element)

		super().__init__(element)

class UnresolvedTagError(Exception):
	"""Exception: HTML tag has unresolved child tag."""

	def __init__(self, tag: str):
		"""
		Exception: HTML tag has unresolved child tag.

		:param tag: Child tag name.
		:type tag: str
		"""

		super().__init__(tag)
