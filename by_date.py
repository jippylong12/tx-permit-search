import os
import re
import requests
from http.cookiejar import MozillaCookieJar
from datetime import datetime, date
from constants import LOOKUP # Import the LOOKUP dictionary

# --- Settings ---
# IMPORTANT: Set your cutoff date here in 'YYYY-MM-DD' format
CUTOFF_DATE_STR = '2023-01-01'  # Example: '2023-01-01'
COOKIE_FILE = 'cookies.txt'
SEARCH_URL = 'https://www.tdlr.texas.gov/TABS/Search/SearchProjects'
RECORD_LIMIT = 250  # Download the latest 250 records
PAGE_SIZE = 100
TYPE_OF_WORK = '' # Keep empty to not filter by type of work, or specify one.

# --- Date Parsing Function ---
def parse_tdlr_date_str(date_str_from_json):
    """
    Parses date strings from TDLR JSON like '/Date(1690434000000-0500)/'
    or common date formats like 'YYYY-MM-DDTHH:MM:SS'.
    Returns a datetime.date object or None if parsing fails.
    """
    if not date_str_from_json:
        return None
    
    match = re.search(r'/Date\((\d+)(?:[-+]\d{4})?\)/', date_str_from_json)
    if match:
        timestamp_ms = int(match.group(1))
        try:
            return datetime.fromtimestamp(timestamp_ms / 1000).date()
        except ValueError:
            print(f"[WARNING] Could not convert timestamp: {timestamp_ms}")
            return None
            
    try:
        return datetime.strptime(date_str_from_json.split('T')[0], '%Y-%m-%d').date()
    except ValueError:
        print(f"[WARNING] Could not parse date string: {date_str_from_json} with common formats.")
        return None

# --- Session Setup ---
session = requests.Session()
session.cookies = MozillaCookieJar(COOKIE_FILE)
if os.path.exists(COOKIE_FILE):
    try:
        session.cookies.load(ignore_discard=True, ignore_expires=True)
        print(f"[INFO] Cookies loaded from {COOKIE_FILE}")
    except Exception as e:
        print(f"[WARNING] Could not load cookies: {e}. Proceeding without loaded cookies.")
else:
    print(f"[INFO] Cookie file {COOKIE_FILE} not found. Proceeding without loaded cookies.")


# --- Function to build form data ---
def build_form_data(start):
    return {
        'draw': '7',
        'columns[0][data]': 'ProjectId', 'columns[0][name]': '', 'columns[0][searchable]': 'true', 'columns[0][orderable]': 'true', 'columns[0][search][value]': '', 'columns[0][search][regex]': 'false',
        'columns[1][data]': 'ProjectNumber', 'columns[1][name]': '', 'columns[1][searchable]': 'true', 'columns[1][orderable]': 'true', 'columns[1][search][value]': '', 'columns[1][search][regex]': 'false',
        'columns[2][data]': 'ProjectName', 'columns[2][name]': '', 'columns[2][searchable]': 'true', 'columns[2][orderable]': 'true', 'columns[2][search][value]': '', 'columns[2][search][regex]': 'false',
        'columns[3][data]': 'ProjectCreatedOn', 'columns[3][name]': '', 'columns[3][searchable]': 'true', 'columns[3][orderable]': 'true', 'columns[3][search][value]': '', 'columns[3][search][regex]': 'false',
        'columns[4][data]': 'ProjectStatus', 'columns[4][name]': '', 'columns[4][searchable]': 'true', 'columns[4][orderable]': 'true', 'columns[4][search][value]': '', 'columns[4][search][regex]': 'false',
        'columns[5][data]': 'FacilityName', 'columns[5][name]': '', 'columns[5][searchable]': 'true', 'columns[5][orderable]': 'true', 'columns[5][search][value]': '', 'columns[5][search][regex]': 'false',
        'columns[6][data]': 'City', 'columns[6][name]': '', 'columns[6][searchable]': 'true', 'columns[6][orderable]': 'true', 'columns[6][search][value]': '', 'columns[6][search][regex]': 'false',
        'columns[7][data]': 'County', 'columns[7][name]': '', 'columns[7][searchable]': 'true', 'columns[7][orderable]': 'true', 'columns[7][search][value]': '', 'columns[7][search][regex]': 'false',
        'columns[8][data]': 'TypeOfWork', 'columns[8][name]': '', 'columns[8][searchable]': 'true', 'columns[8][orderable]': 'true', 'columns[8][search][value]': TYPE_OF_WORK, 'columns[8][search][regex]': 'false',
        'columns[9][data]': 'EstimatedCost', 'columns[9][name]': '', 'columns[9][searchable]': 'true', 'columns[9][orderable]': 'true', 'columns[9][search][value]': '', 'columns[9][search][regex]': 'false',
        'columns[10][data]': 'DataVersionId', 'columns[10][name]': '', 'columns[10][searchable]': 'false', 'columns[10][orderable]': 'true', 'columns[10][search][value]': '', 'columns[10][search][regex]': 'false',
        'order[0][column]': '3',  # Order by ProjectCreatedOn
        'order[0][dir]': 'desc', # Descending to get latest
        'start': str(start),
        'length': str(PAGE_SIZE),
        'search[value]': '',
        'search[regex]': 'false',
    }

# --- Main data collection ---
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
all_data = []
start = 0

print(f"[INFO] Attempting to fetch up to {RECORD_LIMIT} latest records.")
while len(all_data) < RECORD_LIMIT:
    print(f"[INFO] Fetching records {start} to {start + PAGE_SIZE}...")
    try:
        response = session.post(SEARCH_URL, data=build_form_data(start), headers=headers, timeout=30)
        response.raise_for_status() 
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Request failed: {e}")
        break

    try:
        payload = response.json()
    except requests.exceptions.JSONDecodeError:
        print(f"[ERROR] Failed to decode JSON response. Status code: {response.status_code}, Response text: {response.text[:200]}")
        break
        
    new_data = payload.get('data', [])

    if not new_data:
        print("[INFO] No more data found from the source.")
        break

    all_data.extend(new_data)

    if len(new_data) < PAGE_SIZE:
        print("[INFO] Fetched all available data within the current query page size.")
        break 

    start += PAGE_SIZE

all_data = all_data[:RECORD_LIMIT]
print(f"[INFO] Successfully fetched {len(all_data)} records.")

# --- Filter data and Prepare for Report ---
try:
    cutoff_date_obj = datetime.strptime(CUTOFF_DATE_STR, '%Y-%m-%d').date()
    print(f"[INFO] Filtering records on or after cutoff date: {cutoff_date_obj.isoformat()}")
except ValueError:
    print(f"[ERROR] Invalid CUTOFF_DATE_STR: '{CUTOFF_DATE_STR}'. Please use 'YYYY-MM-DD' format.")
    exit()

report_data = []
for record in all_data:
    project_created_on_str = record.get('ProjectCreatedOn')
    record_date = parse_tdlr_date_str(project_created_on_str)

    if record_date and record_date >= cutoff_date_obj:
        city_name = record.get('City')
        county_name = record.get('County')

        # Perform lookups, defaulting to None if not found
        city_id = LOOKUP.get("CITIES", {}).get(str(city_name)) if city_name else None
        county_id = LOOKUP.get("COUNTIES", {}).get(str(county_name)) if county_name else None
        
        report_data.append({
            'ProjectNumber': record.get('ProjectNumber', 'N/A'),
            'ProjectName': record.get('ProjectName', 'N/A'),
            'Date': record_date.isoformat() if record_date else 'N/A',
            'FacilityName': record.get('FacilityName', 'N/A'),
            'City': city_id, # Store integer ID or None
            'County': county_id, # Store integer ID or None
        })

print(f"[INFO] Found {len(report_data)} records matching the criteria.")

# --- Generate and Display Table ---
if report_data:
    print("\n--- Project Report ---")
    header_format = "| {:<15} | {:<40} | {:<10} | {:<30} | {:<20} | {:<20} |"
    header = header_format.format(
        "ProjectNumber", "ProjectName", "Date", "FacilityName", "City (ID)", "County (ID)"
    )
    print(header)
    print("-" * len(header))

    for item in report_data:
        # Helper to format None as 'N/A' for display
        display_city = item['City'] if item['City'] is not None else 'N/A'
        display_county = item['County'] if item['County'] is not None else 'N/A'
        
        print(header_format.format(
            str(item['ProjectNumber']),
            str(item['ProjectName'])[:38], # Truncate if too long
            str(item['Date']),
            str(item['FacilityName'])[:28], # Truncate if too long
            str(display_city),
            str(display_county)
        ))
    print("-" * len(header))
else:
    print("\n[INFO] No records to display based on the specified cutoff date and other criteria.")

print("\n[SUCCESS] Report generation finished.")