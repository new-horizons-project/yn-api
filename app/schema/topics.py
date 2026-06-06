from datetime import datetime
from typing import Optional, Literal, Annotated, Union
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from ..db.enums import ParseMode


class BaseTextModel(BaseModel):
	textId : int


class Header(BaseTextModel):
	type: Literal["header"]
	headerSize: Literal[1, 2, 3]


class TextWithHeader(Header):
	type: Literal["textWithHeader"]
	headerTextId: int
	underlined: bool


class Image(BaseTextModel):
	type: Literal["image"]
	imageId: int


class TextWithImage(TextWithHeader, Image):
	type: Literal["textWithImage"]
	imagePlace: Literal["left", "right"]


class Separator(BaseModel):
	type: Literal["separator"]
	model_config = ConfigDict(extra="forbid")
	pass


TextBlock = Annotated[
	Union[Header, TextWithHeader, Image, TextWithImage, Separator],
	Field(discriminator="type")
]


class BaseSettings(BaseModel):
	dim: float
	blur: float
	align: Literal["left", "center", "right"]


class RootSchema(BaseModel):
	base: BaseSettings
	textBlocks: list[TextBlock]