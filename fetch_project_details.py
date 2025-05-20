import os
import pickle
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re
from tqdm import tqdm
import lxml

# --- Settings ---
INPUT_FILE = 'tabs_projects_9001.pkl'
OUTPUT_FILE = 'project_scopes.pkl'
MAX_PROJECTS = 500  # Maximum number of projects to process from the input file
# Experiment with this value, e.g., 50, 75, 100.
# Be cautious of server limits.
MAX_CONCURRENT_REQUESTS = 50  # Increased for example


async def fetch_project_details(session, project_number, semaphore, ref=None):
    """Fetch project details page and extract the scope of work plus project meta info."""
    url = f"https://www.tdlr.texas.gov/TABS/Search/Project/{project_number}"

    async with semaphore:
        try:
            # Consider adding a timeout to the session.get() call if needed
            # timeout = aiohttp.ClientTimeout(total=60) # 60 seconds total timeout
            # async with session.get(url, timeout=timeout) as response:
            async with session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    # Use lxml parser for better performance
                    # Ensure you have lxml installed: pip install lxml
                    soup = BeautifulSoup(html, 'lxml')

                    # Find Scope of Work
                    scope_dt = soup.find('dt', string=re.compile(r'Scope of Work:', re.IGNORECASE))
                    scope_text = None
                    if scope_dt:
                        scope_dd = scope_dt.find_next('dd')
                        if scope_dd:
                            scope_text = scope_dd.text.strip()

                    d = {
                        "project_number": project_number,
                        "scope_of_work": scope_text,
                        "success": True,
                    }

                    # Add ONLY the requested camelCase keys
                    if ref:
                        d["ProjectName"] = ref.get("ProjectName")
                        d["ProjectCreatedOn"] = ref.get("ProjectCreatedOn")
                        d["FacilityName"] = ref.get("FacilityName")
                        d["City"] = ref.get("City")
                        d["County"] = ref.get("County")

                    return d
                else:
                    return {
                        "project_number": project_number,
                        "scope_of_work": None,
                        "success": False,
                        "error": f"HTTP {response.status}"
                    }
        except asyncio.TimeoutError: # Example of handling timeout
            return {
                "project_number": project_number,
                "scope_of_work": None,
                "success": False,
                "error": "Request timed out"
            }
        except Exception as e:
            return {
                "project_number": project_number,
                "scope_of_work": None,
                "success": False,
                "error": str(e)
            }

async def main():
    try:
        with open(INPUT_FILE, 'rb') as f:
            projects = pickle.load(f)
        print(f"[INFO] Loaded {len(projects)} projects from {INPUT_FILE}")
    except Exception as e:
        print(f"[ERROR] Failed to load projects: {e}")
        return

    projects_to_process = projects[:MAX_PROJECTS]
    print(f"[INFO] Processing {len(projects_to_process)} projects")

    project_refs = [
        {
            "ProjectNumber": proj.get("ProjectNumber"),
            "ProjectName": proj.get("ProjectName"),
            "ProjectCreatedOn": proj.get("ProjectCreatedOn"),
            "FacilityName": proj.get("FacilityName"),
            "City": proj.get("City"),
            "County": proj.get("County"),
        }
        for proj in projects_to_process # Ensure we use the sliced list
        if proj.get("ProjectNumber")
    ]

    if not project_refs:
        print("[INFO] No projects to process after filtering.")
        return

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    results = []

    # Configure TCPConnector
    # Set limit to be at least MAX_CONCURRENT_REQUESTS
    # Set limit_per_host to be at least MAX_CONCURRENT_REQUESTS for a single-site scraper
    connector = aiohttp.TCPConnector(limit=MAX_CONCURRENT_REQUESTS * 2, limit_per_host=MAX_CONCURRENT_REQUESTS)
    
    # Define a client timeout (optional, but good practice)
    timeout = aiohttp.ClientTimeout(total=60) # e.g., 60 seconds for the entire request including connection

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        tasks = [
            fetch_project_details(session, ref["ProjectNumber"], semaphore, ref=ref)
            for ref in project_refs
        ]

        for future in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Fetching project details"):
            result = await future
            if result.get("success"):
                results.append(result)
            else:
                print(f"[WARN] Failed for {result.get('project_number')}: {result.get('error', 'Unknown error')}")

    with open(OUTPUT_FILE, 'wb') as f:
        pickle.dump(results, f)

    print(f"[SUCCESS] Saved {len(results)} project scopes to {OUTPUT_FILE}")
    if len(project_refs) > 0:
        success_rate = len(results) / len(project_refs) * 100
        print(f"Success rate: {len(results)}/{len(project_refs)} = {success_rate:.2f}%")
    else:
        print("No projects were processed to calculate a success rate.")


if __name__ == "__main__":
    asyncio.run(main())