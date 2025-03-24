#!/usr/bin/env python
"""
indeed.py

Main entry point for Indeed Job Application Automation.
"""

from indeed_backend import apply_to_jobs

if __name__ == "__main__":

    role = "Software Development Engineer"
    location = "United States"
    # You can customize the job title and location below or parse command-line args.
    apply_to_jobs(role, location)
