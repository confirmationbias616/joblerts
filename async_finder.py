import asyncio
import aiohttp
from bs4 import BeautifulSoup


async def main():
    async def task(work_queue):
        async with aiohttp.ClientSession() as session:
            while not work_queue.empty():
                url = await work_queue.get()
                page_search = page_searches[url]
                async with session.get(url) as response:
                    content = await response.read()
                    soup = BeautifulSoup(str(content), "html.parser")
                    for search in page_search:
                        search_id = search[0]
                        keywords = search[1]
                        posting_links = {posting.get('href'): posting.get_text() for posting in soup.find_all("a") if keywords in posting.get_text().lower()}
                        postings.append([search_id, posting_links])
    postings = []
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
    print(postings)

if __name__ == "__main__":
    asyncio.run(main())