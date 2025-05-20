import os
import requests
from http.cookiejar import MozillaCookieJar
from dotenv import load_dotenv

# Load credentials from .env
load_dotenv()
EMAIL = os.getenv('Email')
PASSWORD = os.getenv('Password')

# Paths
COOKIE_FILE = 'cookies.txt'

# URLs
LOGIN_URL = 'https://www.tdlr.texas.gov/TABS/Account/Login'
DASHBOARD_URL = 'https://www.tdlr.texas.gov/TABS/Home/Dashboard'

# Create session
session = requests.Session()
session.cookies = MozillaCookieJar(COOKIE_FILE)

# Load cookies if available
if os.path.exists(COOKIE_FILE):
    session.cookies.load(ignore_discard=True, ignore_expires=True)

def login_if_needed():
    # Check if already logged in
    resp = session.get(DASHBOARD_URL, allow_redirects=False)

    if resp.status_code == 302 and 'Login' in resp.headers.get('Location', ''):
        print("[INFO] Session expired or not logged in. Logging in...")

        login_payload = {
            'Email': EMAIL,
            'Password': PASSWORD
        }

        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        resp = session.post(LOGIN_URL, data=login_payload, headers=headers)

        if "Dashboard" in resp.url or resp.status_code == 200:
            print("[SUCCESS] Logged in successfully.")
            session.cookies.save(ignore_discard=True, ignore_expires=True)
        else:
            print("[ERROR] Login failed. Status:", resp.status_code)
            print(resp.text)
    else:
        print("[INFO] Already logged in using saved cookies.")

# Run login check
login_if_needed()

# Now access a protected page
response = session.get(DASHBOARD_URL)
print(response.text[:500])  # print first 500 characters