#!/usr/bin/env python

from flask import Flask, render_template, url_for, request, redirect, session
from flask_session import Session
import datetime
from dateutil.parser import parse as parse_date
from utils import create_connection
import pandas as pd
import logging
import sys
import os
import re
import sqlite3
import json
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from oauthlib.oauth2 import WebApplicationClient
import requests
from user import User
from functools import lru_cache

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

app = Flask(__name__)

#set up Flask-Sessions
app.config.from_object(__name__)
app.config['SESSION_TYPE'] = 'filesystem'

try:
    with open(".secret.json") as f:
        app.config['SECRET_KEY'] = json.load(f)["flask_session_key"]
except FileNotFoundError:  # no `.secret.json` file if running in CI
    app.config['SECRET_KEY'] = "JUSTTESTING"

Session(app)

# trick from SO for properly relaoding CSS
app.config['TEMPLATES_AUTO_RELOAD'] = True

set_default_user_id = False
try:
    with open(".secret.json") as f:
        cred = json.load(f)["oauth_cred"]
    GOOGLE_CLIENT_ID = cred.get("GOOGLE_CLIENT_ID", None)
    GOOGLE_CLIENT_SECRET = cred.get("GOOGLE_CLIENT_SECRET", None)
    client = WebApplicationClient(GOOGLE_CLIENT_ID)  # OAuth 2 client setup
except FileNotFoundError:  # CI server
    set_default_user_id = True  # to enable tests on CI server

GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)

# User session management setup
# https://flask-login.readthedocs.io/en/latest
login_manager = LoginManager()
login_manager.init_app(app)

# Flask-Login helper to retrieve a user from our db
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()

# this function works in conjunction with `dated_url_for` to make sure the browser uses
# the latest version of css stylesheet when modified and reloaded during testing
@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)
def dated_url_for(endpoint, **values):
    if endpoint == "static":
        filename = values.get("filename", None)
        if filename:
            file_path = os.path.join(app.root_path, endpoint, filename)
            values["q"] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)

def load_user():
    if session.get('user_id'):
        return
    username = current_user.name if current_user.is_authenticated else None
    if current_user.is_authenticated:
        session['user_id'] = current_user.id
        session['user_name'] = current_user.name
        session['user_email'] = current_user.email
        if session.get('user_id'):
            with create_connection() as conn:
                session['account_type'] = pd.read_sql("""
                SELECT * 
                FROM users 
                WHERE id=?
            """, conn, params=[current_user.id]).iloc[0].account_type
        if session.get('account_type') != "full":
            return redirect(url_for("index"))
    elif set_default_user_id:  # for CI server
        session['user_id'] = 1
        session['user_name'] = "Testing123"
        session['user_type'] = "full"
    else:  # for for dev and prod servers
        session['user_id'] = None

@app.route("/", methods=["POST", "GET"])
def index():
    load_user()
    return render_template('landing_page.html')

@app.route("/login")
def login():
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)


@app.route("/login/callback")
def callback():
    # Get authorization code Google sent back to you
    code = request.args.get("code")

    # Find out what URL to hit to get tokens that allow you to ask for
    # things on behalf of a user
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # Prepare and send request to get tokens! Yay tokens!
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code,
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    # Parse the tokens!
    client.parse_request_body_response(json.dumps(token_response.json()))

    # Now that we have tokens (yay) let's find and hit URL
    # from Google that gives you user's profile information,
    # including their Google Profile Image and Email
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    # We want to make sure their email is verified.
    # The user authenticated with Google, authorized our
    # app, and now we've verified their email through Google!
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
    else:
        return "User email not available or not verified by Google.", 400

    # Create a user in our db with the information provided
    # by Google
    user = User(
        id_=unique_id, name=users_name, email=users_email, profile_pic=picture
    )

    # Doesn't exist? Add to database
    if not User.get(unique_id):
        User.create(unique_id, users_name, users_email, picture)

    # Begin user session by logging the user in
    login_user(user)

    # Send user back to homepage
    return redirect(url_for("index"))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for("index"))

# Keeping here for later...
# @app.route("/summary_table")
# def summary_table():
#     load_user()
#     if session.get('account_type') != "full":
#         return redirect(url_for("payment"))
#     def highlight_pending(s):
#         days_old = (
#             datetime.datetime.now().date()
#             - parse_date(re.findall("\d{4}-\d{2}-\d{2}", s.pub_date)[0]).date()
#         ).days
#         if days_old < 60:  # fresh - within lien period
#             row_colour = "rgb(97, 62, 143)"
#         else:
#             row_colour = ""
#         return [f"color: {row_colour}" for i in range(len(s))]
#     col_order = [
#         "job_number",
#         "title",
#         "contractor",
#         "engineer",
#         "owner",
#         "address",
#         "city",
#     ]
#     closed_query = """
#             SELECT
#                 company_projects.project_id,
#                 company_projects.job_number,
#                 company_projects.city,
#                 company_projects.address,
#                 company_projects.title,
#                 company_projects.owner,
#                 company_projects.contractor,
#                 company_projects.engineer,
#                 web.url_key,
#                 web.pub_date,
#                 (base_urls.base_url || web.url_key) AS link
#             FROM (SELECT * FROM web_certificates ORDER BY cert_id DESC LIMIT 16000) as web
#             LEFT JOIN
#                 attempted_matches
#             ON
#                 web.cert_id = attempted_matches.cert_id
#             LEFT JOIN
#                 company_projects
#             ON
#                 attempted_matches.project_id = company_projects.project_id
#             LEFT JOIN
#                 base_urls
#             ON
#                 base_urls.source = web.source
#             WHERE
#                 company_projects.closed=1
#             AND
#                 user_id=?
#             AND
#                 attempted_matches.ground_truth=1
#         """
#     open_query = """
#             SELECT *
#             FROM company_projects
#             WHERE company_projects.closed=0
#             AND user_id=?
#         """
#     with create_connection() as conn:
#         df_closed = pd.read_sql(closed_query, conn, params=[session.get('user_id')]).sort_values(
#             "job_number", ascending=False
#         )
#         df_open = pd.read_sql(open_query, conn, params=[session.get('user_id')]).sort_values(
#             "job_number", ascending=False
#         )
#     pd.set_option("display.max_colwidth", -1)
#     if not len(df_closed):
#         df_closed = None
#     else:
#         df_closed["job_number"] = df_closed.apply(
#             lambda row: f"""<a href="{row.link}">{row.job_number}</a>""", axis=1
#         )
#         df_closed = df_closed.drop("url_key", axis=1)
#         df_closed = (
#             df_closed[["pub_date"] + col_order]
#             .style.set_table_styles(
#                 [
#                     {
#                         "selector": "th",
#                         "props": [
#                             ("background-color", "rgb(122, 128, 138)"),
#                             ("color", "black"),
#                         ],
#                     }
#                 ]
#             )
#             .set_table_attributes('border="1"')
#             .set_properties(
#                 **{"font-size": "10pt", "background-color": "rgb(168, 185, 191)"}
#             )
#             .set_properties(subset=["action", "job_number"], **{"text-align": "center"})
#             .hide_index()
#             .apply(highlight_pending, axis=1)
#         )
#         df_closed = df_closed.render(escape=False)
#     if not len(df_open):
#         df_open = None
#     else:
#         df_open["action"] = df_open.apply(
#             lambda row: (
#                 f"""<a href="{url_for('project_entry', **row)}">modify</a> / """
#                 f"""<a href="{url_for('delete_job', project_id=row.project_id)}">delete</a>"""
#             ),
#             axis=1,
#         )
#         df_open["contacts"] = df_open.apply(
#             lambda row: ", ".join(ast.literal_eval(row.receiver_emails_dump).keys()),
#             axis=1,
#         )
#         df_open = (
#             df_open[["action"] + col_order + ["contacts"]]
#             .style.set_table_styles(
#                 [
#                     {
#                         "selector": "th",
#                         "props": [
#                             ("background-color", "rgb(122, 128, 138)"),
#                             ("color", "black"),
#                         ],
#                     }
#                 ]
#             )
#             .set_table_attributes('border="1"')
#             .set_properties(
#                 **{"font-size": "10pt", "background-color": "rgb(168, 185, 191)"}
#             )
#             .set_properties(
#                 subset=["action", "job_number", "contacts"], **{"text-align": "center"}
#             )
#             .hide_index()
#         )
#         df_open = df_open.render(escape=False)
#     return render_template(
#         "summary_table.html",
#         df_closed=df_closed,
#         df_open=df_open,
#     )


# @app.route("/delete_job")
# def delete_job():
#     if session.get('account_type') != "full":
#         return redirect(url_for("payment"))
#     delete_job_query = """
#             DELETE FROM company_projects
#             WHERE project_id=?
#         """
#     delete_match_query = """
#             DELETE FROM attempted_matches
#             WHERE project_id=?
#         """
#     project_id = request.args.get("project_id")
#     with create_connection() as conn:
#         conn.cursor().execute(delete_job_query, [project_id])
#         conn.cursor().execute(delete_match_query, [project_id])
#     return redirect(url_for("summary_table"))

@app.route("/about", methods=["POST", "GET"])
def about():
    return render_template("about.html")

@app.route("/search_entry", methods=["POST", "GET"])
def search_entry():
    load_user()
    if request.method == "POST":
        with create_connection() as conn:
            conn.cursor().execute(f"""
                INSERT INTO search (user_id, career_page, keywords, date_added) VALUES (?, ?, ?, ?)
            """, [session.get('user_id'), request.form.get('career_page'), request.form.get('keywords'), datetime.datetime.now().date()])
        return render_template("signup_confirmation.html")
    else:
        print('fuck')
        return redirect(url_for('/'))

@app.route("/user_account", methods=["POST", "GET"])
def user_account():
    load_user()
    return render_template("user_account.html")

@app.route("/terminate_account", methods=["POST", "GET"])
def terminate_account():
    load_user()
    if request.args.get('confirmed'):
        update_account_type_query = (
            "UPDATE users SET account_type = '' WHERE id = ?"
        )
        with create_connection() as conn:
            conn.cursor().execute(update_account_type_query, [session.get('user_id')])
        session.clear()
        return redirect(url_for("index"))
    return render_template("terminate_account.html")

if __name__ == "__main__":
    app.run(debug=True, ssl_context="adhoc")
