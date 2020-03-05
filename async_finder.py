import asyncio
import aiohttp
from bs4 import BeautifulSoup
from bs4.element import Comment
import re
from utils import create_connection, get_valid_link
import datetime
from sender import send_email

def process_user_search(keywords):
    keyword_list = []
    or_options = re.findall('(?=\().*(?<=\))', keywords)
    or_options = [or_option for or_option in or_options if 'OR' in or_option]
    print(or_options)
    if not or_options:
        or_options = [keywords]
    print(or_options)
    for option in or_options:
        print(option)
        for term in option.lstrip('(').rstrip(')').split('OR'):
            keyword_list.append(keywords.replace(option,term.strip(' ').lstrip('(').rstrip(')')))
    keyword_list = [re.sub(' +',' ',k).lower() for k in keyword_list]
    return keyword_list

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
                async with session.get(page_search, headers={'User-Agent': 'Mozilla/5.0'}) as response:
                    content = await response.read()
                    soup = BeautifulSoup(str(content), "html.parser")
                    new_stale_links = ' '.join([a.get('href') for a in soup.find_all("a") if a.get('href')])
                    with create_connection() as conn:
                        stale_links = conn.cursor().execute("""
                            SELECT stale_links FROM search
                            WHERE id = ?
                        """, [search_id]).fetchone()[0]
                    if not stale_links:
                        with create_connection() as conn:
                            conn.cursor().execute("""
                                UPDATE search SET stale_links = ?
                                WHERE id = ?
                            """, [new_stale_links, search_id])
                        return
                    postings = {}
                    for posting in filter(tag_visible, soup.find_all("a", text=True)):
                        if posting.get('href'):
                            if stale_links and posting.get('href') in stale_links.split(' '):
                                continue
                            posting_content = await get_content(get_valid_link(page_search, posting.get('href')))
                            if not posting_content:
                                continue
                            posting_soup = BeautifulSoup(posting_content, 'html.parser')
                            postings.update({posting:posting_soup})
                    with create_connection() as conn:
                        keywords = conn.cursor().execute("""
                            SELECT keywords FROM search
                            WHERE id = ?
                        """, [search_id]).fetchone()[0]
                    matched_postings = {}
                    for posting in postings:
                        print(f"Maybe {posting.get_text()}?")
                        raw_soup = postings[posting]
                        soup_no_links = BeautifulSoup(re.sub('(?=<a)[\s\S]*(?<=</a>)', '', str(raw_soup)), 'html.parser')
                        texts = soup_no_links.find_all(text=True)
                        visible_texts = filter(tag_visible, texts)
                        posting_text = " ".join(t.strip() for t in visible_texts)
                        keyword_matches = []
                        for keyword in keywords:
                            if keyword in posting_text.lower():
                                keyword_matches.append(keyword)  #this variable is not used downstream (for now!)
                        if not keyword_matches:
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
                    if set(new_stale_links.split(' ')) != set(stale_links.split(' ')):
                        with create_connection() as conn:
                            conn.cursor().execute("""
                                UPDATE search SET stale_links=?
                                WHERE id=?
                            """, [new_stale_links, search_id])
    
    with create_connection() as conn:
        search_info = conn.cursor().execute("""
            SELECT id FROM search
        """).fetchall()
        search_ids = [x[0] for x in search_info]
    
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
            print(f"posting '{result[1][posting]}' is a valid match! logging and sending email...")
            with create_connection() as conn:
                conn.cursor().execute("""
                    INSERT INTO found (search_id, link, title, date_found) VALUES (?, ?, ?, ?)
                """, [search_id, posting, result[1][posting], datetime.datetime.now().date()])
                found_id = conn.cursor().execute("""
                    SELECT id FROM found ORDER BY id DESC LIMIT 1
                """).fetchone()[0]
            send_email(found_id)


if __name__ == "__main__":
    asyncio.run(main())