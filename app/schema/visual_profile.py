from pydantic import BaseModel, ConfigDict

from config import config

CFG = config()


class VisualProfileExportCreate(BaseModel):
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


class VisualProfileField(BaseModel):
    key: str
    name_en: str
    name_uk: str
    description_en: str
    description_uk: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class VisualProfileFieldWithUUID(VisualProfileField):
    uuid: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class VPCriterionJSONFile(BaseModel):
    criteria: list[VisualProfileField]

    model_config = ConfigDict(
        from_attributes=True,
    )


class VPRatingExportCreate(BaseModel):
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


class VPCriterionRatingExportCreate(BaseModel):
    title_visual_profile_id: int
    criterion_id: int
    rating: int
    order: int

    model_config = ConfigDict(
        from_attributes=True,
    )


class VPCriterionRatingJSONFile(BaseModel):
    ratings: list[VPCriterionRatingExportCreate]

    model_config = ConfigDict(
        from_attributes=True,
    )


class VisualProfileCriterionData(BaseModel):
    key: str
    name: str
    description: str
    rating: int

    model_config = ConfigDict(
        from_attributes=True,
    )


class VisualProfileIn(BaseModel):
    movie_key: str
    category_key: str
    criteria: list[VisualProfileCriterionData]

    model_config = ConfigDict(
        from_attributes=True,
    )


class VisualProfileCategoryOut(BaseModel):
    key: str
    name: str
    description: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class VisualProfileData(BaseModel):
    key: str
    name: str
    description: str
    criteria: list[VisualProfileCriterionData]

    model_config = ConfigDict(
        from_attributes=True,
    )


class VisualProfileListOut(BaseModel):
    items: list[VisualProfileData]


class VisualProfileFormIn(VisualProfileField):
    criteria: list[VisualProfileField]

    model_config = ConfigDict(
        from_attributes=True,
    )


class VisualProfileForm(VisualProfileFieldWithUUID):
    criteria: list[VisualProfileFieldWithUUID]

    model_config = ConfigDict(
        from_attributes=True,
    )


class VisualProfileItemUpdateIn(VisualProfileFieldWithUUID):
    old_key: str


class VisualProfileFormOut(BaseModel):
    impact: VisualProfileFieldWithUUID
    categories: list[VisualProfileForm]

    model_config = ConfigDict(
        from_attributes=True,
    )
