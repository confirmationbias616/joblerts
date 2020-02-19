import pandas as pd
import datetime
import re
import asyncio

from finder import get_posting_links
from async_finder import main
from utils import create_connection


async def routine():
    with create_connection() as conn:
        search_df = pd.read_sql("SELECT * FROM search", conn)
    page_searches = {}
    for _, row in search_df.iterrows():
        page_searches.update({row.career_page: [[str(row.id), row.keywords]]})
    results = await main(page_searches)
    for result in results:
        search_id = result[0]
        for posting in result[1]:
            print(f"{result[1][posting]}: {posting}")
            with create_connection() as conn:
                conn.cursor().execute(f"""
                    INSERT INTO found (search_id, link, keywords, date_found) VALUES (?, ?, ?, ?)
                """, [search_id, posting, result[1][posting], datetime.datetime.now().date()])

if __name__ == "__main__":
    asyncio.run(routine())