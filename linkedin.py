"""
linkedin.py

Front-end script for LinkedIn Job Application Automation.

This script gathers user inputs and invokes the backend module to perform the automated
job search and application process on LinkedIn.

Usage:
    python linkedin.py [--debug]

The optional --debug flag sets the logging level to DEBUG, so detailed process information
will be printed to the console.
"""

import argparse
import logging
from linkedin_backend import apply_to_jobs

def main() -> None:
    """
    Main entry point for the LinkedIn Job Application Automation script.

    Parses command-line arguments to optionally enable debug logging, then starts
    the job application process using preset parameters.
    """
    parser = argparse.ArgumentParser(description="LinkedIn Job Application Automation")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        print("Debug mode enabled. Detailed process will be printed to the console.")
    else:
        logging.getLogger().setLevel(logging.INFO)
    
    print("Welcome to LinkedIn Job Application Automation!")
    
    # Hardcoded parameters for demonstration.
    job_title = "Software Development Engineer"
    location = "United States"
    auto_apply = True
    
    print(f"Searching for '{job_title}' jobs in '{location}' with auto-apply set to {auto_apply}.\n")
    
    apply_to_jobs(job_title, location, auto_apply)

if __name__ == '__main__':
    main()
