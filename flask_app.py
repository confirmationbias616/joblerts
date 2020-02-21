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

def load_search_table(user_id):
    fetch_searches_query = """
        SELECT * FROM search
        WHERE user_id = ?
    """
    with create_connection() as conn:
        search_table = pd.read_sql(fetch_searches_query, conn, params=[user_id])    
    return search_table

# function could be improved to find whichever candidate shows up most frequently within visible
# text of base_url page. Make sure to use aiohttp to avoid blocking the event loop if this is
# implemented!
def get_company_name(base_url):
    words = (re.findall('[^#$%&/.:]{3,}', base_url))
    discard_words = ('career', 'careers', 'job', 'jobs', 'lever', 'www', 'http', 'https', 'gov', 'com')
    candidates = [word for word in words if word not in discard_words]
    company_name = candidates[0].title()
    return company_name

@app.route("/", methods=["POST", "GET"])
def index():
    load_user()
    search_table = load_search_table(session['user_id'])
    if len(search_table):
        search_table["action"] = search_table.apply(
            lambda row: (
                f"{url_for('delete_search', id=row.id)}"
            ),
            axis=1,
        )
        search_table_html = (search_table
            .style.set_table_styles(
                [
                    {
                        "selector": "th",
                        "props": [
                            ("background-color", "rgb(122, 128, 138)"),
                            ("color", "black"),
                        ],
                    }
                ]
            )
            .set_table_attributes('border="1"')
            .set_properties(
                **{"font-size": "10pt", "background-color": "rgb(168, 185, 191)"}
            )
            .set_properties(
                subset=["action"], **{"text-align": "center"}
            )
            .hide_index()
        )
        search_table_html = search_table_html.render(escape=False)
    else:
        search_table_html = None
    return render_template('landing_page.html', search_table=search_table, search_table_html=search_table_html)

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


@app.route("/delete_search")
def delete_search():
    delete_search_query = """
            DELETE FROM search
            WHERE id=?
        """
    id = request.args.get("id")
    with create_connection() as conn:
        conn.cursor().execute(delete_search_query, [id])
    return redirect(url_for("index"))

@app.route("/about", methods=["POST", "GET"])
def about():
    return render_template("about.html")

@app.route("/search_entry", methods=["POST", "GET"])
def search_entry():
    load_user()
    if request.method == "POST":
        with create_connection() as conn:
            conn.cursor().execute(f"""
                INSERT INTO search (user_id, career_page, company, keywords, date_added) VALUES (?, ?, ?, ?, ?)
            """, [session.get('user_id'), request.form.get('career_page'), get_company_name(request.form.get('career_page')), request.form.get('keywords').title(), datetime.datetime.now().date()])
        return redirect(url_for("index"))

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
