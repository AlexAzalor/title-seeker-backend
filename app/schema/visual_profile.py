from pydantic import BaseModel

from config import config

CFG = config()


class VisualProfileExportCreate(BaseModel):
    key: str
    criteria_ids: list[int]
    name_en: str
    name_uk: str
    description_en: str
    description_uk: str


class VisualProfileJSONFile(BaseModel):
    visual_profiles: list[VisualProfileExportCreate]


class VisualProfileField(BaseModel):
    key: str
    name_en: str
    name_uk: str
    description_en: str
    description_uk: str


class VisualProfileFieldWithUUID(VisualProfileField):
    uuid: str


class VPCriterionJSONFile(BaseModel):
    criteria: list[VisualProfileField]


class VPRatingExportCreate(BaseModel):
    movie_id: int
    user_id: int
    category_id: int


class VPRatingJSONFile(BaseModel):
    ratings: list[VPRatingExportCreate]


class VPCriterionRatingExportCreate(BaseModel):
    title_visual_profile_id: int
    criterion_id: int
    rating: int
    order: int


class VPCriterionRatingJSONFile(BaseModel):
    ratings: list[VPCriterionRatingExportCreate]


class VisualProfileCriterionData(BaseModel):
    key: str
    name: str
    description: str
    rating: int


class VisualProfileIn(BaseModel):
    movie_key: str
    category_key: str
    criteria: list[VisualProfileCriterionData]


class VisualProfileCategoryOut(BaseModel):
    key: str
    name: str
    description: str


class VisualProfileData(BaseModel):
    key: str
    name: str
    description: str
    criteria: list[VisualProfileCriterionData]


class VisualProfileListOut(BaseModel):
    items: list[VisualProfileData]


class VisualProfileFormIn(VisualProfileField):
    criteria: list[VisualProfileField]


class VisualProfileForm(VisualProfileFieldWithUUID):
    criteria: list[VisualProfileFieldWithUUID]


class VisualProfileItemUpdateIn(VisualProfileFieldWithUUID):
    old_key: str


class VisualProfileFormOut(BaseModel):
    impact: VisualProfileFieldWithUUID
    categories: list[VisualProfileForm]
