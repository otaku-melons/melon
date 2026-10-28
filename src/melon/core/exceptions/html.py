class CompositingError(Exception):
	"""Exception: compositing error."""

	def __init__(self, message: str):
		"""
		Exception: compositing error.

		:param message: Error message.
		:type message: str
		"""

		super().__init__(message)


class UnresolvedTagError(Exception):
	"""Exception: unresolved tag."""

	def __init__(self, tag: str):
		"""
		Exception: unresolved tag.

		:param tag: Tag name.
		:type tag: str
		"""

		super().__init__(tag)
