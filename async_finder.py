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
                    print(f"???{len(postings)}")
                    for search in page_search:
                        print(f"searching for: {search}")
                        search_id = search[0]
                        keywords = search[1]
                        good_posting_links = {posting.get('href'): posting.get_text() for posting in postings if keywords in postings[posting].lower()}
                        if good_posting_links:
                            print(f"WOOH OOOO: {good_posting_links}")
                            results.append([search_id, good_posting_links])

    results = []
    page_searches = {
        "https://www.shopify.ca/careers/search?keywords=&sort=specialty_asc":[['1','the'], ['7','a']],
        "https://jobs.lever.co/close.io/":[['2','bla'], ['8','block']],
        "https://lixar.com/careers/":[['3','blab'], ['9','blab']],
        "https://journey.buffer.com/#vacancies":[['4','thought'], ['10','thought']],
        "https://www.shopify.ca/careers/search":[['5','face'], ['11','face']],
        "https://www.klipfolio.com/careers":[['6','hit'], ['12','log']],
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
        asyncio.create_task(task(work_queue)),
        asyncio.create_task(task(work_queue)),
        asyncio.create_task(task(work_queue)),
        asyncio.create_task(task(work_queue)),
        asyncio.create_task(task(work_queue)),
        asyncio.create_task(task(work_queue)),
        asyncio.create_task(task(work_queue)),
        asyncio.create_task(task(work_queue)),
        asyncio.create_task(task(work_queue)),
        asyncio.create_task(task(work_queue)),
        asyncio.create_task(task(work_queue)),
        asyncio.create_task(task(work_queue)),
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