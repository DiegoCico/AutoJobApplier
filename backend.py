"""
backend.py

Backend module that handles the automation of job search and application on LinkedIn.
It uses Selenium to open Safari, log in to LinkedIn using credentials from a secrets.config file,
navigate to LinkedIn Jobs, search for the specified job title and location, and then attempt to 
automatically apply using the 'Easy Apply' feature when available.

If no resume is attached on LinkedIn, the script will try to attach a resume from Resources/resume.pdf.
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import os

def read_secrets(file_path="secrets.config"):
    """
    Reads the secrets.config file and returns a dictionary of credentials.
    Expected format:
        username=your_email@example.com
        password=your_password
    """
    secrets = {}
    try:
        with open(file_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and "=" in line:
                    key, value = line.split("=", 1)
                    secrets[key.strip()] = value.strip()
    except Exception as e:
        print("Error reading secrets.config:", e)
    return secrets

def login_to_linkedin(driver):
    """
    Logs in to LinkedIn using credentials from the secrets.config file.
    """
    secrets = read_secrets()
    username = secrets.get("username")
    password = secrets.get("password")
    
    if not username or not password:
        raise Exception("LinkedIn credentials not found in secrets.config")
    
    # Navigate to the LinkedIn login page.
    driver.get("https://www.linkedin.com/login")
    time.sleep(3)
    
    # Locate and fill the username and password fields.
    email_input = driver.find_element(By.ID, "username")
    email_input.send_keys(username)
    
    password_input = driver.find_element(By.ID, "password")
    password_input.send_keys(password)
    password_input.send_keys(Keys.RETURN)
    time.sleep(3)

def apply_to_jobs(job_title, location, auto_apply=True):
    """
    Automates LinkedIn job search and application process.
    
    Parameters:
        job_title (str): Keywords or job title for the search.
        location (str): Desired job location.
        auto_apply (bool): If True, the script will try to submit the application automatically.
    """
    # Initialize Safari WebDriver.
    # Ensure that Safari's "Allow Remote Automation" is enabled.
    driver = webdriver.Safari()
    
    try:
        # Log in to LinkedIn using the credentials from secrets.config.
        login_to_linkedin(driver)
        
        # Navigate to the LinkedIn Jobs page.
        driver.get("https://www.linkedin.com/jobs")
        time.sleep(3)  # Wait for the page to load

        # Enter search criteria for job title and location.
        search_box = driver.find_element(By.XPATH, "//input[contains(@placeholder, 'Search jobs')]")
        search_box.send_keys(job_title)
        
        location_box = driver.find_element(By.XPATH, "//input[contains(@placeholder, 'Search location')]")
        location_box.clear()
        location_box.send_keys(location)
        location_box.send_keys(Keys.RETURN)
        time.sleep(3)  # Wait for results to load

        # Find job postings from the search results.
        jobs = driver.find_elements(By.XPATH, "//ul[contains(@class, 'jobs-search-results__list')]/li")
        print(f"Found {len(jobs)} job postings.")

        # Iterate through each job posting.
        for index, job in enumerate(jobs):
            try:
                job.click()
                time.sleep(2)  # Wait for job details to appear

                # Look for the 'Easy Apply' button.
                easy_apply_buttons = driver.find_elements(By.XPATH, "//button[contains(@class, 'jobs-apply-button')]")
                if easy_apply_buttons:
                    print(f"[Job {index+1}] 'Easy Apply' button found.")
                    if auto_apply:
                        # Click the 'Easy Apply' button.
                        easy_apply_buttons[0].click()
                        time.sleep(2)  # Wait for the application modal

                        # Check for a resume upload field. If found, attach resume from Resources/resume.pdf.
                        try:
                            resume_upload = driver.find_element(By.XPATH, "//input[@type='file']")
                            if resume_upload:
                                resume_path = os.path.abspath(os.path.join("Resources", "resume.pdf"))
                                resume_upload.send_keys(resume_path)
                                time.sleep(2)
                                print(f"[Job {index+1}] Resume attached from {resume_path}.")
                        except Exception as resume_error:
                            print(f"[Job {index+1}] No resume upload field found, assuming resume is already attached.")

                        # Attempt to submit the application.
                        try:
                            submit_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Submit application')]")
                            submit_button.click()
                            time.sleep(2)
                            print(f"[Job {index+1}] Application submitted!")
                        except Exception as submit_error:
                            print(f"[Job {index+1}] Could not submit application automatically: {submit_error}")
                else:
                    print(f"[Job {index+1}] 'Easy Apply' not available for this job.")
            except Exception as job_error:
                print(f"[Job {index+1}] Error processing job: {job_error}")
                continue

    except Exception as main_error:
        print("An error occurred during the job search process:", main_error)
    
    finally:
        # Always close the browser.
        driver.quit()
