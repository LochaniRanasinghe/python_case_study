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

# Setup logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename='logs/app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def setup_driver():
    options = Options()
    # options.add_argument('--headless')  # Optional: enable for headless mode
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def main():
    logging.info("Starting browser")
    driver = setup_driver()

    try:
        driver.get("https://www.bestbuy.com/?intl=nosplash")
        logging.info("Navigated to BestBuy with no-splash")

        wait = WebDriverWait(driver, 15)

        # Handle splash page
        try:
            us_link = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a.us-link"))
            )
            us_link.click()
            logging.info("Clicked United States link")
        except:
            logging.info("No country selection shown")

        # Search for 'laptop'
        search_bar = wait.until(EC.presence_of_element_located((By.ID, "autocomplete-search-bar")))
        driver.execute_script("arguments[0].scrollIntoView();", search_bar)
        search_bar.clear()
        search_bar.send_keys("laptop")
        logging.info("Entered search query")

        search_button = wait.until(EC.element_to_be_clickable((By.ID, "autocomplete-search-button")))
        search_button.click()
        logging.info("Clicked search button")

        time.sleep(3)  # let carousel load

        # Click "Windows laptops" chip
        try:
            chip = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Windows laptops')]")))
            chip.click()
            logging.info("Clicked 'Windows laptops' category")
        except Exception as e:
            logging.warning(f"Category chip not found: {e}")

        time.sleep(4)  # allow filters to load

        # Apply Price Filters: $500-$1249.99
        for price_id in ["$500_-_$749.99", "$750_-_$999.99", "$1000_-_$1249.99"]:
            try:
                price_checkbox = driver.find_element(By.ID, price_id)
                driver.execute_script("arguments[0].click();", price_checkbox)
                logging.info(f"Applied price filter: {price_id}")
                time.sleep(1)
            except Exception as e:
                logging.warning(f"Couldn't select price {price_id}: {e}")

        # Apply Brand Filters
        for brand in ["Apple", "Lenovo", "HP"]:
            try:
                brand_checkbox = driver.find_element(By.ID, brand)
                driver.execute_script("arguments[0].click();", brand_checkbox)
                logging.info(f"Applied brand filter: {brand}")
                time.sleep(1)
            except Exception as e:
                logging.warning(f"Couldn't select brand {brand}: {e}")

        # Apply Rating Filter: 4 stars & up
        try:
            rating_checkbox = driver.find_element(By.ID, "customer-rating-4_&_Up")
            driver.execute_script("arguments[0].click();", rating_checkbox)
            logging.info("Applied rating filter: 4 stars & up")
        except Exception as e:
            logging.warning(f"Couldn't apply rating filter: {e}")

        print("✅ Filters applied successfully.")

    except Exception as e:
        driver.save_screenshot("logs/error_screenshot.png")
        logging.error(f"An error occurred: {e}", exc_info=True)
        print("❌ Filtering failed. Check logs and screenshot.")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
