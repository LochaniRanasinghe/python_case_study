from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import logging
import time

# Setup logging
logging.basicConfig(
    filename='logs/navigation.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")  # Headless mode for automation
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def main():
    logging.info("Starting browser")
    driver = setup_driver()
    wait = WebDriverWait(driver, 15)

    try:
        driver.get("https://www.bestbuy.com/")
        logging.info("Navigated to BestBuy with no-splash")

        # Accept splash (country selection) if appears
        try:
            country_popup = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "us-link")))
            country_popup.click()
            logging.info("Clicked country popup")
        except:
            logging.info("No country selection shown")

        # Search for laptops
        search = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='st']")))
        search.clear()
        search.send_keys("laptop")
        logging.info("Entered search query")
        search.send_keys(Keys.RETURN)

        # Wait for products to show
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "sku-item")))
        logging.info("Search results loaded")

        # Click category: Windows laptops
        try:
            windows_laptops = wait.until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "Windows laptops")))
            driver.execute_script("arguments[0].click();", windows_laptops)
            logging.info("Clicked 'Windows laptops' category")
        except Exception as e:
            logging.warning(f"Windows laptops category not found: {e}")

        # Apply price filters
        prices = ["$500 - $749.99", "$750 - $999.99", "$1000 - $1249.99"]
        for price_label in prices:
            try:
                price_checkbox = wait.until(
                    EC.presence_of_element_located((By.XPATH, f"//input[@aria-label='{price_label}']"))
                )
                driver.execute_script("arguments[0].scrollIntoView(true);", price_checkbox)
                driver.execute_script("arguments[0].click();", price_checkbox)
                logging.info(f"Applied price filter: {price_label}")
                time.sleep(1)
            except Exception as e:
                logging.warning(f"Couldn't apply price filter {price_label}: {e}")

        # Show all brands
        try:
            show_more_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@data-show-more, 'brand_facet')]"))
            )
            driver.execute_script("arguments[0].click();", show_more_button)
            logging.info("Clicked 'Show all brands'")
            time.sleep(2)
        except Exception as e:
            logging.warning(f"Show all brands not found: {e}")

        # Apply brand filters
        brands = ["Apple", "Lenovo", "HP"]
        for brand in brands:
            try:
                brand_checkbox = wait.until(
                    EC.presence_of_element_located((By.XPATH, f"//input[@id='{brand}']"))
                )
                driver.execute_script("arguments[0].scrollIntoView(true);", brand_checkbox)
                driver.execute_script("arguments[0].click();", brand_checkbox)
                logging.info(f"Applied brand filter: {brand}")
                time.sleep(1)
            except Exception as e:
                logging.warning(f"Couldn't select brand {brand}: {e}")

        # Apply rating filter
        try:
            rating_checkbox = wait.until(
                EC.presence_of_element_located((By.XPATH, "//input[@id='customer-rating-4_&_Up']"))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", rating_checkbox)
            driver.execute_script("arguments[0].click();", rating_checkbox)
            logging.info("Applied rating filter: 4 stars & up")
        except Exception as e:
            logging.warning(f"Couldn't apply rating filter: {e}")

    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
