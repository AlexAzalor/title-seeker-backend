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


class CriterionRatingIn(BaseModel):
    key: str
    rating: int
    name: str
    description: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class TitleVisualProfileIn(BaseModel):
    movie_key: str
    category_key: str
    criteria: list[CriterionRatingIn]

    model_config = ConfigDict(
        from_attributes=True,
    )


class CategoryCriterionData(BaseModel):
    key: str
    name: str
    description: str
    rating: int

    model_config = ConfigDict(
        from_attributes=True,
    )


class TitleCategoryData(BaseModel):
    key: str
    name: str
    description: str
    criteria: list[CategoryCriterionData]

    model_config = ConfigDict(
        from_attributes=True,
    )


class VisualProfileListOut(BaseModel):
    items: list[TitleCategoryData]


class CategoryFormIn(BaseModel):
    key: str
    name_uk: str
    name_en: str
    description_uk: str
    description_en: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class CategoryFormOut(BaseModel):
    key: str
    name: str
    description: str

    model_config = ConfigDict(
        from_attributes=True,
    )
