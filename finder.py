import requests
from bs4 import BeautifulSoup
import re
from time import sleep
from functools import lru_cache
import argparse


@lru_cache()
def get_link_response(link):
    while True:
        try:
            response = requests.get(link, headers={'User-Agent': 'Mozilla/5.0'})
            return response
        except requests.exceptions.ConnectionError:
            sleep(1)
            continue

@lru_cache()
def find_postings(entry, keyword):
    response = get_link_response(entry)
    html = response.content
    entry_soup = BeautifulSoup(html, "html.parser")
    postings = {posting.get('href'): posting.get_text() for posting in entry_soup.find_all("a") if keyword in posting.get_text().lower()}
    return postings

@lru_cache()
def vet_link(link):
    try:
        sleep(1)
        response = requests.get(link, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code >= 300:
            return None
        raw_html = str(response.content.lower())
        for career_term in ('responsibilities', 'full-time', 'salary', 'posting', 'equal opportunity', 'full time', 'part-time', 'part time'):
            if career_term in raw_html:
                return link
        return 'not_job_link'
    except requests.exceptions.MissingSchema:
        return None

@lru_cache()
def get_posting_links(entry, keyword):
    keywrod = keyword.lower()
    postings = find_postings(entry, keyword)
    posting_links = postings.keys()
    results = []
    for posting_link in posting_links:
        full_link = vet_link(posting_link)
        if full_link:
            if full_link != 'not_job_link':
                results.append((full_link, postings[posting_link]))
            continue
        link_with_params = re.findall('.*(?=\?)', entry)
        search_base_link = link_with_params[0] if link_with_params else entry
        full_link = search_base_link + posting_link
        full_link = vet_link(full_link)
        if full_link:
            if full_link != 'not_job_link':
                results.append((full_link, postings[posting_link]))
            continue
        try:
            parent_link = re.findall('.*(?=/)', search_base_link)[0]
            full_link = parent_link + posting_link
            full_link = vet_link(full_link)
        except IndexError:
            pass
        if full_link:
            if full_link != 'not_job_link':
                results.append((full_link, postings[posting_link]))
            continue
        try:
            parent_link_2 = re.findall('.*(?=/)', parent_link)[0]
            full_link = parent_link_2 + posting_link
            full_link = vet_link(full_link)
        except IndexError:
            pass
        if full_link:
            if full_link != 'not_job_link':
                results.append((full_link, postings[posting_link]))
            continue
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-e",
        "--entry",
        type=str,
    )
    parser.add_argument(
        "-k",
        "--keyword",
        type=str,
    )
    args = parser.parse_args()
    entry = args.entry
    keyword = args.keyword
    print(get_posting_links(entry, keyword))