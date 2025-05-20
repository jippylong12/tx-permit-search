import os
import pickle
import requests
from http.cookiejar import MozillaCookieJar

# --- Settings ---
COOKIE_FILE = 'cookies.txt'
SEARCH_URL = 'https://www.tdlr.texas.gov/TABS/Search/SearchProjects'
OUTPUT_FILE = 'tabs_projects_9001.pkl'
RECORD_LIMIT = 5000
PAGE_SIZE = 100
TYPE_OF_WORK = ''

# --- Session Setup ---
session = requests.Session()
session.cookies = MozillaCookieJar(COOKIE_FILE)
if os.path.exists(COOKIE_FILE):
    session.cookies.load(ignore_discard=True, ignore_expires=True)

# --- Function to build form data ---
def build_form_data(start):
    return {
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
        'columns[8][search][value]': TYPE_OF_WORK,
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
        'start': str(start),
        'length': str(PAGE_SIZE),
        'search[value]': '',
        'search[regex]': 'false',
    }

# --- Main data collection ---
headers = {'User-Agent': 'Mozilla/5.0'}
all_data = []
start = 0

while len(all_data) < RECORD_LIMIT:
    print(f"[INFO] Fetching records {start} to {start + PAGE_SIZE}...")

    response = session.post(SEARCH_URL, data=build_form_data(start), headers=headers)

    if not response.ok:
        print(f"[ERROR] Failed to fetch data at offset {start}")
        break

    payload = response.json()
    new_data = payload.get('data', [])

    if not new_data:
        print("[INFO] No more data found.")
        break

    all_data.extend(new_data)

    if len(new_data) < PAGE_SIZE:
        break  # No more data available

    start += PAGE_SIZE

# Trim to limit (in case of over-fetch)
all_data = all_data[:RECORD_LIMIT]

# --- Save to pickle ---
with open(OUTPUT_FILE, 'wb') as f:
    pickle.dump(all_data, f)

print(f"[SUCCESS] Saved {len(all_data)} records to {OUTPUT_FILE}")