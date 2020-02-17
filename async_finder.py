import asyncio
import aiohttp
from bs4 import BeautifulSoup


async def main():
    async def get_content(url):
        try:
            print(f'trying {url}...')
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers={'User-Agent': 'Mozilla/5.0'}) as response:
                    url_content = str(await response.read())
            return url_content
        except (TypeError, aiohttp.client_exceptions.InvalidURL):
            return ''

    async def task(work_queue):
        async with aiohttp.ClientSession() as session:
            while not work_queue.empty():
                url = await work_queue.get()
                page_search = page_searches[url]
                async with session.get(url, headers={'User-Agent': 'Mozilla/5.0'}) as response:
                    content = await response.read()
                    soup = BeautifulSoup(str(content), "html.parser")
                    postings = {posting:await get_content(posting.get('href')) for posting in soup.find_all("a")}
                    for search in page_search:
                        search_id = search[0]
                        keywords = search[1]
                        good_posting_links = {posting.get('href'): posting.get_text() for posting in postings if keywords in postings[posting].lower()}
                        if good_posting_links:
                            print(f"WOOH OOOO: {good_posting_links}")
                            results.append([search_id, good_posting_links])

    results = []
    page_searches = {
        "http://google.com":[['1','the'], ['7','a']],
        "http://linkedin.com":[['2','bla'], ['8','block']],
        "http://apple.com":[['3','blab'], ['9','blab']],
        "http://microsoft.com":[['4','thought'], ['10','thought']],
        "http://facebook.com":[['5','face'], ['11','face']],
        "http://twitter.com":[['6','hit'], ['12','log']],
    }
    work_queue = asyncio.Queue()
    for url in page_searches:
        await work_queue.put(url)
    await asyncio.gather(
        asyncio.create_task(task(work_queue)),
        asyncio.create_task(task(work_queue)),
        asyncio.create_task(task(work_queue)),
        asyncio.create_task(task(work_queue)),
        asyncio.create_task(task(work_queue)),
        asyncio.create_task(task(work_queue)),
    )
    print(results)

if __name__ == "__main__":
    asyncio.run(main())