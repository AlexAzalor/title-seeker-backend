from pydantic import BaseModel, ConfigDict

from config import config

CFG = config()


class ActionTimeExportCreate(BaseModel):
    key: str
    name_uk: str
    name_en: str
    description_uk: str | None = None
    description_en: str | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class ActionTimesJSONFile(BaseModel):
    action_times: list[ActionTimeExportCreate]

    model_config = ConfigDict(
        from_attributes=True,
    )


class ActionTimeOut(BaseModel):
    key: str
    name: str
    description: str | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )
