# using SendGrid's Python Library
# https://github.com/sendgrid/sendgrid-python
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, From, To
import json
import argparse
from utils import create_connection, get_valid_link
import pandas as pd


def send_email(found_id):
    with create_connection() as conn:
        found = pd.read_sql("""
            SELECT
                users.name as user_name,
                users.email,
                search.career_page,
                search.company,
                searc.keywords,
                found.title,
                found.link 
            FROM found
            JOIN search 
            ON search.id = found.search_id
            JOIN users 
            ON users.id = search.user_id
            WHERE found.id = ?
        """, conn, params=[found_id]).iloc[0]
    print(found.user_name)
    message = Mail(
        to_emails=found.email,
        subject=f'New Job Posting for {found.title}',
        html_content=f"""
            <body>
                Hi {found.user_name},
                <br><br>
                Looks like one of your target career pages (<a href='{found.career_page}'>{found.company}</a>)
                recently posted a new job for <a href='{get_valid_link(found.career_page, found.link)}'>{found.title}</a>.
                <br><br>
                This matches your search for keyword "{found.keywords}".
                <br><br>
                Good luck!<br>
                <a href='www.joblert.me'>joblert.me</a>
            </body>
        """)
    message.from_email = From('notifications@joblert.me', 'joblert.me')
    print(found.user_name)
    message.to_email = To(found.email, found.user_name)
    try:
        with open(".secret.json") as f:
            api_key = json.load(f)["sendgrid_key"]
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e.message)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument( "-i", "--found_id", type=str)
    args = parser.parse_args()
    send_email(args.found_id)