import os
import re
import requests
from http.cookiejar import MozillaCookieJar
from datetime import datetime, date
from constants import LOOKUP  # Import the LOOKUP dictionary
import pickle
from bs4 import BeautifulSoup
from tabulate import tabulate

# --- Settings ---
CUTOFF_DATE_STR = '2025-05-21'  # Example: '2025-05-22'
COOKIE_FILE = 'cookies.txt'
SEARCH_URL = 'https://www.tdlr.texas.gov/TABS/Search/SearchProjects'
RECORD_LIMIT = 200
PAGE_SIZE = 100
TYPE_OF_WORK = ''
OUTPUT_DATA_FOLDER = 'output_data'  # Folder to store pickle files

# --- Global headers for requests ---
REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}


# --- Date Parsing Function ---
def parse_tdlr_date_str(date_str_from_json):
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


# --- Function to build form data ---
def build_form_data(start):
    return {
        'draw': '7',
        'columns[0][data]': 'ProjectId', 'columns[0][name]': '', 'columns[0][searchable]': 'true',
        'columns[0][orderable]': 'true', 'columns[0][search][value]': '', 'columns[0][search][regex]': 'false',
        'columns[1][data]': 'ProjectNumber', 'columns[1][name]': '', 'columns[1][searchable]': 'true',
        'columns[1][orderable]': 'true', 'columns[1][search][value]': '', 'columns[1][search][regex]': 'false',
        'columns[2][data]': 'ProjectName', 'columns[2][name]': '', 'columns[2][searchable]': 'true',
        'columns[2][orderable]': 'true', 'columns[2][search][value]': '', 'columns[2][search][regex]': 'false',
        'columns[3][data]': 'ProjectCreatedOn', 'columns[3][name]': '', 'columns[3][searchable]': 'true',
        'columns[3][orderable]': 'true', 'columns[3][search][value]': '', 'columns[3][search][regex]': 'false',
        'columns[4][data]': 'ProjectStatus', 'columns[4][name]': '', 'columns[4][searchable]': 'true',
        'columns[4][orderable]': 'true', 'columns[4][search][value]': '', 'columns[4][search][regex]': 'false',
        'columns[5][data]': 'FacilityName', 'columns[5][name]': '', 'columns[5][searchable]': 'true',
        'columns[5][orderable]': 'true', 'columns[5][search][value]': '', 'columns[5][search][regex]': 'false',
        'columns[6][data]': 'City', 'columns[6][name]': '', 'columns[6][searchable]': 'true',
        'columns[6][orderable]': 'true', 'columns[6][search][value]': '', 'columns[6][search][regex]': 'false',
        'columns[7][data]': 'County', 'columns[7][name]': '', 'columns[7][searchable]': 'true',
        'columns[7][orderable]': 'true', 'columns[7][search][value]': '', 'columns[7][search][regex]': 'false',
        'columns[8][data]': 'TypeOfWork', 'columns[8][name]': '', 'columns[8][searchable]': 'true',
        'columns[8][orderable]': 'true', 'columns[8][search][value]': TYPE_OF_WORK,
        'columns[8][search][regex]': 'false',
        'columns[9][data]': 'EstimatedCost', 'columns[9][name]': '', 'columns[9][searchable]': 'true',
        'columns[9][orderable]': 'true', 'columns[9][search][value]': '', 'columns[9][search][regex]': 'false',
        'columns[10][data]': 'DataVersionId', 'columns[10][name]': '', 'columns[10][searchable]': 'false',
        'columns[10][orderable]': 'true', 'columns[10][search][value]': '', 'columns[10][search][regex]': 'false',
        'order[0][column]': '3',
        'order[0][dir]': 'desc',
        'start': str(start),
        'length': str(PAGE_SIZE),
        'search[value]': '',
        'search[regex]': 'false',
    }


# --- Function to fetch Scope of Work ---
def fetch_scope_of_work(http_session, project_number):
    if not project_number:
        return "N/A"
    url = f"https://www.tdlr.texas.gov/TABS/Search/Project/{project_number}"
    try:
        response = http_session.get(url, headers=REQUEST_HEADERS, timeout=30)
        response.raise_for_status()
        html_content = response.text
        soup = BeautifulSoup(html_content, 'lxml')
        scope_dt = soup.find('dt', string=re.compile(r'Scope of Work:', re.IGNORECASE))
        if scope_dt:
            scope_dd = scope_dt.find_next('dd')
            if scope_dd:
                return scope_dd.text.strip()
        return "Not found"
    except requests.exceptions.RequestException as e:
        print(f"[WARNING] Could not fetch scope for project {project_number}: {e}")
        return "Error fetching"
    except Exception as e:
        print(f"[WARNING] Error parsing scope for project {project_number}: {e}")
        return "Error parsing"


# --- Main script logic ---
def main():
    # --- Ensure output directory exists ---
    os.makedirs(OUTPUT_DATA_FOLDER, exist_ok=True)
    print(f"[INFO] Output data will be stored in '{OUTPUT_DATA_FOLDER}/' directory.")

    # --- Initialize session ---
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

    # --- Define pickle filename based on current date and cutoff date ---
    today_str = datetime.now().strftime('%Y-%m-%d')
    # Sanitize CUTOFF_DATE_STR for filename (e.g., replace '-' with '_')
    cutoff_date_filename_part = CUTOFF_DATE_STR.replace('-', '_')
    pickle_filename = os.path.join(OUTPUT_DATA_FOLDER,
                                   f'project_report_data_{today_str}_cutoff_{cutoff_date_filename_part}.pkl')

    # --- Define filename for the combined string output ---
    combined_string_filename = os.path.join(OUTPUT_DATA_FOLDER,
                                            f'combined_projects_for_llm_{today_str}_cutoff_{cutoff_date_filename_part}.txt')

    report_data = []

    # --- Check if data already exists ---
    if os.path.exists(pickle_filename):
        print(f"[INFO] Found existing data file: {pickle_filename}")
        try:
            with open(pickle_filename, 'rb') as f:
                report_data = pickle.load(f)
            print(f"[INFO] Successfully loaded {len(report_data)} records from file.")
        except Exception as e:
            print(f"[ERROR] Failed to load data from {pickle_filename}: {e}. Will attempt to re-fetch.")
            report_data = []  # Reset if loading failed

    if not report_data:  # If no data loaded from file, then fetch
        print(
            f"[INFO] No pre-existing data found for today ({today_str}) with cutoff ({CUTOFF_DATE_STR}). Fetching new data.")
        all_data_from_search = []
        start = 0
        print(f"[INFO] Attempting to fetch up to {RECORD_LIMIT} latest records from TDLR.")
        while len(all_data_from_search) < RECORD_LIMIT:
            print(f"[INFO] Fetching records {start} to {start + PAGE_SIZE}...")
            try:
                response = session.post(SEARCH_URL, data=build_form_data(start), headers=REQUEST_HEADERS, timeout=30)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                print(f"[ERROR] Request failed during main search: {e}")
                break
            try:
                payload = response.json()
            except requests.exceptions.JSONDecodeError:
                print(
                    f"[ERROR] Failed to decode JSON response. Status: {response.status_code}, Text: {response.text[:200]}")
                break

            new_data = payload.get('data', [])
            if not new_data:
                print("[INFO] No more data found from the source.")
                break
            all_data_from_search.extend(new_data)
            if len(new_data) < PAGE_SIZE:
                print("[INFO] Fetched all available data within the current query page size.")
                break
            start += PAGE_SIZE

        all_data_from_search = all_data_from_search[:RECORD_LIMIT]
        print(f"[INFO] Successfully fetched {len(all_data_from_search)} records from TDLR main search.")

        try:
            cutoff_date_obj = datetime.strptime(CUTOFF_DATE_STR, '%Y-%m-%d').date()
            print(f"[INFO] Filtering records on or after cutoff date: {cutoff_date_obj.isoformat()}")
        except ValueError:
            print(f"[ERROR] Invalid CUTOFF_DATE_STR: '{CUTOFF_DATE_STR}'. Please use 'YYYY-MM-DD' format.")
            return  # Exit if cutoff date is invalid

        temp_report_data = []
        print(f"[INFO] Processing {len(all_data_from_search)} records to fetch scope of work and filter...")
        for i, record in enumerate(all_data_from_search):
            project_created_on_str = record.get('ProjectCreatedOn')
            record_date = parse_tdlr_date_str(project_created_on_str)

            if record_date and record_date >= cutoff_date_obj:
                project_number = record.get('ProjectNumber')
                print(f"[INFO] ({i + 1}/{len(all_data_from_search)}) Fetching scope for project: {project_number}")
                scope_of_work = fetch_scope_of_work(session, project_number)

                city_name = record.get('City')
                county_name = record.get('County')
                city_id = LOOKUP.get("CITIES", {}).get(str(city_name)) if city_name else None
                county_id = LOOKUP.get("COUNTIES", {}).get(str(county_name)) if county_name else None

                temp_report_data.append({
                    'ProjectNumber': project_number if project_number else 'N/A',
                    'ProjectName': record.get('ProjectName', 'N/A'),
                    'Date': record_date.isoformat() if record_date else 'N/A',
                    'FacilityName': record.get('FacilityName', 'N/A'),
                    'City': city_id,
                    'County': county_id,
                    'ScopeOfWork': scope_of_work
                })
        report_data = temp_report_data  # Assign to the main report_data variable
        print(f"[INFO] Found {len(report_data)} records matching criteria and processed scope of work.")

        # --- Save newly fetched data to pickle file ---
        if report_data:
            try:
                with open(pickle_filename, 'wb') as f:
                    pickle.dump(report_data, f)
                print(f"[SUCCESS] Report data successfully saved to {pickle_filename}")
            except IOError as e:
                print(f"[ERROR] Failed to save data to pickle file {pickle_filename}: {e}")
        else:
            print("[INFO] No data to save as report_data is empty after fetching.")

    # --- Generate and Display Table using Tabulate ---
    if report_data:
        print("\n--- Project Report ---")
        display_list = []
        combined_strings_for_llm = []

        for i, item in enumerate(report_data):
            project_number = item.get('ProjectNumber', 'N/A')
            scope_of_work = item.get('ScopeOfWork', 'N/A')
            combined_string = f"Project: {project_number}, Scope: {scope_of_work}"
            combined_strings_for_llm.append(combined_string)

            display_item = {
                'No.': i + 1,
                'Project Number': project_number,
                'Project Name': str(item.get('ProjectName', 'N/A'))[:38] + (
                    '...' if len(str(item.get('ProjectName', 'N/A'))) > 38 else ''),
                'Date': item.get('Date', 'N/A'),
                'Facility Name': str(item.get('FacilityName', 'N/A'))[:28] + (
                    '...' if len(str(item.get('FacilityName', 'N/A'))) > 28 else ''),
                'City (ID)': item.get('City') if item.get('City') is not None else 'N/A',
                'County (ID)': item.get('County') if item.get('County') is not None else 'N/A',
                'Scope of Work': scope_of_work
            }
            display_list.append(display_item)

        headers = {
            'No.': 'No.',
            'Project Number': 'Project Number',
            'Project Name': 'Project Name',
            'Date': 'Date',
            'Facility Name': 'Facility Name',
            'City (ID)': 'City (ID)',
            'County (ID)': 'County (ID)',
            'Scope of Work': 'Scope of Work'
        }
        print(tabulate(display_list, headers=headers, tablefmt="grid"))

        # --- Write the consolidated string to a file ---
        if combined_strings_for_llm:
            try:
                with open(combined_string_filename, 'w', encoding='utf-8') as f:
                    for s in combined_strings_for_llm:
                        f.write(s + "\n")
                print(f"\n[SUCCESS] Combined LLM string successfully saved to {combined_string_filename}")
            except IOError as e:
                print(f"\n[ERROR] Failed to save combined LLM string to {combined_string_filename}: {e}")
        else:
            print("\n[INFO] No combined LLM strings to save.")

    else:
        print("\n[INFO] No records to display based on the specified criteria (either from file or after fetching).")

    print("\n[SUCCESS] Report generation finished.")


if __name__ == "__main__":
    main()