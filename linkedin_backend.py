"""
backend.py

Backend module for LinkedIn Job Application Automation.

This module automates the process of searching and applying for jobs on LinkedIn.
It uses Selenium WebDriver (configured for Safari) to:
  - Log in to LinkedIn using credentials from a configuration file (secrets.config)
  - Navigate to the LinkedIn Jobs page
  - Search for a given job title and location
  - Attempt to apply using the "Easy Apply" feature (including attaching a resume from Resources/resume.pdf)

If a two-step verification prompt is detected during login, the script will prompt the
user via the console for the verification code.

Additionally, during the application process, if the modal asks questions (e.g. “Number
of years coding in React”), the script looks up the question in a local SQLite database
(stored in Resources/questions.db). If the question is not found, the user is prompted
to input an answer, which is then saved in the database for future use.

Detailed logging is provided throughout for debugging purposes.
"""

import logging
import os
import sqlite3
import time
from typing import Dict
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configure logging. The front-end controls the root logger level.
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


def read_secrets(file_path: str = "secrets.config") -> Dict[str, str]:
    """
    Read LinkedIn credentials from a configuration file.

    The file should contain lines in the following format:
        username_linkedin=your_email@example.com
        password_linkedin=your_password

    Args:
        file_path (str): Path to the configuration file.

    Returns:
        Dict[str, str]: A dictionary with keys 'username_linkedin' and 'password_linkedin'.
    """
    logger.debug("Reading secrets from %s", file_path)
    secrets: Dict[str, str] = {}
    try:
        with open(file_path, "r") as file:
            for line in file:
                line = line.strip()
                if line and "=" in line:
                    key, value = line.split("=", 1)
                    secrets[key.strip()] = value.strip()
        logger.info("Successfully read secrets.config")
    except Exception as e:
        logger.error("Error reading secrets.config: %s", e)
    return secrets


def login_to_linkedin(driver: WebDriver) -> None:
    """
    Log in to LinkedIn using credentials from secrets.config.

    If a two-step verification prompt is detected, the user is prompted to
    enter the verification code via the console.

    Args:
        driver (WebDriver): Selenium WebDriver instance.

    Raises:
        Exception: If credentials are missing or login fails.
    """
    logger.info("Starting LinkedIn login process")
    secrets = read_secrets()
    username = secrets.get("username_linkedin")
    password = secrets.get("password_linkedin")
    
    if not username or not password:
        raise Exception("LinkedIn credentials not found in secrets.config")
    
    driver.get("https://www.linkedin.com/login")
    logger.debug("Navigated to LinkedIn login page")
    
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "username")))
    logger.debug("Username field is present")
    
    driver.find_element(By.ID, "username").send_keys(username)
    logger.debug("Entered username")
    
    password_input = driver.find_element(By.ID, "password")
    password_input.send_keys(password)
    logger.debug("Entered password")
    
    password_input.send_keys(Keys.RETURN)
    logger.info("Submitted login credentials")
    
    # Allow time for potential two-step verification prompt.
    time.sleep(3)
    try:
        logger.debug("Checking for two-step verification prompt")
        twofa_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[contains(@placeholder, 'Verification code')]"))
        )
        if twofa_field:
            logger.info("Two-step verification prompt detected")
            code = input("Enter the two-step verification code from LinkedIn: ")
            twofa_field.send_keys(code)
            twofa_field.send_keys(Keys.RETURN)
            logger.debug("Submitted two-step verification code")
    except Exception as e:
        logger.debug("No two-step verification prompt detected: %s", e)
    
    try:
        logger.debug("Waiting for element that confirms login success")
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/feed/')]"))
        )
        logger.info("Login successful!")
    except Exception as e:
        logger.error("Login might have failed. Current URL: %s", driver.current_url)
        raise Exception("Login did not complete successfully.") from e


def process_application_questions(driver: WebDriver) -> None:
    """
    Process application questions in the "Easy Apply" modal.

    Searches for question groups (each containing a label and an input or textarea).
    For each question, if an answer exists in the local database (Resources/questions.db),
    that answer is used to fill in the input. If not, the user is prompted for an answer,
    which is then saved in the database for future use.

    Args:
        driver (WebDriver): Selenium WebDriver instance.
    """
    db_path = os.path.abspath(os.path.join("Resources", "questions.db"))
    logger.debug("Connecting to questions database at %s", db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS questions (question TEXT PRIMARY KEY, answer TEXT)")
    conn.commit()

    try:
        # Adjust the CSS selector based on the current LinkedIn modal structure.
        question_groups = driver.find_elements(By.CSS_SELECTOR, "div.jobs-easy-apply-form-section__group")
        logger.debug("Found %d question groups", len(question_groups))
        for group in question_groups:
            try:
                label_elem = group.find_element(By.TAG_NAME, "label")
                question_text = label_elem.text.strip()
                if not question_text:
                    continue
                logger.debug("Processing question: %s", question_text)
                # Try to find an input field; if not, try a textarea.
                try:
                    input_field = group.find_element(By.TAG_NAME, "input")
                except Exception:
                    input_field = group.find_element(By.TAG_NAME, "textarea")
                
                cursor.execute("SELECT answer FROM questions WHERE question = ?", (question_text,))
                row = cursor.fetchone()
                if row:
                    answer = row[0]
                    logger.info("Using stored answer for question: %s", question_text)
                else:
                    answer = input(f"Enter answer for '{question_text}': ")
                    cursor.execute("INSERT INTO questions (question, answer) VALUES (?, ?)", (question_text, answer))
                    conn.commit()
                    logger.info("Saved answer for question: %s", question_text)
                input_field.clear()
                input_field.send_keys(answer)
            except Exception as qe:
                logger.debug("Error processing question group: %s", qe)
    except Exception as e:
        logger.error("Error processing application questions: %s", e)
    finally:
        conn.close()
        logger.debug("Closed questions database connection")


def apply_to_jobs(job_title: str, location: str, auto_apply: bool = True) -> None:
    """
    Automate job search and application on LinkedIn.

    Navigates to the LinkedIn Jobs page, searches for jobs based on the provided
    title and location, and attempts to apply automatically using the "Easy Apply"
    feature. If a resume upload field is present, attaches a resume from
    Resources/resume.pdf. If additional application questions are present, they are
    processed via the local questions database.

    Args:
        job_title (str): The job title or keywords to search for.
        location (str): The desired job location.
        auto_apply (bool): If True, automatically attempt to apply. Defaults to True.
    """
    logger.info("Starting job application process for '%s' jobs in '%s'", job_title, location)
    
    try:
        driver = webdriver.Safari()
        logger.debug("Initialized Safari WebDriver")
    except Exception as e:
        logger.error("Failed to initialize Safari WebDriver: %s", e)
        return
    
    try:
        login_to_linkedin(driver)
        
        driver.get("https://www.linkedin.com/jobs")
        logger.debug("Navigated to LinkedIn Jobs page")
        wait = WebDriverWait(driver, 20)
        
        logger.debug("Locating the job keyword search field")
        search_box = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "input.jobs-search-box__text-input--keyword")
        ))
        logger.debug("Job keyword search field found")
        
        logger.debug("Locating the location search field")
        location_box = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "input.jobs-search-box__text-input--location")
        ))
        logger.debug("Location search field found")
        
        search_box.clear()
        search_box.send_keys(job_title)
        logger.debug("Entered job title: %s", job_title)
        
        location_box.clear()
        location_box.send_keys(location)
        logger.debug("Entered location: %s", location)
        location_box.send_keys(Keys.RETURN)
        logger.info("Submitted search criteria")
        
        logger.debug("Waiting for job results to load")
        jobs = wait.until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "ul.jobs-search-results__list li")
        ))
        logger.info("Found %d job postings", len(jobs))
        
        for index, job in enumerate(jobs):
            logger.info("Processing job posting #%d", index + 1)
            try:
                driver.execute_script("arguments[0].scrollIntoView(true);", job)
                time.sleep(1)
                job.click()
                logger.debug("Clicked on job posting #%d", index + 1)
                time.sleep(2)
                
                easy_apply_buttons = driver.find_elements(By.XPATH, "//button[contains(@class, 'jobs-apply-button')]")
                if easy_apply_buttons:
                    logger.info("[Job %d] 'Easy Apply' button found.", index + 1)
                    if auto_apply:
                        easy_apply_buttons[0].click()
                        logger.debug("[Job %d] Clicked 'Easy Apply' button.", index + 1)
                        wait.until(EC.visibility_of_element_located(
                            (By.XPATH, "//div[contains(@class, 'jobs-easy-apply-modal')]")
                        ))
                        logger.debug("[Job %d] Application modal is visible.", index + 1)
                        time.sleep(1)
                        
                        # Process additional application questions, if any.
                        process_application_questions(driver)
                        
                        try:
                            resume_upload = driver.find_element(By.XPATH, "//input[@type='file']")
                            if resume_upload:
                                resume_path = os.path.abspath(os.path.join("Resources", "resume.pdf"))
                                resume_upload.send_keys(resume_path)
                                time.sleep(1)
                                logger.info("[Job %d] Resume attached from %s.", index + 1, resume_path)
                        except Exception as resume_error:
                            logger.debug("[Job %d] No resume upload field found: %s", index + 1, resume_error)
                        
                        try:
                            submit_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Submit application')]")
                            submit_button.click()
                            time.sleep(1)
                            logger.info("[Job %d] Application submitted!", index + 1)
                        except Exception as submit_error:
                            logger.error("[Job %d] Could not submit application automatically: %s", index + 1, submit_error)
                else:
                    logger.info("[Job %d] 'Easy Apply' not available.", index + 1)
            except Exception as job_error:
                logger.error("[Job %d] Error processing job: %s", index + 1, job_error)
                continue
    
    except Exception as main_error:
        logger.error("An error occurred during the job search process: %s", main_error)
    
    finally:
        logger.info("Closing the browser.")
        driver.quit()
