import pickle
from datetime import datetime

# File to load
PICKLE_FILE = 'tabs_projects_9001.pkl'

# Load the data
with open(PICKLE_FILE, 'rb') as f:
    projects = pickle.load(f)

# Extract (name, date) tuples
name_date_pairs = []
for project in projects:
    name = project.get('ProjectName', 'Unnamed')
    date_raw = project.get('ProjectCreatedOn', '')
    try:
        date = datetime.fromisoformat(date_raw).date()
    except Exception:
        date = "Unknown"
    name_date_pairs.append((name, date))

# Sort alphabetically by name
name_date_pairs.sort(key=lambda x: x[0].lower())

# Print the list
print("[INFO] Project Names with Dates:")
for name, date in name_date_pairs:
    print(f" - {name} ({date})")