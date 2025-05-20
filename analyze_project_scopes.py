import pickle
import os
from collections import Counter
import re
from textwrap import fill

# --- Settings ---
INPUT_FILE = 'project_scopes.pkl'
MIN_WORD_LENGTH = 4  # Minimum length for words to count in frequency analysis
TOP_WORDS = 20  # Number of top frequent words to display


def load_data():
    """Load project scopes from pickle file"""
    if not os.path.exists(INPUT_FILE):
        print(f"[ERROR] Input file {INPUT_FILE} not found. Please run fetch_project_details.py first.")
        return None

    try:
        with open(INPUT_FILE, 'rb') as f:
            data = pickle.load(f)
        return data
    except Exception as e:
        print(f"[ERROR] Failed to load data: {e}")
        return None


def analyze_word_frequency(scopes):
    """Analyze word frequency in all scopes"""
    all_text = ' '.join([s.lower() for s in scopes])

    # Remove common punctuation
    all_text = re.sub(r'[.,;:!?\-\'\"()/]', ' ', all_text)

    # Split into words and count
    words = all_text.split()

    # Filter out short words and common stopwords
    stopwords = {'and', 'the', 'to', 'of', 'in', 'for', 'with', 'on', 'at', 'from', 'by',
                 'this', 'that', 'will', 'new', 'existing', 'area', 'building', 'include', 'includes'}
    filtered_words = [w for w in words if len(w) >= MIN_WORD_LENGTH and w not in stopwords]

    return Counter(filtered_words).most_common(TOP_WORDS)


def print_scopes(data):
    """Print all project scopes in a readable format, with project/facility names and date"""
    if not data:
        return

    # Get scopes, project numbers, project names, facility names, and date
    scopes = []
    for item in data:
        if item.get('success') and item.get('scope_of_work'):
            project_name = item.get('ProjectName', '')
            facility_name = item.get('FacilityName', '')
            project_date = item.get('ProjectCreatedOn', '')  # Default to empty string if missing
            scopes.append((
                item['project_number'], project_name, facility_name, project_date, item['scope_of_work']
            ))

    # Print basic stats
    print(f"\n=== Project Scope Analysis ===")
    print(f"Total projects with scopes: {len(scopes)}")

    # Print scope statistics
    scope_lengths = [len(s[4]) for s in scopes]
    avg_length = sum(scope_lengths) / len(scope_lengths) if scope_lengths else 0
    print(f"Average scope length: {avg_length:.1f} characters")
    print(f"Shortest scope: {min(scope_lengths)} characters")
    print(f"Longest scope: {max(scope_lengths)} characters")

    # Extract just the text for frequency analysis
    scope_texts = [s[4] for s in scopes]
    top_words = analyze_word_frequency(scope_texts)

    # Print top words
    print("\n=== Top Words in Scope Descriptions ===")
    for word, count in top_words:
        print(f"{word}: {count}")

    # Print all scopes with project/facility names and date
    print("\n=== All Project Scopes ===")
    print(f"{'Project Number':<20} {'Project Name':<30} {'Facility Name':<30} {'Date':<12} {'Scope of Work':<60}")
    print(f"{'-' * 19:<20} {'-' * 29:<30} {'-' * 29:<30} {'-' * 11:<12} {'-' * 59:<60}")

    for project_number, project_name, facility_name, project_date, scope in scopes:
        # Wrap text to make it more readable
        wrapped_scope = fill(scope, width=60)
        lines = wrapped_scope.split('\n')

        # Print first line with all columns
        print(f"{project_number:<20} {project_name[:29]:<30} {facility_name[:29]:<30} {project_date[:11]:<12} {lines[0]:<60}")

        # Print remaining scope lines indented under "Scope of Work"
        for line in lines[1:]:
            print(f"{'':<20} {'':<30} {'':<30} {'':<12} {line:<60}")

        print()  # Empty line between projects


def main():
    """Main function to analyze project scopes"""
    data = load_data()
    if data:
        print_scopes(data)
    else:
        print("[ERROR] No data to analyze.")


if __name__ == "__main__":
    main()