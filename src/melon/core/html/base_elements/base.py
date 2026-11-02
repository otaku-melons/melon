from abc import ABC, ABCMeta, abstractmethod

from bs4 import BeautifulSoup

class _PostInitMeta(ABCMeta):
	"""Metaclass to run `_post_init()` after `__init__()`."""

	def __call__(cls, *args, **kwargs):
		"""Create instance and run `_post_init()` method."""

		instance = super().__call__(*args, **kwargs)
		instance._post_init()

		return instance

class BaseElement(ABC, metaclass = _PostInitMeta):
	"""Base chapter element."""

	#==========================================================================================#
	# >>>>> PROPERTIES <<<<< #
	#==========================================================================================#

	@property
	def element_tag(self) -> str:
		"""Element tag name."""

		return self._export_element_tag()

	#==========================================================================================#
	# >>>>> PROTECTED METHODS <<<<< #
	#==========================================================================================#

	def _parse(self, text: BeautifulSoup | str, parser: str = "html.parser") -> BeautifulSoup:
		"""
		Parse text with `BeautifulSoup`.

		Args:
			text (BeautifulSoup | str): Text to parsing or parsed object. If object parser is not function parser will be reparsed.
			parser (str, optional): Parser type.

		Returns:
			BeautifulSoup: Parsed text.
		"""

		if isinstance(text, BeautifulSoup):
			if text.builder.NAME == parser:
				return text
			else:
				text = str(text)

		return BeautifulSoup(text, parser)

	#==========================================================================================#
	# >>>>> OVERRIDABLE METHODS <<<<< #
	#==========================================================================================#

	@abstractmethod
	def _export_element_tag(self) -> str:
		"""
		Export element main tag name.

		Returns:
			str: Element main tag name.
		"""

		return ""

	def _post_init(self):
		"""Execute after instance initialization."""

		pass

	@abstractmethod
	def _to_html(self) -> str:
		"""
		Convert element to HTML representation.

		Returns:
			str: HTML representation of element.
		"""

		pass

	#==========================================================================================#
	# >>>>> PUBLIC METHODS <<<<< #
	#==========================================================================================#

	def to_html(self) -> str:
		"""
		Convert element to HTML representation.

		Returns:
			str: HTML representation of element.
		"""

		return self._to_html()
