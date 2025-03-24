"""
backend_indeed.py

Backend module for Indeed Job Application Automation.

This module automates the process of searching and applying for jobs on Indeed.
It logs in to Indeed using credentials from secrets.config, navigates to the
jobs page, searches for jobs based on a keyword and location, and if an "Apply Now"
button is present, processes the application questions (if any) and submits the application.
"""

import difflib
import logging
import os
import time
from typing import Dict

from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from db_handler import get_db_connection

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


def read_secrets(file_path: str = "secrets.config") -> Dict[str, str]:
    """
    Read Indeed credentials from a configuration file.
    The file should contain lines like:
        username_indeed=your_email@example.com
        password_indeed=your_password
    """
    logger.debug("Reading secrets from %s", file_path)
    secrets = {}
    try:
        with open(file_path, "r") as file:
            for line in file:
                line = line.strip()
                if line and "=" in line:
                    key, value = line.split("=", 1)
                    secrets[key.strip()] = value.strip()
        logger.info("Successfully read secrets from %s", file_path)
    except Exception as e:
        logger.error("Error reading secrets.config: %s", e)
    return secrets


def find_element_fuzzy(driver: WebDriver, target_placeholder: str, cutoff: float = 0.5):
    """
    Look for an <input> element whose placeholder attribute is a close match to target_placeholder.
    Uses difflib.SequenceMatcher to compute a similarity ratio.
    Returns the element if a candidate meets the cutoff; otherwise raises an exception.
    """
    candidates = driver.find_elements(By.TAG_NAME, "input")
    best_match = None
    best_ratio = 0.0
    for elem in candidates:
        placeholder = elem.get_attribute("placeholder")
        if placeholder:
            ratio = difflib.SequenceMatcher(None, placeholder.lower(), target_placeholder.lower()).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = elem
    logger.debug("Best match for placeholder '%s' is '%s' with ratio %f",
                 target_placeholder, best_match.get_attribute("placeholder") if best_match else "None", best_ratio)
    if best_match and best_ratio >= cutoff:
        return best_match
    else:
        raise Exception(f"No element with placeholder close to '{target_placeholder}' found (best ratio: {best_ratio})")


def click_element(driver: WebDriver, element):
    """
    Attempt a normal click on the element; if that fails, use JavaScript to click.
    """
    try:
        element.click()
    except Exception as e:
        logger.debug("Standard click failed: %s; using JavaScript click", e)
        driver.execute_script("arguments[0].click();", element)


def login_to_indeed(driver: WebDriver) -> None:
    """
    Log in to Indeed using credentials from secrets.config.
    """
    logger.info("Starting Indeed login process")
    secrets = read_secrets()
    username = secrets.get("username_indeed")
    password = secrets.get("password_indeed")

    if not username or not password:
        raise Exception("Indeed credentials not found in secrets.config")

    # Navigate to Indeed login page (URL may change over time)
    driver.get("https://secure.indeed.com/account/login")
    logger.debug("Navigated to Indeed login page")

    wait = WebDriverWait(driver, 10)
    wait = WebDriverWait(driver, 20)
    email_field = wait.until(EC.element_to_be_clickable((By.ID, "login-email-input")))
    email_field.clear()
    password_field = driver.find_element(By.ID, "login-password-input")

    email_field.send_keys(username)
    password_field.send_keys(password)
    password_field.send_keys(Keys.RETURN)
    logger.info("Submitted login credentials")

    time.sleep(3)  # Wait for login to process

    # Check for a successful login by waiting for a known element (e.g., profile icon)
    try:
        wait.until(EC.presence_of_element_located((By.ID, "userOptionsLabel")))
        logger.info("Login successful!")
    except Exception as e:
        logger.error("Login might have failed. Current URL: %s", driver.current_url)
        raise Exception("Login did not complete successfully.") from e


def process_application_questions(driver: WebDriver) -> None:
    """
    Process application questions in the Easy Apply modal on Indeed.
    For each question, check the local SQLite database for an answer.
    If not found, prompt the user and save the answer.
    
    Note: The selectors below (e.g., 'div.indeed-apply-form-section')
    are placeholders and may need to be updated according to the actual page structure.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        question_groups = driver.find_elements(By.CSS_SELECTOR, "div.indeed-apply-form-section")
        logger.debug("Found %d question groups", len(question_groups))
        for group in question_groups:
            try:
                label_elem = group.find_element(By.TAG_NAME, "label")
                question_text = label_elem.text.strip()
                if not question_text:
                    continue
                # Attempt to find an input or textarea element within the group.
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
    Automate job search and application on Indeed.
    Searches for jobs matching the given job_title and location.
    If an Apply Now button is available, processes the application questions and submits the application.
    """
    logger.info("Starting job application process for '%s' jobs in '%s'", job_title, location)

    try:
        driver = webdriver.Safari()  # Adjust the driver (Chrome, Firefox, etc.) as needed.
        logger.debug("Initialized Safari WebDriver")
    except Exception as e:
        logger.error("Failed to initialize Safari WebDriver: %s", e)
        return

    try:
        # Log in to Indeed
        login_to_indeed(driver)

        # Navigate to the Indeed jobs page
        driver.get("https://www.indeed.com/jobs")
        logger.debug("Navigated to Indeed jobs page")
        driver.execute_script("window.scrollTo(0,0);")
        wait = WebDriverWait(driver, 30)

        # --- UPDATE THE TARGET STRINGS AS NEEDED ---
        # The Indeed job search page usually contains two input boxes:
        # one for job keywords ("what") and one for location ("where").
        what_target = "Job title, keywords, or company"
        where_target = "City, state, or zip code"

        # Locate the job title (what) search box using fuzzy matching.
        try:
            what_box = find_element_fuzzy(driver, what_target, cutoff=0.5)
            wait.until(EC.element_to_be_clickable((By.XPATH, f"//input[@placeholder='{what_box.get_attribute('placeholder')}']")))
            logger.debug("Found job title search box with placeholder: '%s'", what_box.get_attribute("placeholder"))
        except Exception as e:
            logger.error("Failed to locate job title search box: %s", e)
            raise

        # Locate the location (where) search box using fuzzy matching.
        try:
            where_box = find_element_fuzzy(driver, where_target, cutoff=0.5)
            wait.until(EC.element_to_be_clickable((By.XPATH, f"//input[@placeholder='{where_box.get_attribute('placeholder')}']")))
            logger.debug("Found location search box with placeholder: '%s'", where_box.get_attribute("placeholder"))
        except Exception as e:
            logger.error("Failed to locate location search box: %s", e)
            raise

        # Enter the job keyword.
        try:
            click_element(driver, what_box)
        except Exception as click_error:
            logger.error("Error clicking job title box: %s", click_error)
            raise
        what_box.clear()
        what_box.send_keys(job_title)
        logger.info("Entered job title: '%s'", job_title)

        # Enter the location.
        try:
            click_element(driver, where_box)
        except Exception as click_error:
            logger.error("Error clicking location box: %s", click_error)
            raise
        driver.execute_script("arguments[0].value = '';", where_box)
        where_box.send_keys(location)
        where_box.send_keys(Keys.RETURN)
        logger.info("Submitted search criteria for '%s' in '%s'", job_title, location)

        # Wait for job results to load.
        try:
            # Indeed job cards are often anchor elements with the class "tapItem".
            jobs = wait.until(EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "a.tapItem")
            ))
            logger.info("Found %d job postings", len(jobs))
        except Exception as e:
            logger.error("Failed to locate job postings: %s", e)
            raise

        # Process each job posting.
        for index, job in enumerate(jobs):
            logger.info("Processing job posting #%d", index + 1)
            try:
                driver.execute_script("arguments[0].scrollIntoView(true);", job)
                time.sleep(1)
                try:
                    job.click()
                    logger.debug("Clicked on job posting #%d using standard click", index + 1)
                except Exception as click_error:
                    logger.warning("Standard click failed: %s; using JS click", click_error)
                    driver.execute_script("arguments[0].click();", job)
                time.sleep(2)

                # (Optional) Extract a snippet of the job description.
                try:
                    description_elem = driver.find_element(By.ID, "jobDescriptionText")
                    description = description_elem.text
                except Exception as e:
                    logger.error("Could not extract job description for job #%d: %s", index + 1, e)
                    description = "Unknown"

                # Check for the presence of an Apply Now button.
                apply_buttons = driver.find_elements(By.XPATH, "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply now')]")
                if apply_buttons:
                    logger.info("Apply Now button found for job #%d", index + 1)
                    if auto_apply:
                        try:
                            click_element(driver, apply_buttons[0])
                            logger.debug("Clicked Apply Now button for job #%d", index + 1)
                        except Exception as e:
                            logger.error("Failed to click Apply Now: %s", e)
                        # Wait for the application modal or form to appear.
                        wait.until(EC.visibility_of_element_located(
                            (By.XPATH, "//div[contains(@class, 'indeed-apply-modal')]")
                        ))
                        time.sleep(1)
                        process_application_questions(driver)

                        # Optionally attach your resume.
                        try:
                            resume_upload = driver.find_element(By.XPATH, "//input[@type='file']")
                            resume_path = os.path.abspath(os.path.join("Resources", "resume.pdf"))
                            resume_upload.send_keys(resume_path)
                            time.sleep(1)
                            logger.info("Attached resume from %s for job #%d", resume_path, index + 1)
                        except Exception as resume_error:
                            logger.debug("No resume upload field found for job #%d: %s", index + 1, resume_error)

                        # Attempt to submit the application.
                        try:
                            submit_button = driver.find_element(By.XPATH, "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'submit')]")
                            click_element(driver, submit_button)
                            time.sleep(2)
                            logger.info("Submitted application for job #%d", index + 1)
                        except Exception as submit_error:
                            logger.error("Could not submit application for job #%d: %s", index + 1, submit_error)
                    else:
                        logger.info("Auto-apply disabled for job #%d", index + 1)
                else:
                    logger.info("Apply Now not available for job #%d", index + 1)

            except Exception as job_error:
                logger.error("Error processing job #%d: %s", index + 1, job_error)
                continue

    except Exception as main_error:
        logger.error("An error occurred during the job search process: %s", main_error)
    finally:
        driver.quit()
        logger.info("Closed browser session.")


if __name__ == "__main__":
    # Example usage:
    apply_to_jobs("Software Engineer", "United States", auto_apply=True)
