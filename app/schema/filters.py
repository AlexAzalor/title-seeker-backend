from enum import Enum
from pydantic import BaseModel, ConfigDict

from config import config

CFG = config()


class FilterEnum(Enum):
    GENRE = "genre"
    SUBGENRE = "subgenre"
    SPECIFICATION = "specification"
    KEYWORD = "keyword"
    ACTION_TIME = "action_time"


class FilterFields(BaseModel):
    key: str
    name_uk: str
    name_en: str
    description_uk: str
    description_en: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class FilterFieldsWithUUID(FilterFields):
    uuid: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class FilterFieldList(BaseModel):
    items: list[FilterFieldsWithUUID]

    model_config = ConfigDict(
        from_attributes=True,
    )


class SpecificationsJSONFile(BaseModel):
    specifications: list[FilterFields]

    model_config = ConfigDict(
        from_attributes=True,
    )


class KeywordExportCreate(BaseModel):
    id: int
    key: str
    name_uk: str
    name_en: str
    description_uk: str | None = None
    description_en: str | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class KeywordsJSONFile(BaseModel):
    keywords: list[KeywordExportCreate]

    model_config = ConfigDict(
        from_attributes=True,
    )


class ActionTimeExportCreate(BaseModel):
    id: int
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


class FilterItemOut(BaseModel):
    key: str
    name: str
    description: str
    percentage_match: float

    model_config = ConfigDict(
        from_attributes=True,
    )


class FilterList(BaseModel):
    items: list[FilterItemOut]

    model_config = ConfigDict(
        from_attributes=True,
    )


class FilterItemField(BaseModel):
    key: str
    name: str
    percentage_match: float

    model_config = ConfigDict(
        from_attributes=True,
    )


class FilterFormIn(BaseModel):
    movie_key: str
    items: list[FilterItemField]

    model_config = ConfigDict(
        from_attributes=True,
    )


class FilterItem(BaseModel):
    key: str
    name: str
    description: str
    percentage_match: float

    model_config = ConfigDict(
        from_attributes=True,
    )


class MovieFilterItem(FilterItem):
    # Equivalent to TypeScript subgenre_parent_key?: string;
    subgenre_parent_key: str = ""

    model_config = ConfigDict(
        from_attributes=True,
    )
