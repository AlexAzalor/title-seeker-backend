from pydantic import BaseModel, ConfigDict

from config import config

CFG = config()


class VisualProfileExportCreate(BaseModel):
    id: int
    key: str
    criteria_ids: list[int]
    name_en: str
    name_uk: str
    description_en: str
    description_uk: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class VisualProfileJSONFile(BaseModel):
    visual_profiles: list[VisualProfileExportCreate]

    model_config = ConfigDict(
        from_attributes=True,
    )


class TitleCriterionExportCreate(BaseModel):
    id: int
    # movie_id: int
    # user_id: int
    # rating:int
    key: str
    # category_id: int
    name_en: str
    name_uk: str
    description_en: str
    description_uk: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class TitleCriterionJSONFile(BaseModel):
    criteria: list[TitleCriterionExportCreate]

    model_config = ConfigDict(
        from_attributes=True,
    )


class VPRatingExportCreate(BaseModel):
    id: int
    movie_id: int
    user_id: int
    category_id: int

    model_config = ConfigDict(
        from_attributes=True,
    )


class VPRatingJSONFile(BaseModel):
    ratings: list[VPRatingExportCreate]

    model_config = ConfigDict(
        from_attributes=True,
    )


class TitleCriterionRatingExportCreate(BaseModel):
    id: int
    title_visual_profile_id: int
    criterion_id: int
    rating: int
    order: int

    model_config = ConfigDict(
        from_attributes=True,
    )


class TitleCriterionRatingJSONFile(BaseModel):
    ratings: list[TitleCriterionRatingExportCreate]

    model_config = ConfigDict(
        from_attributes=True,
    )
