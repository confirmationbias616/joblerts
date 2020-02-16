import pandas as pd
import datetime
import re

from finder import get_posting_links
from utils import create_connection


with create_connection() as conn:
    search_df = pd.read_sql("SELECT * FROM search", conn)

def show_results():
    for _, row in search_df.iterrows():
        result = get_posting_links(row['career_page'], row.keywords)[0]
        title = re.findall('[A-z0-9 \-\/:]+', result[1].title())[0].lstrip().rstrip()
        link = result[0]
        return f"{title}: {link}"

if __name__ == "__main__":
    print(show_results())