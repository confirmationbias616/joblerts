import sqlite3
from sqlite3 import Error
import pandas as pd
import json
import sys
import datetime
import logging

logger = logging.getLogger(__name__)
log_handler = logging.StreamHandler(sys.stdout)
log_handler.setFormatter(
    logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(funcName)s "
        "- line %(lineno)d"
    )
)
logger.addHandler(log_handler)
logger.setLevel(logging.INFO)


def persistant_cache(file_name):
    """Creates and/or updates persitant cache in json format with given filename."""
    def decorator(original_func):
        try:
            cache = json.load(open(file_name, 'r'))
        except (IOError, ValueError):
            cache = {}
        def new_func(param):
            if param not in cache:
                cache[param] = original_func(param)
                json.dump(cache, open(file_name, 'w'), indent=4)
            return cache[param]
        return new_func
    return decorator


def create_connection(db_name="job_db.sqlite3"):
    """Creates a connection with specified SQLite3 database in current directory.
    Connection conveniently closes on unindent of with block.

    Typical usage pattern is as follows:
    with create_connection() as conn:
        some_df = pd.read_sql(some_query, conn)
    
    """
    try:
        conn = sqlite3.connect(db_name)
        return conn
    except Error as e:
        logger.critical(e)
    return None

def custom_query(query):
    """Run custom SQL query against job_db.sqlite3"""
    try:
        with create_connection() as conn:
            result =  pd.read_sql(query, conn)
        print(result)
        return result
    except TypeError:
        with create_connection() as conn:
            conn.cursor().execute(query)
        print("SQL statement executed.")
        return

def dbtables_to_csv(db_name="job_db.sqlite3", destination=""):
    """Writes all tables of specified SQLite3 database to separate CSV files located in
    specified destination subdirectory.
    Not specifying a destination parameter will save CSV files to current directory.

    """
    with create_connection(db_name) as conn:
        table_names = (
            conn.cursor()
            .execute("SELECT name FROM sqlite_master WHERE type='table';")
            .fetchall()
        )
    table_names = [x[0] for x in table_names]
    open_query = "SELECT * FROM {}"
    for table in table_names:
        with create_connection(db_name) as conn:
            pd.read_sql(open_query.format(table), conn).to_csv(
                f"{destination}{'/' if destination else ''}{table}.csv", index=False
            )
    
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

