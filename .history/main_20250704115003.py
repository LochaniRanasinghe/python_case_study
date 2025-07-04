from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import logging
import time

# Setup logging
logging.basicConfig(filename='logs/app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# def setup_driver():
#     options = Options()
#     options.add_argument('--headless')  # Run in headless mode
#     options.add_argument('--disable-gpu')
#     options.add_argument('--window-size=1920,1080')
#     driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
#     return driver

def main():
    logging.info("Starting browser")
    driver = setup_driver()
    driver.get("https://www.bestbuy.com/")
    logging.info("Navigated to BestBuy")

    try:
        wait = WebDriverWait(driver, 15)

        # Wait for search bar
        search_bar = wait.until(EC.presence_of_element_located((By.ID, "autocomplete-search-bar")))
        search_bar.clear()
        search_bar.send_keys("laptop")

        logging.info("Entered search query: laptop")

        # Wait for and click the search button
        search_button = wait.until(EC.element_to_be_clickable((By.ID, "autocomplete-search-button")))
        search_button.click()

        logging.info("Search submitted")

        # Wait for results to load
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".sku-item")))
        logging.info("Search results loaded")

        print("✅ Laptop search completed successfully.")

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        print("❌ Something went wrong. Check logs.")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
