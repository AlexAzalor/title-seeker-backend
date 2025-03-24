from pydantic import BaseModel, ConfigDict

from config import config

CFG = config()


class SharedUniverseExportCreate(BaseModel):
    id: int
    key: str
    name_uk: str
    name_en: str
    description_uk: str | None = None
    description_en: str | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class SharedUniversesJSONFile(BaseModel):
    shared_universes: list[SharedUniverseExportCreate]

    model_config = ConfigDict(
        from_attributes=True,
    )


class SharedUniversePreCreateOut(BaseModel):
    key: str
    name: str
    description: str

    model_config = ConfigDict(
        from_attributes=True,
    )
