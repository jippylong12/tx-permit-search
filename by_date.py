import os
import re
import requests
from http.cookiejar import MozillaCookieJar
from datetime import datetime, date
from constants import LOOKUP  # Import the LOOKUP dictionary
import pickle
from bs4 import BeautifulSoup
from tabulate import tabulate
import json

# --- Settings ---
CUTOFF_DATE_STR = '2025-11-25'
COOKIE_FILE = 'cookies.txt'
SEARCH_URL = 'https://www.tdlr.texas.gov/TABS/Search/SearchProjects'
PAGE_SIZE = 100
TYPE_OF_WORK = ''
OUTPUT_DATA_FOLDER = 'output_data'  # Folder to store pickle files
CHECKPOINT_INTERVAL = 100  # Save progress every 100 records


# --- Global headers for requests ---
REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}


def get_checkpoint_files(base_name):
    """Generate checkpoint file names"""
    return {
        'progress': f"{base_name}_progress.json",
        'processed_data': f"{base_name}_processed.pkl",
        'remaining_ids': f"{base_name}_remaining_ids.pkl"
    }


def save_checkpoint(checkpoint_files, processed_data, remaining_project_ids, current_index, total_count):
    """Save current progress to checkpoint files"""
    try:
        # Save progress metadata
        progress_data = {
            'current_index': current_index,
            'total_count': total_count,
            'processed_count': len(processed_data),
            'remaining_count': len(remaining_project_ids),
            'timestamp': datetime.now().isoformat()
        }

        with open(checkpoint_files['progress'], 'w') as f:
            json.dump(progress_data, f, indent=2)

        # Save processed data
        with open(checkpoint_files['processed_data'], 'wb') as f:
            pickle.dump(processed_data, f)

        # Save remaining project IDs
        with open(checkpoint_files['remaining_ids'], 'wb') as f:
            pickle.dump(remaining_project_ids, f)

        print(f"[CHECKPOINT] Progress saved: {len(processed_data)} processed, {len(remaining_project_ids)} remaining")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to save checkpoint: {e}")
        return False


def load_checkpoint(checkpoint_files):
    """Load progress from checkpoint files"""
    try:
        if not os.path.exists(checkpoint_files['progress']):
            return None, None, None, None, None

        with open(checkpoint_files['progress'], 'r') as f:
            progress_data = json.load(f)

        with open(checkpoint_files['processed_data'], 'rb') as f:
            processed_data = pickle.load(f)

        with open(checkpoint_files['remaining_ids'], 'rb') as f:
            remaining_project_ids = pickle.load(f)

        current_index = progress_data['current_index']
        total_count = progress_data['total_count']

        print(f"[RESUME] Found checkpoint: {len(processed_data)} processed, {len(remaining_project_ids)} remaining")
        print(f"[RESUME] Checkpoint created at: {progress_data['timestamp']}")

        return processed_data, remaining_project_ids, current_index, total_count, progress_data
    except Exception as e:
        print(f"[ERROR] Failed to load checkpoint: {e}")
        return None, None, None, None, None


def cleanup_checkpoint_files(checkpoint_files):
    """Remove checkpoint files after successful completion"""
    try:
        for file_path in checkpoint_files.values():
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"[CLEANUP] Removed checkpoint file: {file_path}")
    except Exception as e:
        print(f"[WARNING] Failed to cleanup some checkpoint files: {e}")


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
        'columns[10][data]': 'DataVersionId', 'columns[10][name]': '', 'columns[10][searchable]': 'true',
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




# --- Function to get county name from ID ---
def get_county_name_from_id(county_id):
    """Get county name from county ID using reverse lookup"""
    if county_id is None:
        return 'N/A'

    for name, id_val in LOOKUP.get("COUNTIES", {}).items():
        if str(id_val) == str(county_id):
            return name
    return 'N/A'


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

    # --- Define file names ---
    today_str = datetime.now().strftime('%Y-%m-%d')
    cutoff_date_filename_part = CUTOFF_DATE_STR.replace('-', '_')

    base_filename = f'project_report_data_{today_str}_cutoff_{cutoff_date_filename_part}'
    pickle_filename = os.path.join(OUTPUT_DATA_FOLDER, f'{base_filename}.pkl')
    combined_string_filename = os.path.join(OUTPUT_DATA_FOLDER,
                                            f'combined_projects_for_llm_{today_str}_cutoff_{cutoff_date_filename_part}.txt')

    # Get checkpoint file names
    checkpoint_files = get_checkpoint_files(os.path.join(OUTPUT_DATA_FOLDER, base_filename))

    # --- Check for existing complete data ---
    if os.path.exists(pickle_filename):
        print(f"[INFO] Found existing complete data file: {pickle_filename}")
        try:
            with open(pickle_filename, 'rb') as f:
                report_data = pickle.load(f)
            print(f"[INFO] Successfully loaded {len(report_data)} records from file.")

            # Clean up any leftover checkpoint files
            cleanup_checkpoint_files(checkpoint_files)

            # Skip to display section
            display_results(report_data, combined_string_filename)
            return
        except Exception as e:
            print(f"[ERROR] Failed to load data from {pickle_filename}: {e}. Will attempt to re-fetch.")

    # --- Check for checkpoint data ---
    processed_data, remaining_project_ids, current_index, total_count, progress_info = load_checkpoint(checkpoint_files)

    if processed_data is not None and remaining_project_ids is not None:
        # Resume from checkpoint
        print(f"[RESUME] Resuming from checkpoint...")
        user_input = input("Do you want to resume from the checkpoint? (y/n): ").lower().strip()
        if user_input != 'y':
            print("[INFO] Starting fresh (checkpoint files will be overwritten)")
            processed_data = None

    if processed_data is None:
        # Start fresh - fetch all project IDs first
        print("[INFO] Starting fresh data fetch...")
        start = 0

        # Parse cutoff date once before fetching
        try:
            cutoff_date_obj = datetime.strptime(CUTOFF_DATE_STR, '%Y-%m-%d').date()
            print(f"[INFO] Will fetch records until going past cutoff date: {cutoff_date_obj.isoformat()}")
        except ValueError:
            print(f"[ERROR] Invalid CUTOFF_DATE_STR: '{CUTOFF_DATE_STR}'. Please use 'YYYY-MM-DD' format.")
            return

        remaining_project_ids = []
        reached_cutoff = False

        while not reached_cutoff:
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

            # Add only records on/after cutoff and stop when we reach older ones
            for record in new_data:
                project_created_on_str = record.get('ProjectCreatedOn')
                record_date = parse_tdlr_date_str(project_created_on_str)
                if record_date is None:
                    continue
                if record_date >= cutoff_date_obj:
                    remaining_project_ids.append(record)
                else:
                    reached_cutoff = True
                    break

            if reached_cutoff:
                print("[INFO] Reached records older than cutoff date. Stopping fetch.")
                break

            if len(new_data) < PAGE_SIZE:
                print("[INFO] Fetched all available data within the current query page size.")
                break

            start += PAGE_SIZE

        processed_data = []
        current_index = 0
        total_count = len(remaining_project_ids)

        print(f"[INFO] Found {total_count} records on/after cutoff date. Starting to process...")

    # Process remaining projects with checkpointing
    try:
        for i, record in enumerate(remaining_project_ids):
            actual_index = current_index + i
            project_number = record.get('ProjectNumber')

            print(f"[INFO] ({actual_index + 1}/{total_count}) Fetching scope for project: {project_number}")

            scope_of_work = fetch_scope_of_work(session, project_number)

            project_created_on_str = record.get('ProjectCreatedOn')
            record_date = parse_tdlr_date_str(project_created_on_str)

            city_name = record.get('City')
            county_name = record.get('County')
            city_id = LOOKUP.get("CITIES", {}).get(str(city_name)) if city_name else None
            county_id = LOOKUP.get("COUNTIES", {}).get(str(county_name)) if county_name else None

            processed_item = {
                'ProjectNumber': project_number if project_number else 'N/A',
                'ProjectName': record.get('ProjectName', 'N/A'),
                'Date': record_date.isoformat() if record_date else 'N/A',
                'FacilityName': record.get('FacilityName', 'N/A'),
                'City': city_id,
                'County': county_id,
                'CountyName': county_name,  # Keep original county name for filtering
                'ScopeOfWork': scope_of_work
            }

            processed_data.append(processed_item)

            # Save checkpoint every CHECKPOINT_INTERVAL records
            if (i + 1) % CHECKPOINT_INTERVAL == 0:
                remaining_for_checkpoint = remaining_project_ids[i + 1:]  # Remaining items after current
                save_checkpoint(checkpoint_files, processed_data, remaining_for_checkpoint, actual_index + 1,
                                total_count)

        # Processing completed successfully
        print(f"[SUCCESS] Processing completed! Processed {len(processed_data)} records.")

        # Save final data to main pickle file
        with open(pickle_filename, 'wb') as f:
            pickle.dump(processed_data, f)
        print(f"[SUCCESS] Report data successfully saved to {pickle_filename}")

        # Clean up checkpoint files
        cleanup_checkpoint_files(checkpoint_files)

    except KeyboardInterrupt:
        print("\n[INFO] Process interrupted by user. Saving checkpoint...")
        remaining_for_checkpoint = remaining_project_ids[i:]  # Current item and remaining
        save_checkpoint(checkpoint_files, processed_data, remaining_for_checkpoint, actual_index, total_count)
        print("[INFO] Checkpoint saved. You can resume later by running the script again.")
        return
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}. Saving checkpoint...")
        remaining_for_checkpoint = remaining_project_ids[i:]  # Current item and remaining
        save_checkpoint(checkpoint_files, processed_data, remaining_for_checkpoint, actual_index, total_count)
        print("[ERROR] Checkpoint saved. You can resume later by running the script again.")
        return

    # Display results
    display_results(processed_data, combined_string_filename)


def display_results(report_data, combined_string_filename):
    """Display and save the final results"""
    if report_data:
        print("\n--- Complete Project Report (All Data) ---")
        print(f"Total records in dataset: {len(report_data)}")

        # Build combined strings for ALL records (filtering handled by print_out.py)
        combined_strings_for_llm = []
        for item in report_data:
            project_number = item.get('ProjectNumber', 'N/A')
            scope_of_work = item.get('ScopeOfWork', 'N/A')
            combined_strings_for_llm.append(f"Project: {project_number}, Scope: {scope_of_work}")

        # --- Write the consolidated string to a file (ALL DATA) ---
        if combined_strings_for_llm:
            try:
                with open(combined_string_filename, 'w', encoding='utf-8') as f:
                    for s in combined_strings_for_llm:
                        f.write(s + "\n")
                print(
                    f"\n[SUCCESS] Combined LLM string (ALL {len(combined_strings_for_llm)} records) successfully saved to {combined_string_filename}")
            except IOError as e:
                print(f"\n[ERROR] Failed to save combined LLM string to {combined_string_filename}: {e}")
        else:
            print("\n[INFO] No combined LLM strings to save.")
    else:
        print("\n[INFO] No records to display.")

    print("\n[SUCCESS] Report generation finished.")


if __name__ == "__main__":
    main()