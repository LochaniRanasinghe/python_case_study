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
from bs4 import BeautifulSoup
import json
import pandas as pd

# Setup logging and folders
os.makedirs("logs", exist_ok=True)
os.makedirs("data", exist_ok=True)
os.makedirs("reports", exist_ok=True)

logging.basicConfig(
    filename='logs/app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def setup_driver():
    options = Options()
    options.add_argument('--headless')
    # options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def scroll_through_all_pages(driver):
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def extract_filtered_data_from_html(html):
    soup = BeautifulSoup(html, "html.parser")
    product_cards = soup.find_all("li", class_="product-list-item")
    logging.info(f"Found {len(product_cards)} product cards")

    products = []
    for card in product_cards:
        def safe_select(selector, default="N/A", attr=None):
            try:
                tag = card.select_one(selector)
                return tag[attr] if attr else tag.get_text(strip=True)
            except:
                return default

        name = safe_select("h2.product-title")
        price = safe_select("div[data-testid='medium-customer-price']")
        rating = safe_select(".c-ratings-reviews .visually-hidden")
        reviews = safe_select(".c-reviews", default="0").strip("()")
        link = safe_select("a.product-list-item-link", attr="href")
        if link != "N/A" and not link.startswith("http"):
            link = "https://www.bestbuy.com" + link

        model = "N/A"
        sku = "N/A"
        try:
            attributes = card.select("div.product-attributes div.attribute")
            for attr in attributes:
                text = attr.get_text(strip=True)
                if "Model:" in text:
                    model = attr.select_one("span.value").get_text(strip=True)
                elif "SKU:" in text:
                    sku = attr.select_one("span.value").get_text(strip=True)
        except Exception as e:
            logging.warning(f"Error extracting model/SKU: {e}")

        products.append({
            "name": name,
            "link": link,
            "price": price,
            "rating": rating,
            "reviews": reviews,
            "sku": sku,
            "model": model
        })

    with open("data/filtered_products.json", "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)

    logging.info("✅ Product data saved to data/filtered_products.json")
    print(f"✅ {len(products)} products extracted and saved.")

def export_to_excel():
    try:
        df = pd.read_json("data/filtered_products.json")
        with pd.ExcelWriter("reports/summary.xlsx", engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Product Summary", index=False)
        logging.info("📊 Excel report generated at reports/summary.xlsx")
        print("📊 Excel summary report generated.")
    except Exception as e:
        logging.error(f"Error exporting Excel file: {e}", exc_info=True)
        print("❌ Failed to export Excel summary.")

def main():
    logging.info("Starting browser")
    driver = setup_driver()

    try:
        driver.get("https://www.bestbuy.com/?intl=nosplash")
        logging.info("Navigated to BestBuy")
        wait = WebDriverWait(driver, 15)

        # Country splash
        try:
            us_link = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a.us-link"))
            )
            us_link.click()
            logging.info("Clicked United States link")
        except:
            logging.info("No country splash shown")

        # Search laptops
        search_bar = wait.until(EC.presence_of_element_located((By.ID, "autocomplete-search-bar")))
        search_bar.clear()
        search_bar.send_keys("laptop")
        search_button = wait.until(EC.element_to_be_clickable((By.ID, "autocomplete-search-button")))
        search_button.click()
        logging.info("Search submitted")
        time.sleep(3)

        # Click category chip
        try:
            chip = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Windows laptops')]")))
            chip.click()
            logging.info("Clicked 'Windows laptops' chip")
        except:
            logging.warning("Could not click 'Windows laptops' chip")

        time.sleep(4)

        # Apply price filters
        for price_id in ["$500_-_$749.99", "$750_-_$999.99", "$1000_-_$1249.99"]:
            try:
                price_checkbox = driver.find_element(By.ID, price_id)
                driver.execute_script("arguments[0].click();", price_checkbox)
                logging.info(f"Applied price filter: {price_id}")
                time.sleep(1)
            except Exception as e:
                logging.warning(f"Couldn't select price {price_id}: {e}")

        # Expand and apply brand filters
        try:
            show_all_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-show-more='brand_facet']")))
            driver.execute_script("arguments[0].click();", show_all_button)
            logging.info("Clicked 'Show all' for brand filters")
            time.sleep(2)
        except Exception as e:
            logging.warning(f"Couldn't click 'Show all' button: {e}")

        for brand in ["Apple", "Lenovo", "HP"]:
            try:
                brand_checkbox = driver.find_element(By.ID, brand)
                driver.execute_script("arguments[0].click();", brand_checkbox)
                logging.info(f"Applied brand filter: {brand}")
                time.sleep(1)
            except Exception as e:
                logging.warning(f"Couldn't select brand {brand}: {e}")

        # Close modal if appears
        try:
            modal = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='sheet-id-header']"))
            )
            close_button = driver.find_element(By.CSS_SELECTOR, "[data-testid='sheet-id-closeButton']")
            driver.execute_script("arguments[0].click();", close_button)
            logging.info("Closed modal after brand filter")
        except:
            logging.info("No modal appeared")

        # Apply rating filter
        try:
            rating_label = wait.until(EC.presence_of_element_located((By.XPATH, "//label[contains(., '4') and contains(., 'Up')]")))
            rating_input = rating_label.find_element(By.TAG_NAME, "input")
            driver.execute_script("arguments[0].click();", rating_input)
            logging.info("Applied rating filter: 4 stars & up")
            time.sleep(1)
        except Exception as e:
            logging.warning(f"Rating filter error: {e}")

        logging.info("Waiting 10 seconds for full data load")
        time.sleep(10)
        logging.info("Scrolling through all pages...")
        scroll_through_all_pages(driver)

        # Parse and extract
        html = driver.page_source
        with open("logs/rendered_page.html", "w", encoding="utf-8") as f:
            f.write(html)

        extract_filtered_data_from_html(html)
        export_to_excel()

    except Exception as e:
        driver.save_screenshot("logs/error_screenshot.png")
        logging.error(f"An error occurred: {e}", exc_info=True)
        print("❌ Filtering failed. Check logs and screenshot.")
    finally:
        driver.quit()
        logging.info("Browser closed.")

if __name__ == "__main__":
    main()
