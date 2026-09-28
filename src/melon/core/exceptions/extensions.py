class ExtensionNotFoundError(Exception):
	"""Exception: extension not found."""

	def __init__(self, extension_name: str):
		"""
		Exception: extension not found.

		:param extension_name: Extension name.
		:type extension_name: str
		"""

		super().__init__(extension_name) 

class ExtensionAlreadyExistsError(Exception):
	"""Exception: extension already exists."""

	def __init__(self, extension_name: str):
		"""
		Exception: extension already exists.

		:param extension_name: Extension name.
		:type extension_name: str
		"""

		super().__init__(extension_name) 
