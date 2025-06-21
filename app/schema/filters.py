from enum import Enum
from pydantic import BaseModel

from config import config

CFG = config()


class FilterEnum(Enum):
    GENRE = "genre"
    SUBGENRE = "subgenre"
    SPECIFICATION = "specification"
    KEYWORD = "keyword"
    ACTION_TIME = "action_time"
    ACTOR = "actor"
    DIRECTOR = "director"
    CHARACTER = "character"
    VISUAL_PROFILE = "visual_profile"
    SHARED_UNIVERSE = "shared_universe"


class FilterFields(BaseModel):
    key: str
    name_uk: str
    name_en: str
    description_uk: str
    description_en: str


class FilterFieldsWithUUID(FilterFields):
    uuid: str


class FilterFieldList(BaseModel):
    items: list[FilterFieldsWithUUID]


class FilterJSONFile(BaseModel):
    items: list[FilterFields]


class FilterItemOut(BaseModel):
    key: str
    name: str
    description: str
    percentage_match: float


class FilterList(BaseModel):
    items: list[FilterItemOut]


class FilterItemField(BaseModel):
    key: str
    name: str
    percentage_match: float


class FilterFormIn(BaseModel):
    movie_key: str
    items: list[FilterItemField]


class FilterItem(BaseModel):
    key: str
    name: str
    description: str
    percentage_match: float


class MovieFilterItem(FilterItem):
    # Equivalent to TypeScript subgenre_parent_key?: string;
    subgenre_parent_key: str = ""


class MovieFilterFormIn(BaseModel):
    """Form for creating a new movie attribute for specification, keyword, action time"""

    key: str
    name_uk: str
    name_en: str
    description_uk: str | None = None
    description_en: str | None = None
