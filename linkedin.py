"""
linkedin.py

Front-end script for the Job Application Automation on LinkedIn.
This script gathers user inputs (job title, location, auto-apply option) and then
calls the backend module to perform the automation.
"""

from backend import apply_to_jobs

def main():
    print("Welcome to LinkedIn Job Application Automation!")
    
    # For this example, the job title, location, and auto-apply flag are hardcoded.
    job_title = "Software Development Engineer"
    location = "United States"
    auto_apply = True
    
    print(f"Searching for '{job_title}' jobs in '{location}' with auto-apply set to {auto_apply}.\n")
    
    apply_to_jobs(job_title, location, auto_apply)

if __name__ == '__main__':
    main()
