import asyncio
import warnings

import requests
from bs4 import BeautifulSoup, Tag
from crawl4ai import (AsyncWebCrawler, BrowserConfig, CacheMode,
                      CrawlerRunConfig)
from crawl4ai.chunking_strategy import RegexChunking
from lxml import etree, html
from rich import print

from .base import Author, PaperSearchResult, SearchEngine


def parse_google_scholar_html(html_content: str) -> list[PaperSearchResult]:
    result = []
    soup = BeautifulSoup(html_content, 'html.parser')

    body = soup.find(id="gs_res_ccl_mid")
    if body is None or not isinstance(body, Tag):
        if "not a robot" in html_content:
            raise ValueError("Google Scholar is blocking the request")
        else:
            raise ValueError("Cannot find the body tag of the google scholar search result")
    
    # Get all children of the body
    children = body.find_all("div", recursive=False)
    # print(f"The body has {len(children)} children")

    for child in children:
        # Get the title of the paper
        tree = html.fromstring(str(child))
        title = tree.xpath("//div[@class='gs_ri']/h3/a")
        
        if len(title) > 0: # type: ignore
            title = title[0].text_content() # type: ignore
            title = " ".join(title.split()) # type: ignore
        else:
            continue

        citedby = tree.xpath("//a[starts-with(text(), 'Cited by')]")
        if len(citedby) > 0: # type: ignore
            citedby = citedby[0].text_content() # type: ignore
            citedby = citedby.split()[-1] # type: ignore
            citedby = int(citedby) # type: ignore
        else:
            citedby = 0

        
        # Determine the detailed result or general result
        detailed = False
        if len(tree.xpath("//div[@class='gs_a']")) > 0: # type: ignore
            detailed = False
        elif len(tree.xpath("//div[@class='gs_fmaa']")) > 0: # type: ignore
            detailed = True
        else:
            raise ValueError("Cannot determine the type of the result")

            
        if detailed:
            venue = tree.xpath("//div[@class='gs_a gs_fma_p']/text()")
            venue_name = venue[0] if len(venue) > 0 else None # type: ignore
            venue_url = venue[1] if len(venue) > 1 else None # type: ignore
            
            venue_name, year = venue_name.split(",") if venue_name is not None else (None, None) # type: ignore
            venue_name = " ".join(venue_name.split()) if venue_name is not None else None # type: ignore # remove the \xa0 in the string
            year = int(year) if year is not None else None
            
            authors = tree.xpath("//div[@class='gs_fmaa']")
            if len(authors) > 0: # type: ignore
                authors_source = etree.tostring(authors[0]).decode("utf-8") # type: ignore
                
                authors = authors_source.split(",") # split the html string by comma
                
                for author in authors:
                    author_html = html.fromstring(author) # type: ignore
                    author_name = author_html.xpath("//text()")[0] # type: ignore
                    author_id = author_html.xpath("//a/@href")[0] # type: ignore
                    if author_id is not None:
                        author_id = author_id.split("user=")[1] # type: ignore
                        author_id = author_id.split("&")[0] # type: ignore
                    
                    authors = [
                        Author(
                            full_name= author_name,
                            google_scholar_id=author_id
                    )
                    for author in authors
                ]
                
                
                
                authors = authors[0].text_content() # type: ignore
                authors = " ".join(authors.split()) # type: ignore
                authors = authors.split(",") # type: ignore
                authors = [Author(full_name=author.strip()) for author in authors] # type: ignore
            else:
                authors = None # type: ignore
                
            abstract = tree.xpath("//div[@class='gs_fma_abs']/div[@class='gs_fma_snp']")
            if len(abstract) > 0: # type: ignore
                abstract = abstract[0].text_content() # type: ignore
            else:
                abstract = None # type: ignore
        else:
            authors = tree.xpath("//div[@class='gs_a']")
            print(authors[0].text_content().split('-'))
            
            temp = authors[0].text_content().split('-') if len(authors) > 0 else (None, None, None)
            if len(temp) >= 3:
                authors, venue_name, venue_url = temp[0], temp[-2], temp[-1]
            else:
                authors = authors[0].text_content() # type: ignore
                venue_name = None
                venue_url = None
                
            authors = authors.split(",") # type: ignore
            authors = [Author(full_name=author.strip()) for author in authors] # type: ignore
            venue_url = venue_url.strip() if venue_url is not None else None # type: ignore
            
            temp = venue_name.split(",") if venue_name is not None else (None, None)
            if len(temp) > 1:
                venue_name, year = temp[0], temp[-1]
            else:
                venue_name = temp[0]
                year = None
            venue_name = " ".join(venue_name.split()) if venue_name is not None else None # remove the \xa0 in the string
            year = int(year) if year is not None else None
            
            abstract = tree.xpath("//div[@class='gs_rs']")
            if len(abstract) > 0: # type: ignore
                abstract = abstract[0].text_content() # type: ignore
            else:
                abstract = None # type: ignore

        assert type(authors) is list
        assert type(year) is int if year is not None else True, f"year: {year} have type {type(year)}"
        assert type(authors[0]) is Author if authors is not None else True
        
        result.append(PaperSearchResult(
            title=title,
            authors=authors, # type: ignore
            year=year,
            abstract=abstract, # type: ignore
            citation_count=citedby,
            venue_name=venue_name,
            venue_url=venue_url, # type: ignore
        ))
    return result


def get_next_proxy():
    ret = requests.get("https://proxypool.scrape.center/random")
    
    return {
        "server": "http://" + ret.content.decode("utf-8"),
    }


class GoogleScholarSearchEngine(SearchEngine):
    """
    Find usage example in `pd-core-latex/demo_search_google_scholar.py`
    """
    def __init__(self):
        super().__init__()

    def _get_url(self, query: str, offset: int | None, year_from: int | None = None, year_to: int | None = None) -> str:
        GOOGLE_SCHOLAR_BASE = 'https://scholar.google.com/scholar'
        PARAMS = {
            'hl': 'en',                            # Language: English
            'as_sdt': '0,5',                       # Search type and scope
            'q': query,                            # Search query
            'start': offset if offset else 0,      # Start index
        }

        if year_from is not None:
            PARAMS['as_ylo'] = year_from
        if year_to is not None:
            PARAMS['as_yhi'] = year_to

        param_string = '&'.join(f'{k}={v}' for k, v in PARAMS.items())
        return f'{GOOGLE_SCHOLAR_BASE}?{param_string}'


    async def _search(self, query: str, year_from: int | None, year_to: int | None, offset: int | None, limit: int | None) -> list[PaperSearchResult]:
        browser_cfg = BrowserConfig(
            headless=True,
            user_agent_mode="random",
            cookies=[],
            use_persistent_context=True,
            browser_type="chromium"
        )
        async with AsyncWebCrawler(verbose=True, config=browser_cfg) as crawler:
            
            config = CrawlerRunConfig(
                js_code = [
                    "let buttons = document.querySelectorAll('a.gs_or_cit');",
                    "if (buttons.length > 0) {buttons[buttons.length - 1].click();}"
                ],
                proxy_config=get_next_proxy(),
            )
            
            result = await crawler.arun(
                url=self._get_url(query, offset, year_from, year_to),
                cache_mode=CacheMode.BYPASS,
                simulate_user=True,  # Causes random mouse movements and clicks
                override_navigator=True,  # Makes the browser appear more like a real user
                remove_overlay_elements=True,
                chunking_strategy=RegexChunking(patterns=["\n\n"]),
                config=config,
            )
            assert result.html.strip() != '', 'The result is empty'
            return parse_google_scholar_html(result.html)

    async def search(self, query: str, year_from: int | None = None, year_to: int | None = None, offset: int | None = None, limit: int | None = None) -> list[PaperSearchResult]:
        if limit is not None:
            warnings.warn("The limit is not supported for Google Scholar search engine", UserWarning)
        return await self._search(query, year_from, year_to, offset, limit)


async def get_search_result_googlescholar(keyword: str, page: int) -> list[PaperSearchResult]:
    assert page > 0
    search_engine = GoogleScholarSearchEngine()
    return await search_engine.search(
        query=keyword,
        offset=(page - 1) * 10
    )

async def get_all_paper(keyword: str) -> list[PaperSearchResult]:
    search_engine = GoogleScholarSearchEngine()
    return await search_engine.search(
        query=keyword
    )

async def get_all_paper_year_till_now(keyword: str, fromyear: int) -> list[PaperSearchResult]:
    search_engine = GoogleScholarSearchEngine()
    return await search_engine.search(
        query=keyword,
        year_from=fromyear
    )
