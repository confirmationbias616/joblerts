import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re


async def main(page_searches):
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
                search_url = await work_queue.get()
                page_search = page_searches[search_url]
                parent_url = re.findall('.*/(?=.*)', search_url.rstrip('/'))[0]
                async with session.get(parent_url, headers={'User-Agent': 'Mozilla/5.0'}) as response:
                    parent_content = await response.read()
                soup = BeautifulSoup(str(parent_content), "html.parser")
                irrelevant_links = [a.get('href') for a in soup.find_all('a')]
                async with session.get(search_url, headers={'User-Agent': 'Mozilla/5.0'}) as response:
                    content = await response.read()
                    soup = BeautifulSoup(str(content), "html.parser")
                    postings = {}
                    for posting in soup.find_all("a"):
                        if posting.get('href'):
                            if posting.get('href') in irrelevant_links:
                                continue
                            posting_content = await get_content(posting.get('href'))
                            if not posting_content:
                                continue
                            posting_soup = BeautifulSoup(posting_content, 'html.parser')
                            postings.update({posting:posting_soup})
                    for search in page_search:
                        search_id = search[0]
                        keywords = search[1].lower()
                        matched_postings = {}
                        for posting in postings:
                            print(f"Maybe {posting.get_text()}?")
                            posting_text = ' '.join(postings[posting].find_all(text=True))
                            if not keywords in posting_text.lower():
                                print(f"Nope, didn't contain keyword {keywords}")
                                continue
                            posting_sentences = re.findall("([A-Z][^\.!?\'\"&:=|%{}]{60,}[\.!?])", posting_text)
                            if len(posting_sentences) <= 13:
                                print(f"Nope, didn't contain enough sentences ({len(posting_sentences)})")
                                print(posting)
                                continue
                            for career_term in ('responsibilities', 'full-time', 'salary', 'posting', 'equal opportunity', 'full time', 'part-time', 'part time'):
                                if career_term in posting_text.lower():
                                    matched_postings.update({posting.get('href'): posting.get_text()})
                                    print(f"Yes, it's a match for {posting.get_text()}! -> contains {len(posting_sentences)} sentences and career term `{career_term}`")
                                    break
                            else:
                                print(f"Nope, didn't contain a career term")
                        if matched_postings:
                            print(f"WOOH OOOO: {matched_postings}")
                            results.append([search_id, matched_postings])

    results = []
    # page_searches = {
    #     "https://www.shopify.ca/careers/search?keywords=&sort=specialty_asc":[['1','Marketing']],
    #     "https://jobs.lever.co/close.io/":[['2','Marketing']],
    #     "https://lixar.com/careers/":[['3','Marketing']],
    #     "https://journey.buffer.com/#vacancies":[['4','Marketing']],
    #     "https://www.shopify.ca/careers/search":[['5','Marketing']],
    #     "https://www.klipfolio.com/careers":[['6','front-end']],
    # }
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
    for result in results:
        for posting in result[1]:
            print(f"{result[1][posting]}: {posting}")
    return results

if __name__ == "__main__":
    asyncio.run(main())