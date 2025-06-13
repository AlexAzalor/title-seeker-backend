from pydantic import BaseModel


class BasePagination(BaseModel):
    total: int  # total items
    page: int  # current page number
    pages: int  # total pages


class Pagination(BasePagination):
    """Pagination data"""

    query: str | None  # query string
    per_page: int  # number items on the page
    skip: int  # number items on all previous pages
    pages_for_links: list[int]  # number of links
