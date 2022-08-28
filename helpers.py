import os
import requests

from flask import render_template, redirect, request, session
from functools import wraps
import datetime
from random import randint

def error(message, code=400):

    def escape(s):
        """Escape special characters."""

        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("error.html", top=code, bottom=escape(message)), code 

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None and session.get("user_status") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def date():
    now = datetime.datetime.now()
    return now.strftime('%Y-%m-%d %H:%M:%S')

def rann():
    x = ""
    for i in range(6):
        x += str(randint(0,9))
    return x
