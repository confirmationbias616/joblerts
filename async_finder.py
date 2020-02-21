import asyncio
import aiohttp
from bs4 import BeautifulSoup
from bs4.element import Comment
import re
from utils import create_connection
import datetime
from sender import send_email

def get_valid_link(base_url, posting_url):
    if '.' not in posting_url:
        matching_url_location = [posting_param for posting_param in posting_url.split('/') if posting_param in base_url.split('/') and posting_param]
        if matching_url_location:
            url = base_url.split(matching_url_location[0])[0].rstrip('/') + '/' + posting_url.lstrip('/')
        else:
            url = re.findall('.*(?=/)', base_url)[0] + posting_url
    else:
        url = posting_url
    return url

async def main():
    async def get_content(url):
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

    async def find_postings(work_queue):
        def tag_visible(element):
            if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
                return False
            if isinstance(element, Comment):
                return False
            return True
        async with aiohttp.ClientSession() as session:
            while not work_queue.empty():
                search_id = await work_queue.get()
                with create_connection() as conn:
                    page_search = conn.cursor().execute("""
                        SELECT career_page FROM search
                        WHERE id = ?
                    """, [search_id]).fetchone()[0]
                # parent_url = re.findall('.*/(?=.*)', page_search.rstrip('/'))[0]
                # async with session.get(parent_url, headers={'User-Agent': 'Mozilla/5.0'}) as response:
                #     parent_content = await response.read()
                # soup = BeautifulSoup(str(parent_content), "html.parser")
                # irrelevant_links = [a.get('href') for a in soup.find_all('a')]
                async with session.get(page_search, headers={'User-Agent': 'Mozilla/5.0'}) as response:
                    content = await response.read()
                    soup = BeautifulSoup(str(content), "html.parser")
                    new_stale_links = ' '.join([a.get('href') for a in soup.find_all("a") if a.get('href')])
                    with create_connection() as conn:
                        stale_links = conn.cursor().execute("""
                            SELECT stale_links FROM search
                            WHERE id = ?
                        """, [search_id]).fetchone()[0]
                    if not stale_links or (set(new_stale_links.split(' ')) != set(stale_links.split(' '))):
                        with create_connection() as conn:
                            conn.cursor().execute("""
                                UPDATE search SET stale_links = ?
                                WHERE id = ?
                            """, [new_stale_links, search_id])
                    postings = {}
                    for posting in filter(tag_visible, soup.find_all("a", text=True)):
                        if posting.get('href'):
                            if stale_links and posting.get('href') in stale_links:
                                continue
                            # if posting.get('href') in irrelevant_links:
                            #     continue
                            posting_content = await get_content(get_valid_link(page_search, posting.get('href')))
                            if not posting_content:
                                continue
                            posting_soup = BeautifulSoup(posting_content, 'html.parser')
                            postings.update({posting:posting_soup})
                    with create_connection() as conn:
                        keywords = conn.cursor().execute("""
                            SELECT keywords FROM search
                            WHERE id = ?
                        """, [search_id]).fetchone()[0].lower()
                    matched_postings = {}
                    for posting in postings:
                        print(f"Maybe {posting.get_text()}?")
                        texts = postings[posting].find_all(text=True)
                        visible_texts = filter(tag_visible, texts)
                        posting_text = " ".join(t.strip() for t in visible_texts)
                        if not keywords in posting_text.lower():
                            print(f"Nope, didn't contain keyword {keywords}")
                            continue
                        posting_sentences = re.findall("([A-Z][^.]{60,}[\.!?])", posting_text)
                        if len(posting_sentences) <= 10:
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
    
    with create_connection() as conn:
        search_ids = conn.cursor().execute("""
            SELECT id FROM search
        """).fetchall()
        search_ids = [x[0] for x in search_ids]
    
    results = []
    
    work_queue = asyncio.Queue()
    for search_id in search_ids:
        await work_queue.put(search_id)
    await asyncio.gather(
        asyncio.create_task(find_postings(work_queue)),
        asyncio.create_task(find_postings(work_queue)),
        asyncio.create_task(find_postings(work_queue)),
        asyncio.create_task(find_postings(work_queue)),
        asyncio.create_task(find_postings(work_queue)),
        asyncio.create_task(find_postings(work_queue)),
        asyncio.create_task(find_postings(work_queue)),
        asyncio.create_task(find_postings(work_queue)),
        asyncio.create_task(find_postings(work_queue)),
        asyncio.create_task(find_postings(work_queue)),
        asyncio.create_task(find_postings(work_queue)),
        asyncio.create_task(find_postings(work_queue)),
        asyncio.create_task(find_postings(work_queue)),
        asyncio.create_task(find_postings(work_queue)),
        asyncio.create_task(find_postings(work_queue)),
        asyncio.create_task(find_postings(work_queue)),
        asyncio.create_task(find_postings(work_queue)),
        asyncio.create_task(find_postings(work_queue)),
        asyncio.create_task(find_postings(work_queue)),
        asyncio.create_task(find_postings(work_queue)),
        asyncio.create_task(find_postings(work_queue)),
        asyncio.create_task(find_postings(work_queue)),
        asyncio.create_task(find_postings(work_queue)),
        asyncio.create_task(find_postings(work_queue)),
    )

    for result in results:
        search_id = result[0]
        for posting in result[1]:
            print(f"{result[1][posting]}: {posting}")
            send_email(search_id)
            with create_connection() as conn:
                conn.cursor().execute("""
                    INSERT INTO found (search_id, link, title, date_found) VALUES (?, ?, ?, ?)
                """, [search_id, posting, result[1][posting], datetime.datetime.now().date()])


if __name__ == "__main__":
    asyncio.run(main())