from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import logging
import time
import os
import requests
from bs4 import BeautifulSoup
import json

# Setup logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename='logs/app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def setup_driver():
    options = Options()
    # options.add_argument('--headless')  # Optional for debugging
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def main():
    logging.info("Starting browser")
    driver = setup_driver()

    try:
        driver.get("https://www.bestbuy.com/?intl=nosplash")
        logging.info("Navigated to BestBuy")

        wait = WebDriverWait(driver, 15)

        # Handle country splash
        try:
            us_link = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a.us-link"))
            )
            us_link.click()
            logging.info("Clicked United States link")
        except:
            logging.info("No country splash shown")

        # Search for laptops
        search_bar = wait.until(EC.presence_of_element_located((By.ID, "autocomplete-search-bar")))
        search_bar.clear()
        search_bar.send_keys("laptop")
        search_button = wait.until(EC.element_to_be_clickable((By.ID, "autocomplete-search-button")))
        search_button.click()
        logging.info("Search submitted")
        time.sleep(3)

        # Click 'Windows laptops' chip
        try:
            chip = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Windows laptops')]")))
            chip.click()
            logging.info("Clicked 'Windows laptops' chip")
        except:
            logging.warning("Could not click 'Windows laptops' chip")

        time.sleep(4)
        logging.info("Applying filters...")

        # Apply price filters
        for price_id in ["$500_-_$749.99", "$750_-_$999.99", "$1000_-_$1249.99"]:
            try:
                price_checkbox = driver.find_element(By.ID, price_id)
                driver.execute_script("arguments[0].click();", price_checkbox)
                logging.info(f"Applied price filter: {price_id}")
                time.sleep(1)
            except Exception as e:
                logging.warning(f"Couldn't select price {price_id}: {e}")

        # Show all brands
        try:
            show_all_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-show-more='brand_facet']")))
            driver.execute_script("arguments[0].click();", show_all_button)
            logging.info("Clicked 'Show all' for brand filters")
            time.sleep(2)
        except Exception as e:
            logging.warning(f"Couldn't click 'Show all' button: {e}")

        # Apply brand filters
        for brand in ["Apple", "Lenovo", "HP"]:
            try:
                brand_checkbox = driver.find_element(By.ID, brand)
                driver.execute_script("arguments[0].click();", brand_checkbox)
                logging.info(f"Applied brand filter: {brand}")
                time.sleep(1)
            except Exception as e:
                logging.warning(f"Couldn't select brand {brand}: {e}")

        # Apply rating filter
        try:
            rating_label = wait.until(EC.presence_of_element_located(
                (By.XPATH, "//label[contains(., '4') and contains(., 'Up')]")
            ))
            rating_input = rating_label.find_element(By.TAG_NAME, "input")
            driver.execute_script("arguments[0].click();", rating_input)
            logging.info("Applied rating filter: 4 stars & up")
            time.sleep(1)
        except Exception as e:
            logging.warning(f"Rating filter error: {e}")

        logging.info("✅ All filters applied successfully")
        print("✅ All filters applied successfully")

    except Exception as e:
        driver.save_screenshot("logs/error_screenshot.png")
        logging.error(f"An error occurred: {e}", exc_info=True)
        print("❌ Filtering failed. Check logs and screenshot.")
    finally:
        time.sleep(2)
        driver.quit()
        logging.info("Browser closed.")

if __name__ == "__main__":
    main()
