import os
import pickle
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re
from tqdm import tqdm

# --- Settings ---
INPUT_FILE = 'tabs_projects_9001.pkl'
OUTPUT_FILE = 'project_scopes.pkl'
MAX_PROJECTS = 5000  # Maximum number of projects to process from the input file
MAX_CONCURRENT_REQUESTS = 50  # Maximum number of concurrent async requests


async def fetch_project_details(session, project_number, semaphore, ref=None):
    """Fetch project details page and extract the scope of work plus project meta info."""
    url = f"https://www.tdlr.texas.gov/TABS/Search/Project/{project_number}"

    async with semaphore:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')

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

    projects = projects[:MAX_PROJECTS]
    print(f"[INFO] Processing {len(projects)} projects")

    # Prepare project meta dicts for each project
    project_refs = [
        {
            "ProjectNumber": proj.get("ProjectNumber"),
            "ProjectName": proj.get("ProjectName"),
            "ProjectCreatedOn": proj.get("ProjectCreatedOn"),
            "FacilityName": proj.get("FacilityName"),
            "City": proj.get("City"),
            "County": proj.get("County"),
        }
        for proj in projects
        if proj.get("ProjectNumber")
    ]

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    results = []
    async with aiohttp.ClientSession() as session:
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
    print(f"Success rate: {len(results)}/{len(project_refs)} = {len(results) / len(project_refs) * 100:.2f}%")


if __name__ == "__main__":
    asyncio.run(main())