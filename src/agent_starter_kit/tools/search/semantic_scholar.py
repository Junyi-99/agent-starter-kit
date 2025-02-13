import json
import os
import time

import requests
from loguru import logger
from rich import print

from .base import Author, PaperSearchResult, SearchEngine

SEMANTIC_SCHOLAR_API_KEY = os.getenv("SEMANTIC_SCHOLAR_API_KEY", None)


class SemanticScholarSearchEngine(SearchEngine):
    def __init__(self):
        super().__init__()

    async def search(
        self,
        query: str,
        year_from: int | str | None = None,
        year_to: int | str | None = None,
        offset: int | None = None,
        limit: int | None = None,
    ) -> list[PaperSearchResult]:
        if year_from is not None and year_to is None:
            year_from = f"{year_from}-"
        if year_to is not None and year_from is None:
            year_to = f"-{year_to}"

        year = f"{year_from}-{year_to}" if year_from is not None and year_to is not None else None
        result = []

        headers = (
            {
                "x-api-key": SEMANTIC_SCHOLAR_API_KEY,
            }
            if SEMANTIC_SCHOLAR_API_KEY is not None
            else {}
        )

        ret = requests.get(
            "https://api.semanticscholar.org/graph/v1/paper/search",
            params={
                "query": query,
                "year": year,
                # "fieldsOfStudy": "Computer Science",
                "limit": limit,
                "offset": offset,
                "fields": "paperId,title,authors,externalIds,year,abstract,referenceCount,citationCount,venue,publicationVenue,isOpenAccess,openAccessPdf,tldr",
            },
            headers=headers,
        )

        logger.info(ret.json())
        if "code" in ret.json():  # 429
            logger.error(ret.json())
            time.sleep(5)
            raise Exception(f"Semantic Scholar API limit reached: {ret.json()}")
        elif "message" in ret.json():
            logger.error(ret.json())
            time.sleep(5)
            raise Exception(f"Semantic Scholar API error: {ret.json()}")

        if "data" in ret.json():
            data = ret.json()["data"]
            for paper in data:
                result.append(
                    PaperSearchResult(
                        title=paper["title"],
                        authors=[
                            Author(
                                full_name=author["name"],
                                google_scholar_id=author.get("externalIds", {}).get("googleScholarId", None),
                                dblp_id=author.get("externalIds", {}).get("DBLP", None),
                                orcid_id=author.get("externalIds", {}).get("ORCID", None),
                                affiliation=str(author.get("affiliations", [])),
                                homepage=author.get("homepage", None),
                            )
                            for author in paper["authors"]
                        ],
                        year=paper["year"],
                        abstract=paper["abstract"],
                        citation_count=paper["citationCount"],
                        venue_name=json.dumps(paper["publicationVenue"]),
                        is_open_access=paper["isOpenAccess"],
                        open_access_link=json.dumps(paper["openAccessPdf"]),
                    )
                )

        # if "total" in ret.json():
        #     # this means no result
        #     return []
        return result

    def paper_citations(self, paper_id: str, limit: int = 1000, offset: int = 0) -> list[dict]:
        while True:
            ret = requests.get(
                url=f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}/citations",
                params={
                    "fields": "paperId,title,year,abstract",
                    "limit": str(limit),
                    "offset": str(offset),
                },
            )

            if "code" in ret.json():
                print(ret.json())
                time.sleep(5)
                continue
            elif "message" in ret.json():
                print(ret.json())
                time.sleep(5)
                continue

            if "data" in ret.json():
                return ret.json()["data"]

            if "total" in ret.json():
                # this means no result
                return []

            print(ret.json())
            time.sleep(5)
            continue
