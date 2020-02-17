import pandas as pd
import datetime
import re

from finder import get_posting_links
from utils import create_connection


with create_connection() as conn:
    search_df = pd.read_sql("SELECT * FROM search", conn)

def show_results():
    for _, row in search_df.iterrows():
        results = get_posting_links(row['career_page'], row.keywords)
        if results:
            result = results[0]
            title = re.findall('[A-z0-9 \-\/:]+', result[1].title())[0].lstrip().rstrip()
            link = result[0]
            print(f"{title}: {link}")
            with create_connection() as conn:
                conn.cursor().execute(f"""
                INSERT INTO found (search_id, link, date_found) VALUES (?, ?, ?)
            """, [row.id, link, datetime.datetime.now().date()])
        else:
            print("nothing found.")

if __name__ == "__main__":
    show_results()