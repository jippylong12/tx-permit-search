import os
import requests
from http.cookiejar import MozillaCookieJar

# Constants
COOKIE_FILE = 'cookies.txt'
SEARCH_URL = 'https://www.tdlr.texas.gov/TABS/Search/SearchProjects'

# Setup session
session = requests.Session()
session.cookies = MozillaCookieJar(COOKIE_FILE)
if os.path.exists(COOKIE_FILE):
    session.cookies.load(ignore_discard=True, ignore_expires=True)

# Form data
form_data = {
    'draw': '7',
    'columns[0][data]': 'ProjectId',
    'columns[0][name]': '',
    'columns[0][searchable]': 'true',
    'columns[0][orderable]': 'true',
    'columns[0][search][value]': '',
    'columns[0][search][regex]': 'false',
    'columns[1][data]': 'ProjectNumber',
    'columns[1][name]': '',
    'columns[1][searchable]': 'true',
    'columns[1][orderable]': 'true',
    'columns[1][search][value]': '',
    'columns[1][search][regex]': 'false',
    'columns[2][data]': 'ProjectName',
    'columns[2][name]': '',
    'columns[2][searchable]': 'true',
    'columns[2][orderable]': 'true',
    'columns[2][search][value]': '',
    'columns[2][search][regex]': 'false',
    'columns[3][data]': 'ProjectCreatedOn',
    'columns[3][name]': '',
    'columns[3][searchable]': 'true',
    'columns[3][orderable]': 'true',
    'columns[3][search][value]': '',
    'columns[3][search][regex]': 'false',
    'columns[4][data]': 'ProjectStatus',
    'columns[4][name]': '',
    'columns[4][searchable]': 'true',
    'columns[4][orderable]': 'true',
    'columns[4][search][value]': '',
    'columns[4][search][regex]': 'false',
    'columns[5][data]': 'FacilityName',
    'columns[5][name]': '',
    'columns[5][searchable]': 'true',
    'columns[5][orderable]': 'true',
    'columns[5][search][value]': '',
    'columns[5][search][regex]': 'false',
    'columns[6][data]': 'City',
    'columns[6][name]': '',
    'columns[6][searchable]': 'true',
    'columns[6][orderable]': 'true',
    'columns[6][search][value]': '',
    'columns[6][search][regex]': 'false',
    'columns[7][data]': 'County',
    'columns[7][name]': '',
    'columns[7][searchable]': 'true',
    'columns[7][orderable]': 'true',
    'columns[7][search][value]': '',
    'columns[7][search][regex]': 'false',
    'columns[8][data]': 'TypeOfWork',
    'columns[8][name]': '',
    'columns[8][searchable]': 'true',
    'columns[8][orderable]': 'true',
    'columns[8][search][value]': '9001',
    'columns[8][search][regex]': 'false',
    'columns[9][data]': 'EstimatedCost',
    'columns[9][name]': '',
    'columns[9][searchable]': 'true',
    'columns[9][orderable]': 'true',
    'columns[9][search][value]': '',
    'columns[9][search][regex]': 'false',
    'columns[10][data]': 'DataVersionId',
    'columns[10][name]': '',
    'columns[10][searchable]': 'false',
    'columns[10][orderable]': 'true',
    'columns[10][search][value]': '',
    'columns[10][search][regex]': 'false',
    'order[0][column]': '3',
    'order[0][dir]': 'desc',
    'start': '0',
    'length': '1',
    'search[value]': '',
    'search[regex]': 'false',
}

# Make the POST request
headers = {
    'User-Agent': 'Mozilla/5.0',
    'Content-Type': 'application/x-www-form-urlencoded'
}

response = session.post(SEARCH_URL, data=form_data, headers=headers)

# Handle response
if response.ok:
    print("[SUCCESS] Data retrieved")
    print(response.json())
else:
    print(f"[ERROR] Status: {response.status_code}")
    print(response.text)