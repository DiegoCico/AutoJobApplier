import configparser
import os
import re
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
import db_handler

# Set the path to your configuration file
CONFIG_FILE = "secrets.config"

def get_config_parser():
    """Load the configuration from secrets.config and ensure the [secrets] section exists."""
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)
    if "secrets" not in config:
        config["secrets"] = {}
    return config

def save_config_parser(config):
    """Save the configuration back to the file."""
    with open(CONFIG_FILE, "w") as configfile:
        config.write(configfile)

def get_config_value(var_name, prompt, cast_type=str):
    """
    Retrieve a configuration value from the [secrets] section.
    If the key is missing, prompt the user for it and update the config file.
    """
    config = get_config_parser()
    if var_name in config["secrets"]:
        value = config["secrets"][var_name]
        try:
            return cast_type(value)
        except Exception:
            return value
    else:
        user_input = input(f"Missing configuration for '{var_name}' ({prompt}). Please provide a value: ")
        try:
            value_casted = cast_type(user_input)
        except Exception:
            value_casted = user_input
        config["secrets"][var_name] = str(value_casted)
        save_config_parser(config)
        return value_casted

def sanitize_key(text):
    """
    Sanitizes a text string to create a valid variable name fragment.
    """
    key = re.sub(r'\W+', '_', text)
    return key[:20]

def get_dynamic_config(key_base, prompt):
    """
    For unrecognized questions, generate a key based on the question text.
    If the key isn’t found, prompt the user and store the answer.
    """
    var_name = f"custom_{key_base}"
    config = get_config_parser()
    if var_name in config["secrets"]:
        return config["secrets"][var_name]
    else:
        value = input(f"Missing configuration for '{var_name}' ({prompt}). Please provide a value: ")
        config["secrets"][var_name] = value
        save_config_parser(config)
        return value

# -----------------------------------------------------------------------------
# Retrieve configuration values (they will be prompted for if missing)
# -----------------------------------------------------------------------------
load_delay             = get_config_value("load_delay", "Page load delay in seconds", float)
add_address            = get_config_value("add_address", "Your address", str)
add_phone              = get_config_value("add_phone", "Your phone number", str)
add_city               = get_config_value("add_city", "Your city", str)
add_postal             = get_config_value("add_postal", "Your postal/zip code", str)
add_state              = get_config_value("add_state", "Your county/town", str)
add_github             = get_config_value("add_github", "Your GitHub profile URL", str)
add_DBS                = get_config_value("add_DBS", "Do you have a valid DBS? (Yes/No)", str)
add_criminal           = get_config_value("add_criminal", "Any criminal convictions? (Yes/No)", str)
add_valid_cert         = get_config_value("add_valid_cert", "Do you have a certificate? (Yes/No)", str)
add_university         = get_config_value("add_university", "Your university", str)
add_linkedin           = get_config_value("add_linkedin", "Your LinkedIn URL", str)
add_sponsorship        = get_config_value("add_sponsorship", "Will you need work sponsorship? (Yes/No)", str)
add_relocate           = get_config_value("add_relocate", "Willing to relocate? (Yes/No)", str)
add_workauthorized     = get_config_value("add_workauthorized", "Authorized to work in the US? (Yes/No)", str)
add_citizen            = get_config_value("add_citizen", "US citizen? (Yes/No)", str)
add_education          = get_config_value("add_education", "Education level (Other, Highschool, Associate, Bachelor, Master, Doctorate)", str)
add_leadershipdevelopment = get_config_value("add_leadershipdevelopment", "Years of leadership experience", str)
add_salary             = get_config_value("add_salary", "Salary expectation", str)
add_gender             = get_config_value("add_gender", "Your gender (Male, Female, Decline)", str)
add_veteran            = get_config_value("add_veteran", "Veteran status (Yes/No/Decline)", str)
add_disability         = get_config_value("add_disability", "Disability status (Yes/No/Decline)", str)
add_commute            = get_config_value("add_commute", "Commute status (Yes/No/Decline)", str)
add_commute2           = get_config_value("add_commute2", "Alternative commute status", str)
add_shift              = get_config_value("add_shift", "Preferred shift (Day shift, Night shift, Overnight shift)", str)
add_available          = get_config_value("add_available", "Availability for work hours (Yes/No)", str)
default_unknown_multi  = get_config_value("default_unknown_multi", "Default answer for unknown questions", str)
add_interview_dates    = get_config_value("add_interview_dates", "Available interview dates", str)

# Experience values (as strings; change cast_type if needed)
add_java         = get_config_value("add_java", "Years of Java experience", str)
add_aws          = get_config_value("add_aws", "Years of AWS experience", str)
add_python       = get_config_value("add_python", "Years of Python experience", str)
add_analysis     = get_config_value("add_analysis", "Years of analysis experience", str)
add_django       = get_config_value("add_django", "Years of Django experience", str)
add_php          = get_config_value("add_php", "Years of PHP experience", str)
add_react        = get_config_value("add_react", "Years of React experience", str)
add_node         = get_config_value("add_node", "Years of Node experience", str)
add_angular      = get_config_value("add_angular", "Years of Angular experience", str)
add_javascript   = get_config_value("add_javascript", "Years of JavaScript experience", str)
add_orm          = get_config_value("add_orm", "Years of ORM experience", str)
add_sdet         = get_config_value("add_sdet", "Years of SDET experience", str)
add_selenium     = get_config_value("add_selenium", "Years of Selenium experience", str)
add_testautomation = get_config_value("add_testautomation", "Years of test automation experience", str)
add_webdevyears  = get_config_value("add_webdevyears", "Years of web development experience", str)
add_programming  = get_config_value("add_programming", "Years of programming experience", str)
add_teaching     = get_config_value("add_teaching", "Years of teaching experience", str)
add_default_experience = get_config_value("add_default_experience", "Default experience answer", str)

# -----------------------------------------------------------------------------
# Ensure applied jobs database table exists
# -----------------------------------------------------------------------------
conn = db_handler.get_db_connection()
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS applied_jobs (job_url TEXT PRIMARY KEY)")
conn.commit()
conn.close()

def log_job_application(job_url):
    """
    Inserts the job URL into the applied_jobs table.
    If the URL already exists, it is ignored.
    """
    conn = db_handler.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO applied_jobs (job_url) VALUES (?)", (job_url,))
    conn.commit()
    conn.close()

# -----------------------------------------------------------------------------
# Selenium WebDriver setup
# -----------------------------------------------------------------------------
options = Options()
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36")
driver = webdriver.Chrome('chromedriver', options=options)
driver.get("https://www.indeed.com/account/login")

input("Press Enter when you have successfully logged in and searched for a job title:\n")

total_results = driver.find_element(By.CLASS_NAME, "jobsearch-JobCountAndSortPane-jobCount")
total_results_int = int(total_results.text.split(' ', 1)[0].replace(",", ""))
print(total_results_int, "jobs found in total.")

items_per_page = 15
num_pages = total_results_int // items_per_page

try:
    apply_btn = driver.find_element(By.CLASS_NAME, "ia-IndeedApplyButton")
except Exception:
    apply_btn = 0

# -----------------------------------------------------------------------------
# Main job application loop
# -----------------------------------------------------------------------------
for p in range(num_pages):
    results = driver.find_elements(By.CSS_SELECTOR, ".mosaic-provider-jobcards .tapItem")
    try:
        for result in results:
            hover = ActionChains(driver).move_to_element(result).click()
            hover.perform()
            time.sleep(load_delay)
            
            try:
                apply_btn = driver.find_element(By.CLASS_NAME, "ia-IndeedApplyButton")
            except Exception:
                apply_btn = 0
            
            if not apply_btn:
                continue
            
            if apply_btn.text.lower() == 'apply now':
                apply_btn.click()
                time.sleep(load_delay)
                
                # Switch to the new application window
                windows = driver.window_handles
                driver.switch_to.window(windows[-1])
                
                # Process questionnaire pages (limit to 10 pages)
                for i in range(10):
                    try:
                        applied_title = driver.find_element(By.CLASS_NAME, "ia-HasApplied-bodyTop").text.lower()
                        if "you've applied to this job" in applied_title:
                            driver.close()
                            driver.switch_to.window(windows[0])
                            continue
                    except Exception:
                        pass
                    
                    # Get the questions page heading
                    title_again = False
                    try:
                        questions_title_el = driver.find_element(By.CLASS_NAME, "ia-BasePage-heading").text
                        questions_title = questions_title_el.lower()
                    except Exception:
                        title_again = True
                        
                    if title_again:
                        for i in range(50):
                            try:
                                questions_title_el = driver.find_element(By.CLASS_NAME, "ia-BasePage-heading").text
                                questions_title = questions_title_el.lower()
                                title_again = False
                            except Exception:
                                pass
                    if title_again:
                        questions_title = ''
                    
                    try:
                        questions_continue_btn = driver.find_element(By.CSS_SELECTOR, '.css-1gljdq7')
                    except Exception:
                        questions_continue_btn = 0
                        
                    try:
                        qualifications_continue_btn = driver.find_element(By.CSS_SELECTOR, '.css-10w34ze')
                    except Exception:
                        qualifications_continue_btn = 0
                        
                    try:
                        resume_continue_btn = driver.find_element(By.CSS_SELECTOR, ".css-1gljdq7")
                    except Exception:
                        resume_continue_btn = 0
                        
                    try:
                        experience_continue_btn = driver.find_element(By.CSS_SELECTOR, ".css-1gljdq7")
                    except Exception:
                        experience_continue_btn = 0
                    
                    try:
                        submit_application_btn = driver.find_element(By.CSS_SELECTOR, ".css-njr1op")
                    except Exception:
                        submit_application_btn = 0
                    
                    # Process questionnaire responses if this page has questions
                    if 'questions' in questions_title:
                        questions = driver.find_elements(By.CLASS_NAME, "ia-Questions-item")
                        for question in questions:
                            question_text = question.find_element(By.CSS_SELECTOR, ".css-kyg8or").text.lower()
                            
                            # Determine the answer based on recognized keywords
                            if 'python experience' in question_text:
                                answer = add_python
                            elif 'javascript experience' in question_text:
                                answer = add_javascript
                            elif 'analysis experience' in question_text:
                                answer = add_analysis
                            elif 'experience' in question_text:
                                answer = add_default_experience
                            elif 'phone' in question_text:
                                answer = add_phone
                            elif 'address' in question_text:
                                answer = add_address
                            elif 'city' in question_text:
                                answer = add_city
                            elif 'github url' in question_text:
                                answer = add_github
                            elif 'teaching experience' in question_text:
                                answer = add_teaching
                            elif 'aws experience' in question_text:
                                answer = add_aws
                            elif 'django experience' in question_text or 'selenium experience' in question_text:
                                answer = add_django
                            elif 'leadership experience' in question_text:
                                answer = add_leadershipdevelopment
                            elif 'programming experience' in question_text:
                                answer = add_programming
                            elif 'salary' in question_text:
                                answer = add_salary
                            elif 'gender' in question_text:
                                answer = add_gender
                            elif 'postal' in question_text or 'zip' in question_text:
                                answer = add_postal
                            elif 'state' in question_text:
                                answer = add_state
                            elif 'linkedin url' in question_text:
                                answer = add_linkedin
                            elif 'college' in question_text:
                                answer = add_university
                            elif 'java experience' in question_text:
                                answer = add_java
                            elif 'interview' in question_text:
                                answer = add_interview_dates
                            elif 'available to work the following hours' in question_text:
                                answer = add_available
                            elif any(kw in question_text for kw in ['authorization', 'authorized', 'right to work', 'authorisation', 'authorised']):
                                try:
                                    question.find_element(By.XPATH, f'//*[contains(text(), "{add_workauthorized}")]').click()
                                    answer = None
                                except Exception:
                                    answer = None
                            elif 'level of education' in question_text:
                                try:
                                    question.find_element(By.XPATH, f'//*[contains(text(), "{add_education}")]').click()
                                    answer = None
                                except Exception:
                                    answer = None
                            elif 'sponsorship' in question_text:
                                try:
                                    question.find_element(By.XPATH, f'//*[contains(text(), "{add_sponsorship}")]').click()
                                    answer = None
                                except Exception:
                                    answer = None
                            elif 'commute' in question_text or 'travel' in question_text:
                                try:
                                    question.find_element(By.XPATH, f'//*[contains(text(), "{add_commute}")]').click()
                                    answer = None
                                except Exception:
                                    try:
                                        question.find_element(By.XPATH, f'//*[contains(text(), "{add_commute2}")]').click()
                                        answer = None
                                    except Exception:
                                        answer = None
                            elif 'shift' in question_text:
                                try:
                                    question.find_element(By.XPATH, f'//*[contains(text(), "{add_shift}")]').click()
                                    answer = None
                                except Exception:
                                    answer = None
                            elif 'veteran' in question_text or 'disability' in question_text:
                                try:
                                    question.find_element(By.XPATH, f'//*[contains(text(), "{add_disability}")]').click()
                                    answer = None
                                except Exception:
                                    answer = None
                            elif 'DBS' in question_text:
                                try:
                                    question.find_element(By.XPATH, f'//*[contains(text(), "{add_DBS}")]').click()
                                    answer = None
                                except Exception:
                                    answer = None
                            elif 'criminal' in question_text:
                                try:
                                    question.find_element(By.XPATH, f'//*[contains(text(), "{add_criminal}")]').click()
                                    answer = None
                                except Exception:
                                    try:
                                        question.find_elements(By.XPATH, f'//span[contains(text(), "{add_criminal}")]')[-1].click()
                                        answer = None
                                    except Exception:
                                        answer = None
                            elif 'valid' in question_text:
                                try:
                                    question.find_element(By.XPATH, f'//*[contains(text(), "{add_valid_cert}")]').click()
                                    answer = None
                                except Exception:
                                    answer = None
                            elif 'hear about this position' in question_text:
                                try:
                                    question.find_element(By.XPATH, f'//*[contains(text(), "{add_disability}")]').click()
                                    answer = None
                                except Exception:
                                    answer = None
                            else:
                                # Unknown question – generate a key and prompt the user
                                key_base = sanitize_key(question_text)
                                answer = get_dynamic_config(key_base, f"Answer for question: {question_text}")
                            
                            # If an answer was determined, type it into the input field
                            if answer is not None:
                                try:
                                    input_field = question.find_element(By.CSS_SELECTOR, '[id^="input-q"]')
                                    input_field.send_keys(Keys.CONTROL, "a", Keys.DELETE)
                                    input_field.send_keys(answer)
                                except Exception as e:
                                    print("Error entering answer:", e)
                    
                    # Click on the next/submit button as available
                    if questions_continue_btn:
                        questions_continue_btn.click()
                        time.sleep(load_delay)
                    elif qualifications_continue_btn:
                        qualifications_continue_btn.click()
                        time.sleep(load_delay)
                    elif resume_continue_btn:
                        resume_continue_btn.click()
                        time.sleep(load_delay)
                    elif experience_continue_btn:
                        experience_continue_btn.click()
                        time.sleep(load_delay)
                    elif submit_application_btn:
                        # Log the job application before finishing
                        job_url = driver.current_url
                        submit_application_btn.click()
                        time.sleep(load_delay)
                        log_job_application(job_url)
                        break
                    else:
                        print("There appears to be something wrong with this job. Skipping.")
                        break

                driver.close()
                driver.switch_to.window(windows[0])
    except Exception as e:
        print(e)
        windows = driver.window_handles
        driver.switch_to.window(windows[0])
        driver.refresh()
        continue
    
    while True:
        try:
            driver.find_element(By.XPATH, "//a[@data-testid='pagination-page-next']").click()
            break
        except Exception as e:
            print(e)
            driver.refresh()
            time.sleep(load_delay)
    
    time.sleep(load_delay)
