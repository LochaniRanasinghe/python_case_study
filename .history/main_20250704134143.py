import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Setup folders
os.makedirs("logs", exist_ok=True)

# Setup logging
logging.basicConfig(
    filename="logs/app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def setup_driver():
    options = Options()
    # options.add_argument('--headless')  # Uncomment for headless mode
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def main():
    logging.info("Starting browser")
    driver = setup_driver()

    try:
        driver.get("https://www.bestbuy.com/?intl=nosplash")
        logging.info("Navigated to BestBuy")

        wait = WebDriverWait(driver, 15)

        # Handle splash page (if shown)
        try:
            us_link = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a.us-link"))
            )
            us_link.click()
            logging.info("Clicked United States link")
        except:
            logging.info("No country splash shown")

        # Search for 'laptop'
        search_bar = wait.until(EC.presence_of_element_located((By.ID, "autocomplete-search-bar")))
        driver.execute_script("arguments[0].scrollIntoView();", search_bar)
        search_bar.clear()
        search_bar.send_keys("laptop")
        logging.info("Search submitted")

        search_button = wait.until(EC.element_to_be_clickable((By.ID, "autocomplete-search-button")))
        search_button.click()

        time.sleep(3)  # Wait for chip options

        # Click "Windows laptops" chip
        try:
            chip = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//span[contains(text(), 'Windows laptops')]")))
            chip.click()
            logging.info("Clicked 'Windows laptops' chip")
        except Exception as e:
            logging.warning(f"Could not click chip: {e}")

        time.sleep(4)  # Allow filters to load

        logging.info("Applying filters...")

        # Apply price filters
        for price_id in ["$500_-_$749.99", "$750_-_$999.99", "$1000_-_$1249.99"]:
            try:
                price_checkbox = driver.find_element(By.ID, price_id)
                driver.execute_script("arguments[0].click();", price_checkbox)
                logging.info(f"Applied price filter: {price_id}")
                time.sleep(1)
            except Exception as e:
                logging.warning(f"Couldn't apply price filter {price_id}: {e}")

        # Expand brand list if needed
        try:
            show_all_btn = driver.find_element(By.XPATH, "//button[contains(@data-show-more, 'brand_facet')]")
            driver.execute_script("arguments[0].click();", show_all_btn)
            logging.info("Clicked 'Show all' for brand filters")
            time.sleep(2)
        except Exception as e:
            logging.warning(f"No 'Show all' for brands found: {e}")

        # Apply brand filters
        for brand in ["Apple", "Lenovo", "HP"]:
            try:
                label = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, f"//label[contains(@for, '{brand}')]"))
                )
                checkbox = label.find_element(By.TAG_NAME, "input")
                driver.execute_script("arguments[0].click();", checkbox)
                logging.info(f"Applied brand filter: {brand}")
                time.sleep(1)
            except Exception as e:
                logging.warning(f"Brand filter error: {brand}: {e}")

        # Apply 4+ rating filter
        # Apply 4+ rating filter
try:
    rating_label = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.XPATH, "//label[contains(@for, 'customer-rating-4_&_Up')]"))
    )
    rating_checkbox = rating_label.find_element(By.TAG_NAME, "input")
    driver.execute_script("arguments[0].click();", rating_checkbox)
    logging.info("Applied rating filter: 4 stars & up")
    time.sleep(1)
except Exception as e:
    logging.warning(f"Rating filter error: {e}")


        print("✅ Filters applied successfully.")
        logging.info("✅ All filters applied successfully")

    except Exception as e:
        driver.save_screenshot("logs/error_screenshot.png")
        logging.error(f"Error occurred", exc_info=True)
        print("❌ Error applying filters. Check logs and screenshot.")

    finally:
        driver.quit()
        logging.info("Browser closed.")

if __name__ == "__main__":
    main()
