import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re


async def main():
    async def get_content(url):
        if '.' not in url:
            url = re.findall('.*(?=/)', search_url)[0] + url
        try:
            print(f'trying {url} ...')
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers={'User-Agent': 'Mozilla/5.0'}) as response:
                    print(response.status)
                    url_content = ''
                    if response.status == 200:
                        url_content = str(await response.read())
            return url_content
        except (TypeError, aiohttp.client_exceptions.InvalidURL, aiohttp.client_exceptions.ClientConnectorError):
            print(f"{url} didn't work")
            return ''

    async def task(work_queue):
        async with aiohttp.ClientSession() as session:
            while not work_queue.empty():
                url = await work_queue.get()
                page_search = page_searches[url]
                async with session.get(url, headers={'User-Agent': 'Mozilla/5.0'}) as response:
                    content = await response.read()
                    soup = BeautifulSoup(str(content), "html.parser")
                    postings = {}
                    for posting in soup.find_all("a"):
                        if posting.get('href'):
                            posting_content = await get_content(posting.get('href'))
                            posting_soup = BeautifulSoup(posting_content, 'html.parser')
                            posting_sentences = re.findall("([^\.!?\'\"&:=|%]{20,})", str(posting_soup.find_all(text=True)))
                            posting_text = ' '.join(posting_sentences).lower()
                            if len(posting_sentences) > 10:
                                for career_term in ('responsibilities', 'full-time', 'salary', 'posting', 'equal opportunity', 'full time', 'part-time', 'part time'):
                                    if career_term in posting_text:
                                        postings.update({posting:posting_text})
                                        break
                    for search in page_search:
                        search_id = search[0]
                        keywords = search[1].lower()
                        matched_postings = {posting.get('href'): posting.get_text() for posting in postings if keywords in postings[posting].lower()}
                        if matched_postings:
                            print(f"WOOH OOOO: {matched_postings}")
                            results.append([search_id, matched_postings])

    results = []
    page_searches = {
        "https://www.shopify.ca/careers/search?keywords=&sort=specialty_asc":[['1','Marketing']],
        "https://jobs.lever.co/close.io/":[['2','Marketing']],
        "https://lixar.com/careers/":[['3','Marketing']],
        "https://journey.buffer.com/#vacancies":[['4','Marketing']],
        "https://www.shopify.ca/careers/search":[['5','Marketing']],
        "https://www.klipfolio.com/careers":[['6','front-end']],
    }
    work_queue = asyncio.Queue()
    for search_url in page_searches:
        await work_queue.put(search_url)
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
    import pdb; pdb.set_trace()
    print(results)

if __name__ == "__main__":
    asyncio.run(main())