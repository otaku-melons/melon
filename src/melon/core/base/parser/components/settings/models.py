from pathlib import Path
from typing import Annotated, Any

from pydantic import BaseModel

from dublib.validators import types

class DirectoriesModel(BaseModel):
	"""Directories model."""

	content: Annotated[Path, types.ExistingDirPath] | None = None
	images: Annotated[Path, types.ExistingDirPath] | None = None
	titles: Annotated[Path, types.ExistingDirPath] | None = None

class CommonModel(BaseModel):
	"""Common model."""

	pretty: bool = True
	use_id_as_filename: bool = False
	sizing_images: bool = True

class NetworkModel(BaseModel):
	"""Network model."""

	delay: float = 1.0
	retries: int = 1
	proxies: tuple[str, ...] = ()
	images_mirrors: dict[str, str] = {}

class TextFiltersModel(BaseModel):
	"""Text filters model."""

	regexs: tuple[str, ...] = ()
	strings: tuple[str, ...] = ()

class ImagesFiltersModel(BaseModel):
	"""Images filters model."""

	min_height: int | None = None
	max_height: int | None = None

	min_width: int | None = None
	max_width: int | None = None

	min_size: int | None = 100
	signatures: tuple[str, ...] = ()

class FiltersModel(BaseModel):
	"""Filters model."""

	text: TextFiltersModel = TextFiltersModel()
	images: ImagesFiltersModel = ImagesFiltersModel()

class SettingsModel(BaseModel):
	"""Settings model."""

	directories: DirectoriesModel = DirectoriesModel()
	common: CommonModel = CommonModel()
	network: NetworkModel = NetworkModel()
	filters: FiltersModel = FiltersModel()
	custom: dict[str, Any] = {}
