from pydantic import BaseModel, ConfigDict

from config import config

CFG = config()


class GenreFormFields(BaseModel):
    key: str
    name_uk: str
    name_en: str
    description_uk: str
    description_en: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class GenreFormFieldsWithUUID(GenreFormFields):
    uuid: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class GenresJSONFile(BaseModel):
    genres: list[GenreFormFields]

    model_config = ConfigDict(
        from_attributes=True,
    )


class SubgenreOut(BaseModel):
    key: str
    name: str
    description: str
    parent_genre_key: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class GenreOut(BaseModel):
    key: str
    name: str
    description: str
    subgenres: list[SubgenreOut]

    model_config = ConfigDict(
        from_attributes=True,
    )


class GenreListOut(BaseModel):
    genres: list[GenreOut]

    model_config = ConfigDict(
        from_attributes=True,
    )


class GenreIn(BaseModel):
    key: str
    name_uk: str
    name_en: str
    description_uk: str | None = None
    description_en: str | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class GenreItemOut(BaseModel):
    key: str
    name: str
    description: str
    percentage_match: float
    parent_genre_key: str | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class GenresSubgenresOut(BaseModel):
    genres: list[GenreOut]

    model_config = ConfigDict(
        from_attributes=True,
    )


class GenreItemFieldEditIn(BaseModel):
    key: str
    name: str
    percentage_match: float

    model_config = ConfigDict(
        from_attributes=True,
    )


class GenreItemFieldEditFormIn(BaseModel):
    genres: list[GenreItemFieldEditIn]
    subgenres: list[GenreItemFieldEditIn]

    model_config = ConfigDict(
        from_attributes=True,
    )
