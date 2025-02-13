import json
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Author:
    full_name: str
    google_scholar_id: str | None = None
    dblp_id: str | None = None
    orcid_id: str | None = None
    affiliation: str | None = None
    homepage: str | None = None

    def __str__(self):
        return self.full_name

    def to_dict(self) -> dict:
        return {
            "full_name": self.full_name,
            "google_scholar_id": self.google_scholar_id,
            "dblp_id": self.dblp_id,
            "orcid_id": self.orcid_id,
            "affiliation": self.affiliation,
            "homepage": self.homepage,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


@dataclass
class PaperSearchResult:
    title: str
    authors: list[Author]
    year: int | None = None
    abstract: str | None = None
    citation_count: int | None = None
    venue_name: str | None = None
    venue_url: str | None = None
    is_open_access: bool | None = None
    open_access_link: str | None = None  # URL to the PDF or Latex source. Only available if is_open_access is True

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "authors": [author.to_dict() for author in self.authors],
            "year": self.year,
            "abstract": self.abstract,
            "citation_count": self.citation_count,
            "venue_name": self.venue_name,
            "venue_url": self.venue_url,
            "is_open_access": self.is_open_access,
            "open_access_link": self.open_access_link,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class SearchEngine(ABC):
    def __init__(self):
        super().__init__()

    @abstractmethod
    async def search(
        self, query: str, year_from: int | None = None, year_to: int | None = None, offset: int | None = None, limit: int | None = None
    ) -> list[PaperSearchResult]:
        """
        Search for papers based on a query.

        Args:
            query: The search query.
            year_from: Limit search results to papers published after this year.
            year_to: Limit search results to papers published before this year.
            offset: Offset how many results to skip.
            limit: Maximum number of results to return.

        Returns:
            A list of PaperSearchResult objects.
        """
        pass
