"""
tracker_updater.py

Module to update a Google Sheet with job application details.

This module uses the editable Google Sheet URL provided in secrets.config under the key
"spreadsheet_tracker". The sheet must be publicly editable ("Anyone with the link can edit").
It attempts to use gspread in unauthenticated mode (by passing an empty credentials dictionary)
to append a new row to the first worksheet.

If updating the Google Sheet fails (or if no URL is provided), this module falls back to
updating a CSV file (Resources/applications_tracker.csv) with the application details.

Expected columns (in both the Google Sheet and CSV):
  Company Name, Job Title, Job Level, Salary Range, Application Link, Status

Usage:
    Import the update_tracker function from this module and call it with the appropriate parameters.
    Or run this module directly for testing.
"""

import csv
import logging
import os
from typing import List, Any

import requests
import gspread

# Configure logging.
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


def read_secrets(file_path: str = "secrets.config") -> dict:
    """
    Reads configuration values from a secrets file.

    The file should contain lines in the following format:
        key=value

    Expected to include:
      - spreadsheet_tracker: The editable URL of the Google Sheet.

    Args:
        file_path (str): Path to the secrets configuration file.

    Returns:
        dict: Dictionary of key/value pairs.
    """
    secrets = {}
    try:
        with open(file_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and "=" in line:
                    key, value = line.split("=", 1)
                    secrets[key.strip()] = value.strip()
        logger.info("Secrets file '%s' read successfully.", file_path)
    except Exception as e:
        logger.error("Error reading secrets file '%s': %s", file_path, e)
    return secrets


def update_google_sheet(new_row: List[Any], sheet_url: str) -> bool:
    """
    Attempts to update the Google Sheet via the provided URL.

    Uses gspread in unauthenticated mode by passing an empty credentials dictionary,
    and a custom requests session. The sheet must be publicly editable.

    Args:
        new_row (List[Any]): The row data to append.
        sheet_url (str): The editable Google Sheet URL.

    Returns:
        bool: True if the update succeeds, False otherwise.
    """
    try:
        session = requests.Session()
        session.headers.update({"User-Agent": "Mozilla/5.0"})
        # Pass an empty dictionary for credentials.
        gc = gspread.Client(auth={})
        gc.session = session

        sheet = gc.open_by_url(sheet_url).sheet1
        sheet.append_row(new_row)
        logger.info("Google Sheet updated successfully with row: %s", new_row)
        return True
    except Exception as e:
        logger.error("Error updating Google Sheet: %s", e)
        return False


def update_csv_tracker(new_row: List[Any]) -> None:
    """
    Updates the local CSV file with application information.

    The CSV file is located at Resources/applications_tracker.csv. If the file does not exist,
    it will be created with the appropriate header.

    Args:
        new_row (List[Any]): The row data to append.
    """
    csv_path = os.path.abspath(os.path.join("Resources", "applications_tracker.csv"))
    file_exists = os.path.isfile(csv_path)
    try:
        with open(csv_path, "a", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            if not file_exists:
                writer.writerow(["Company Name", "Job Title", "Job Level", "Salary Range", "Application Link", "Status"])
            writer.writerow(new_row)
        logger.info("Local CSV tracker updated successfully with row: %s", new_row)
    except Exception as e:
        logger.error("Error updating local CSV tracker: %s", e)


def update_tracker(company: str, job_title: str, job_level: str, salary_range: str,
                   application_link: str, status: str) -> None:
    """
    Updates the tracker with application information.

    First, the function checks for an editable Google Sheet URL in secrets.config.
    If a URL is provided, it attempts to update the Google Sheet. If the update fails
    (or no URL is provided), it falls back to updating a local CSV file (Resources/applications_tracker.csv).

    Args:
        company (str): The company name.
        job_title (str): The job title.
        job_level (str): The job level.
        salary_range (str): The salary range.
        application_link (str): URL of the application.
        status (str): Application status.
    """
    new_row: List[Any] = [company, job_title, job_level, salary_range, application_link, status]
    secrets = read_secrets()
    sheet_url = secrets.get("spreadsheet_tracker", "")
    
    if sheet_url:
        logger.info("Attempting to update Google Sheet using the provided URL.")
        success = update_google_sheet(new_row, sheet_url)
        if not success:
            logger.info("Falling back to local CSV tracker update.")
            update_csv_tracker(new_row)
    else:
        logger.info("No spreadsheet_tracker URL provided in secrets.config; updating local CSV tracker.")
        update_csv_tracker(new_row)


if __name__ == "__main__":
    # For testing purposes.
    update_tracker(
        company="Test Company",
        job_title="Software Engineer",
        job_level="Entry Level",
        salary_range="$100,000 - $120,000",
        application_link="https://example.com/apply/123",
        status="Applied"
    )
