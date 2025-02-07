import asyncio

from rich import print

import agent_starter_kit
from agent_starter_kit.tools.search import (GoogleScholarSearchEngine,
                                            PaperSearchResult)


def print_results(results: list[PaperSearchResult]):
    for result in results:
        print(f"Title=\"{result.title}\"")
        print(f"    Authors={', '.join([author.full_name for author in result.authors])}")
        print(f"    Year={result.year}")
        print(f"    CitedBy={result.citation_count}")
        print(f"    Venue={result.venue_name} ({result.venue_url})")
        print(f"    OpenAccess={result.is_open_access}")
        print(f"    Abstract={result.abstract}")
        print("")


async def main():
    se = GoogleScholarSearchEngine()

    results = await se.search(
        query="Dense Graph Convolutional With Joint Cross-Attention Network for Multimodal Emotion Recognition"
    )
    print_results(results)

    agent_starter_kit.main()


asyncio.get_event_loop().run_until_complete(main())
