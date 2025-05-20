
# TX Permit Search

A Python-based utility for searching and analyzing construction permit data from the Texas Department of Licensing and Regulation (TDLR) Architectural Barriers (TABS) system.

## Overview

This project provides tools to:
- Authenticate with the TDLR TABS system
- Search for construction projects 
- Fetch permit data for specific project types
- Save and analyze project information

## Components

- **login_session.py**: Handles authentication to the TDLR TABS system using credentials stored in a .env file
- **search.py**: Basic implementation for searching construction projects in the TABS database
- **fetch_tabs_projects.py**: Fetches multiple pages of project data and saves them to a pickle file
- **analyze_tabs_projects.py**: Loads and analyzes saved project data, displaying project names sorted alphabetically

## Setup

1. Clone the repository
2. Create a `.env` file in the project root with your TDLR account credentials:
   ```
   Email=your_email@example.com
   Password=your_password
   ```
3. Install required dependencies (requests, python-dotenv)

## Usage

### Authentication
Run the login script to establish a session:

#### python login_session.py
This will create a cookies.txt file to maintain your session.

### Search Projects
To perform a basic search for projects:

#### python search.py

### Fetch Multiple Projects
To fetch and save multiple projects (filtered by TypeOfWork=9001 which is New Construction):

#### python fetch_tabs_projects.py

This will save the data to `tabs_projects_9001.pkl`.

### Analyze Project Data
To analyze the fetched project data:

#### python analyze_tabs_projects.py

This will display project names sorted alphabetically with their creation dates.

## Configuration

- `RECORD_LIMIT`: Maximum number of records to fetch (default: 1000)
- `PAGE_SIZE`: Number of records per page (default: 100)
- `TYPE_OF_WORK`: Project type filter code (default: 9001)

## Files

- `cookies.txt`: Stores session cookies for authentication
- `tabs_projects_9001.pkl`: Pickle file containing fetched project data

## Notes

This tool is designed for data analysis purposes and requires valid TDLR TABS credentials. You can obtain valid 
credentials by visiting TLDR website and signing up as a Tenant. 
