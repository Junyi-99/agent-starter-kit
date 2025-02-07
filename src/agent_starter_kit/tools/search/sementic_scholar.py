from .base import Author, PaperSearchResult, SearchEngine

class SemanticScholarSearchEngine(SearchEngine):
    def __init__(self):
        super().__init__()
    
    async def search(self, query: str, year_from: int | None = None, year_to: int | None = None, offset: int | None = None, limit: int | None = None) -> list[PaperSearchResult]:
        raise NotImplementedError
        #TODO: Implement this method
