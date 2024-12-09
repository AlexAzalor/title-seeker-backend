from datetime import datetime

from pydantic import BaseModel, ConfigDict

from config import config

CFG = config()


class DirectorExportCreate(BaseModel):
    key: str
    first_name_uk: str
    last_name_uk: str
    first_name_en: str
    last_name_en: str
    born: datetime
    died: datetime | None = None
    born_in_uk: str
    born_in_en: str
    avatar: str | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class DirectorsJSONFile(BaseModel):
    directors: list[DirectorExportCreate]

    model_config = ConfigDict(
        from_attributes=True,
    )


class DirectorOut(BaseModel):
    key: str
    full_name: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class DirectorListOut(BaseModel):
    directors: list[DirectorOut]

    model_config = ConfigDict(
        from_attributes=True,
    )
