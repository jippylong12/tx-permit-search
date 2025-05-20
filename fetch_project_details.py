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


async def fetch_project_details(session, project_number, semaphore):
    """Fetch project details page and extract the scope of work"""
    url = f"https://www.tdlr.texas.gov/TABS/Search/Project/{project_number}"

    async with semaphore:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    # Find the Scope of Work element
                    # Look for the dt element with text 'Scope of Work:'
                    scope_dt = soup.find('dt', string=re.compile(r'Scope of Work:', re.IGNORECASE))

                    if scope_dt:
                        # Get the next dd element which contains the scope of work text
                        scope_dd = scope_dt.find_next('dd')
                        if scope_dd:
                            scope_text = scope_dd.text.strip()
                            return {
                                'project_number': project_number,
                                'scope_of_work': scope_text,
                                'success': True
                            }

                    return {
                        'project_number': project_number,
                        'scope_of_work': None,
                        'success': False,
                        'error': 'Scope of work not found'
                    }
                else:
                    return {
                        'project_number': project_number,
                        'scope_of_work': None,
                        'success': False,
                        'error': f'HTTP {response.status}'
                    }
        except Exception as e:
            return {
                'project_number': project_number,
                'scope_of_work': None,
                'success': False,
                'error': str(e)
            }


async def main():
    # Load projects from the pickle file
    try:
        with open(INPUT_FILE, 'rb') as f:
            projects = pickle.load(f)
        print(f"[INFO] Loaded {len(projects)} projects from {INPUT_FILE}")
    except Exception as e:
        print(f"[ERROR] Failed to load projects: {e}")
        return

    # Limit the number of projects if needed
    projects = projects[:MAX_PROJECTS]
    print(f"[INFO] Processing {len(projects)} projects")

    # Extract project numbers
    project_numbers = [project.get('ProjectNumber') for project in projects
                       if project.get('ProjectNumber')]

    # Create a semaphore to limit the number of concurrent requests
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    # Create results list
    results = []

    # Create async session and tasks
    async with aiohttp.ClientSession() as session:
        tasks = []
        for project_number in project_numbers:
            task = fetch_project_details(session, project_number, semaphore)
            tasks.append(task)

        # Use tqdm to show progress
        for future in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Fetching project details"):
            result = await future
            if result['success']:
                results.append(result)
            else:
                print(f"[WARN] Failed for {result['project_number']}: {result.get('error', 'Unknown error')}")

    # Save results to pickle file
    with open(OUTPUT_FILE, 'wb') as f:
        pickle.dump(results, f)

    print(f"[SUCCESS] Saved {len(results)} project scopes to {OUTPUT_FILE}")
    print(f"Success rate: {len(results)}/{len(project_numbers)} = {len(results) / len(project_numbers) * 100:.2f}%")


if __name__ == "__main__":
    asyncio.run(main())