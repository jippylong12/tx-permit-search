import pickle
import os
from tabulate import tabulate
from datetime import datetime
import json


def print_pickle_search_data(filename,
                             filter_counties=None,
                             filter_terms=None,
                             output_format='table',
                             save_to_file=None,
                             show_stats=True):
    """
    Print the entire search data from a pickle file with optional filtering and formatting.

    Args:
        filename (str): Path to the pickle file
        filter_counties (list, optional): List of county names to filter by
        filter_terms (list, optional): List of terms to search in project names, facility names, and scope
        output_format (str): Output format - 'table', 'json', 'simple', or 'detailed'
        save_to_file (str, optional): If provided, save output to this file
        show_stats (bool): Whether to show statistics summary
    """

    # Check if file exists
    if not os.path.exists(filename):
        print(f"[ERROR] File {filename} not found.")
        return

    try:
        # Load the pickle data
        with open(filename, 'rb') as f:
            data = pickle.load(f)

        print(f"[INFO] Successfully loaded {len(data)} records from {filename}")

        # Apply filters if specified
        filtered_data = data

        if filter_counties:
            filtered_data = [item for item in filtered_data
                             if item.get('County') in filter_counties]
            print(f"[INFO] Filtered by counties {filter_counties}: {len(filtered_data)} records")

        if filter_terms:
            def matches_terms(item):
                search_text = f"{item.get('ProjectName', '')} {item.get('FacilityName', '')} {item.get('ScopeOfWork', '')}".lower()
                return any(term.lower() in search_text for term in filter_terms)

            filtered_data = [item for item in filtered_data if matches_terms(item)]
            print(f"[INFO] Filtered by terms {filter_terms}: {len(filtered_data)} records")

        # Show statistics if requested
        if show_stats:
            print_statistics(filtered_data)

        # Format and display output
        output_text = format_output(filtered_data, output_format)
        print(output_text)

        # Save to file if requested
        if save_to_file:
            try:
                with open(save_to_file, 'w', encoding='utf-8') as f:
                    f.write(f"Search Data from: {filename}\n")
                    f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Total records: {len(data)}\n")
                    f.write(f"Filtered records: {len(filtered_data)}\n")
                    if filter_counties:
                        f.write(f"County filter: {filter_counties}\n")
                    if filter_terms:
                        f.write(f"Search terms: {filter_terms}\n")
                    f.write("\n" + "=" * 80 + "\n\n")
                    f.write(output_text)
                print(f"[SUCCESS] Output saved to {save_to_file}")
            except Exception as e:
                print(f"[ERROR] Failed to save to file: {e}")

    except Exception as e:
        print(f"[ERROR] Failed to load pickle file: {e}")


def print_statistics(data):
    """Print statistical summary of the data"""
    if not data:
        print("[INFO] No data to analyze")
        return

    print(f"\n{'=' * 50}")
    print(f"STATISTICS SUMMARY")
    print(f"{'=' * 50}")
    print(f"Total records: {len(data)}")

    # County distribution
    counties = {}
    for item in data:
        county = item.get('County', 'N/A')
        counties[county] = counties.get(county, 0) + 1

    if counties:
        print(f"\nCounty distribution:")
        for county, count in sorted(counties.items(), key=lambda x: x[1], reverse=True):
            print(f"  {county}: {count}")

    # Date range
    dates = []
    for item in data:
        date_str = item.get('Date')
        if date_str and date_str != 'N/A':
            dates.append(date_str)

    if dates:
        dates.sort()
        print(f"\nDate range: {dates[0]} to {dates[-1]}")

    # Projects with scope vs without
    with_scope = sum(1 for item in data if item.get('ScopeOfWork') and item.get('ScopeOfWork') != 'N/A')
    print(f"\nProjects with scope of work: {with_scope} / {len(data)}")

    print(f"{'=' * 50}\n")


def format_output(data, format_type):
    """Format the data according to the specified format"""
    if not data:
        return "[INFO] No data to display"

    if format_type == 'json':
        return json.dumps(data, indent=2, ensure_ascii=False)

    elif format_type == 'simple':
        output = []
        for i, item in enumerate(data, 1):
            output.append(f"{i}. {item.get('ProjectNumber', 'N/A')} - {item.get('ProjectName', 'N/A')}")
        return '\n'.join(output)

    elif format_type == 'detailed':
        output = []
        for i, item in enumerate(data, 1):
            output.append(f"\n{'=' * 80}")
            output.append(f"PROJECT {i}")
            output.append(f"{'=' * 80}")
            output.append(f"Project Number: {item.get('ProjectNumber', 'N/A')}")
            output.append(f"Project Name: {item.get('ProjectName', 'N/A')}")
            output.append(f"Date: {item.get('Date', 'N/A')}")
            output.append(f"Facility Name: {item.get('FacilityName', 'N/A')}")
            output.append(f"City: {item.get('City', 'N/A')}")
            output.append(f"County: {item.get('County', 'N/A')}")
            output.append(f"Scope of Work: {item.get('ScopeOfWork', 'N/A')}")
        return '\n'.join(output)

    else:  # table format (default)
        table_data = []
        for i, item in enumerate(data, 1):
            # Truncate long text for table display
            project_name = str(item.get('ProjectName', 'N/A'))

            facility_name = str(item.get('FacilityName', 'N/A'))

            scope = str(item.get('ScopeOfWork', 'N/A'))
            table_data.append({
                'No.': i,
                'Project #': item.get('ProjectNumber', 'N/A'),
                'Project Name': project_name,
                'Date': item.get('Date', 'N/A'),
                'Facility': facility_name,
                'City': item.get('City', 'N/A'),
                'County': item.get('County', 'N/A'),
                'Scope': scope
            })

        return tabulate(table_data, headers='keys', tablefmt='grid')


# Convenience functions for common use cases
def print_all_projects(filename):
    """Print all projects from pickle file in table format"""
    print_pickle_search_data(filename)


def print_county_projects(filename, counties):
    """Print projects filtered by county"""
    print_pickle_search_data(filename, filter_counties=counties)


def print_ev_projects(filename):
    """Print projects related to EV charging"""
    ev_terms = ['electric vehicle', 'ev charging', 'charger', 'tesla', 'supercharger']
    print_pickle_search_data(filename, filter_terms=ev_terms)


def search_projects(filename, search_terms):
    """Search projects by terms"""
    print_pickle_search_data(filename, filter_terms=search_terms)


# Example usage
if __name__ == "__main__":
    # Example calls - replace with your actual pickle file path
    pickle_file = "output_data/project_report_data_2025-08-18_cutoff_2025_07_17.pkl"

    # Print all data
    # print_all_projects(pickle_file)

    # Print with filters
    print_county_projects(pickle_file, ['Martin', 'Midland', 'Ector'])
    # print_ev_projects(pickle_file)
    # search_projects(pickle_file, ['solar', 'renewable'])
    # search_projects(pickle_file, ['charg'])

    # Advanced usage with all parameters
    # print_pickle_search_data(
    #     filename=pickle_file,
    #     filter_counties=['Martin', 'Midland'],
    #     filter_terms=['charging', 'electric'],
    #     output_format='detailed',
    #     save_to_file='filtered_results.txt',
    #     show_stats=True
    # )