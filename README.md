JOB_FINDER_AUTOPILOT
Overview
`JOB_FINDER_AUTOPILOT` is a Python-based job discovery and application
automation project.
The goal is simple:
> Configure your profile and job preferences once, then run the program
> and let it search for jobs, inspect application methods, attempt
> supported applications automatically, record the results, and continue
> to the next opportunity.
The original MVP uses a configurable search API key for job discovery.
Search results are then passed into the application's discovery and
automation pipeline.
Planned workflow
``` text
CONFIGURE PROFILE + JOB PREFERENCES
                ↓
             CLICK RUN
                ↓
        SEARCH FOR JOB OPENINGS
                ↓
      SEARCH API / SEARCH PROVIDER
                ↓
         COLLECT JOB POSTINGS
                ↓
       REMOVE DUPLICATES / TRACK
                ↓
       INSPECT JOB / APPLICATION PAGE
                ↓
    ┌───────────┼───────────┐
    │           │           │
Google Form   HR Email    Website
    │           │           │
Auto-fill     Send        Auto-fill
Resume        Resume      Resume
    │           │           │
    └───────────┴───────────┘
                ↓
   CAPTCHA / LOGIN / UNSUPPORTED?
                ↓
         LOG + SKIP
                ↓
           NEXT JOB
```
What the MVP is designed to do
Search for jobs using configured job roles and locations.
Use a search API key for automated job discovery.
Collect discovered job URLs.
Avoid processing duplicate URLs already stored in the database.
Inspect job pages for application information.
Detect exposed email addresses.
Attempt supported Google Form applications.
Upload the configured resume where supported.
Send resume applications through configured email credentials.
Attempt supported public website application forms.
Record statuses such as:
`Found`
`Processing`
`Applied`
`Sent`
`Manual Required`
`Failed`
Skip CAPTCHA, login, and unsupported flows instead of stopping the
entire run.
Important limitations
This project does not bypass:
CAPTCHA or reCAPTCHA
Login requirements
Two-factor authentication
Website security controls
Anti-bot protections
Platform restrictions
A job application website can have a completely custom structure, so
automatic website application cannot be guaranteed for every company.
Unsupported or restricted cases should be logged and skipped for manual
review.
---
Folder structure
``` text
JOB_FINDER_AUTOPILOT/
│
├── main.py
├── requirements.txt
├── .env
├── config.json
├── database.py
│
├── discovery/
│   ├── __init__.py
│   ├── search.py
│   └── extractor.py
│
├── application/
│   ├── __init__.py
│   ├── browser.py
│   ├── router.py
│   ├── google_forms.py
│   ├── website.py
│   └── email_sender.py
│
├── files/
│   └── resume.pdf
│
└── data/
    └── jobs.db
```
Folder and file purpose
`main.py`
The main entry point for the autopilot.
Running:
``` bash
python main.py
```
starts the complete workflow.
`requirements.txt`
Contains the Python packages required by the project.
`.env`
Stores private configuration values such as:
Search API key
Email address
Email app password
This file should not be committed to GitHub.
`config.json`
Stores the user's application profile and job preferences, including:
Name
Email
Phone number
Location
LinkedIn
GitHub
Portfolio or showreel
Education
Experience
Skills
Target roles
Preferred locations
Maximum jobs per run
`database.py`
Handles the SQLite database used to track jobs and avoid duplicate
processing.
`discovery/`
Contains the job discovery system.
`search.py` --- builds search queries and searches for jobs using
the configured search provider.
`extractor.py` --- inspects discovered job pages for application
links and email addresses.
`application/`
Contains the application automation system.
`browser.py` --- manages the Playwright browser.
`router.py` --- decides which application method to use.
`google_forms.py` --- handles supported Google Forms.
`website.py` --- handles supported website forms.
`email_sender.py` --- sends resume applications by email.
`files/`
Contains application files such as:
``` text
resume.pdf
```
`data/`
Contains generated application data, including the SQLite database:
``` text
jobs.db
```
---
Installation
1. Clone or create the project
Create the project folder:
``` powershell
mkdir JOB_FINDER_AUTOPILOT
cd JOB_FINDER_AUTOPILOT
```
Create the folder structure shown above and place the project Python
files in their respective locations.
2. Create a virtual environment
``` powershell
python -m venv .venv
```
Activate it on Windows PowerShell:
``` powershell
.venv\Scripts\Activate.ps1
```
If PowerShell blocks activation because of execution policy, use the
appropriate PowerShell execution-policy solution for your system, or
activate the environment using another supported terminal.
3. Install Python packages
``` powershell
pip install -r requirements.txt
```
Required packages
The project requires:
``` text
playwright
requests
beautifulsoup4
python-dotenv
```
These should be placed in `requirements.txt`.
Package purpose
Package            Purpose
---
`playwright`       Browser automation for supported application pages
`requests`         HTTP requests to the configured search provider
`beautifulsoup4`   Extracting information from HTML pages
`python-dotenv`    Loading private values from `.env`
4. Install the Playwright browser
After installing Playwright:
``` powershell
python -m playwright install chromium
```
This installs the Chromium browser required by the browser automation
module.
---
Configuration
1. Configure `config.json`
Add your personal application profile and job preferences.
The application uses this information to answer supported form fields
and build job searches.
Examples of information that should be configured:
``` text
Profile
├── Full name
├── First name
├── Last name
├── Email
├── Phone
├── Location
├── LinkedIn
├── GitHub
├── Portfolio / Showreel
├── Education
├── Experience
├── Skills
└── Resume path

Job Preferences
├── Target roles
├── Preferred locations
├── Keywords
├── Maximum jobs per run
└── Auto-submit preference
```
2. Add your resume
Place the resume file in:
``` text
files/resume.pdf
```
The configured resume path must match the actual file location.
3. Configure `.env`
The original MVP uses a search provider API key for automated job
discovery.
Your `.env` should contain:
``` text
SEARCH_API_KEY=YOUR_REAL_SEARCH_API_KEY

JOB_FINDER_EMAIL=your_email@example.com
JOB_FINDER_APP_PASSWORD=your_email_app_password
```
Replace:
``` text
YOUR_REAL_SEARCH_API_KEY
```
with your actual API key from the search provider selected for the
project.
Do not leave the placeholder value:
``` text
PUT_YOUR_SEARCH_API_KEY_HERE
```
Otherwise the search provider will reject the request and job discovery
can return `401 Unauthorized` errors.
The email values are used by the email application module when a
supported opportunity requires sending the resume by email.
---
Running the project
Activate the virtual environment:
``` powershell
.venv\Scripts\Activate.ps1
```
Then run:
``` powershell
python main.py
```
The autopilot will begin its configured workflow.
---
Expected behavior
A typical run is intended to follow this pattern:
``` text
[AUTOPILOT] Starting Job Finder Autopilot...

[AUTOPILOT] Searching for configured roles...

[AUTOPILOT] Discovered job opportunities.

[AUTOPILOT] Inspecting application information...

[AUTOPILOT] Applying through a supported method...

[AUTOPILOT] RESULT: Applied
```
For email applications:
``` text
[AUTOPILOT] RESULT: Sent
```
For restricted or unsupported cases:
``` text
[AUTOPILOT] RESULT: Manual Required
```
The program should then continue to the next discovered job rather than
stopping the complete run.
---
Database and duplicate prevention
The project stores processed job URLs in:
``` text
data/jobs.db
```
This allows the program to check whether a job has already been
processed before attempting it again.
The database can store information such as:
Job URL
Job title
Company
Source
Application status
Additional details
Processing time
---
Security notes
Never upload the following to a public GitHub repository:
``` text
.env
```
The `.env` file may contain private API keys and email credentials.
A `.gitignore` file should eventually include:
``` text
.env
.venv/
__pycache__/
data/*.db
```
Do not share API keys or email app passwords publicly.
---
Project status
This README describes the original autonomous MVP architecture:
``` text
Search API
    ↓
Job Discovery
    ↓
Job Page Extraction
    ↓
Application Router
    ├── Google Forms
    ├── Email
    └── Website Forms
    ↓
SQLite Tracking
```
The code is intentionally kept separate from this README. The README is
documentation for understanding, installing, configuring, and running
the project.

NOTE: You have create an account in any one of the search api and paste the key in .env or else this automation will not work, there are several search api's which give free trial version like bravesearch, searchapi, exa etc.. in this project i used "Tavily" . which gives 1000 free credits every month.