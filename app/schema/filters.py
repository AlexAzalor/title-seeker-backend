from pydantic import BaseModel, ConfigDict

from config import config

CFG = config()


class SpecificationExportCreate(BaseModel):
    id: int
    key: str
    name_uk: str
    name_en: str
    description_uk: str | None = None
    description_en: str | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class SpecificationsJSONFile(BaseModel):
    specifications: list[SpecificationExportCreate]

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
    parent_genre: FilterItem | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )
