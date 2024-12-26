from pydantic import BaseModel, ConfigDict

from config import config

CFG = config()


class SubgenreExportCreate(BaseModel):
    id: int
    key: str
    name_uk: str
    name_en: str
    description_uk: str | None = None
    description_en: str | None = None
    parent_genre_id: int | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class SubgenresJSONFile(BaseModel):
    subgenres: list[SubgenreExportCreate]

    model_config = ConfigDict(
        from_attributes=True,
    )
