import getpass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
import time
from datetime import datetime
from inmate_search import parse_inmate_search_results

# Prompt user for credentials
username = input('Enter your PBSO username: ')
password = getpass.getpass('Enter your PBSO password: ')

# Set up Chrome options
chrome_options = Options()
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
chrome_options.add_experimental_option("prefs", {
    "credentials_enable_service": False,
    "profile.password_manager_enabled": False
})
chrome_options.add_argument("--disable-save-password-bubble")
chrome_options.add_argument("--disable-infobars")
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument("--incognito")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-popup-blocking")

# Helper to robustly set date fields
def set_date_field(element, value):
    element.click()
    element.send_keys(Keys.CONTROL + "a")
    element.send_keys(Keys.DELETE)
    time.sleep(0.2)
    element.send_keys(value)
    time.sleep(0.2)

# Function to dismiss password popup
def dismiss_password_popup(driver):
    try:
        ok_buttons = driver.find_elements(By.XPATH, "//button[normalize-space()='OK']")
        for btn in ok_buttons:
            btn.click()
            time.sleep(0.5)
    except Exception:
        pass

# Start ChromeDriver
service = Service()
driver = webdriver.Chrome(service=service, options=chrome_options)

driver.get('https://www3.pbso.org/mediablotter/index.cfm?fa=login')

# Fill in username and password
user_input = driver.find_element(By.ID, 'username')
pass_input = driver.find_element(By.ID, 'password')
user_input.send_keys(username)
pass_input.send_keys(password)

# Click the sign in button
login_btn = driver.find_element(By.CSS_SELECTOR, 'button.btn-login')
login_btn.click()

# Wait for login to process and navigate to search page
print('Logging in...')
time.sleep(3)
driver.get('https://www3.pbso.org/mediablotter/index.cfm?fa=search1')
print('Navigated to inmate search page.')

# Prompt for search parameters
start_date = input('Enter start date (MM/DD/YYYY): ')
today = datetime.today().strftime('%m/%d/%Y')
print(f'End date will be set to today: {today}')

print('Paste in the list of names (one per line, format: Last, First). Enter an empty line to finish:')
name_lines = []
while True:
    line = input()
    if not line.strip():
        break
    name_lines.append(line.strip())

names = []
for name in name_lines:
    if ',' in name:
        last, first = name.split(',', 1)
        last = last.strip().split()[0]
        first = first.strip().split()[0]
        # Only accept if both last and first are alphabetic
        if last.isalpha() and first.isalpha():
            names.append((last, first))
        else:
            print(f'Skipping invalid name: {name}')
    else:
        print(f'Invalid name format: {name}')

# For each name, perform a search
for last, first in names:
    print(f'Searching for: {last}, {first}')
    dismiss_password_popup(driver)
    # Fill in search form
    set_date_field(driver.find_element(By.ID, 'start_date'), start_date)
    set_date_field(driver.find_element(By.ID, 'end_date'), today)
    driver.find_element(By.ID, 'lastName').clear()
    driver.find_element(By.ID, 'lastName').send_keys(last)
    driver.find_element(By.ID, 'firstName').clear()
    driver.find_element(By.ID, 'firstName').send_keys(first)
    # Submit search
    driver.find_element(By.CSS_SELECTOR, 'input[type="submit"][name="process"]').click()
    time.sleep(2)  # Wait for results to load
    # Extract inmate info from page source
    html = driver.page_source
    results = parse_inmate_search_results(html, today=datetime.today())
    if not results:
        print('No bookings found for this name.')
    for booking in results:
        print('---')
        print(f"Booking Number: {booking['booking_number']}")
        print(f"Booking Date: {booking['booking_date']}")
        print(f"Release Date: {booking['release_date'] if booking['release_date'] else 'In Custody'}")
        print(f"Custody Duration: {booking['custody_duration']}")
        print(f"Facility: {booking['facility']}")
    # Return to search page for next name
    driver.get('https://www3.pbso.org/mediablotter/index.cfm?fa=search1')
    time.sleep(1)

input('Press Enter to close browser...')
driver.quit()
