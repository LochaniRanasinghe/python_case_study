from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import logging
import time
import os
from bs4 import BeautifulSoup
import json
import re

# Setup logging and folders
os.makedirs("logs", exist_ok=True)
os.makedirs("data", exist_ok=True)
os.makedirs("data/products", exist_ok=True)

logging.basicConfig(
    filename='logs/app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def setup_driver():
    options = Options()
    # options.add_argument('--headless')  # Uncomment for headless mode
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def extract_filtered_data_from_html(html):
    soup = BeautifulSoup(html, "html.parser")

    product_names, product_prices, product_ratings, review_counts, product_links = [], [], [], [], []

    product_cards = soup.find_all("li", class_="product-list-item")
    logging.info(f"Found {len(product_cards)} product cards")

    for card in product_cards:
        try:
            product_names.append(card.select_one("h2.product-title").get_text(strip=True))
        except:
            product_names.append("N/A")

        try:
            price = card.select_one("div[data-testid='medium-customer-price']").get_text(strip=True)
            product_prices.append(price)
        except:
            product_prices.append("N/A")

        try:
            rating = card.select_one(".c-ratings-reviews .visually-hidden").get_text(strip=True)
            product_ratings.append(rating)
        except:
            product_ratings.append("N/A")

        try:
            review = card.select_one(".c-reviews").get_text(strip=True).strip("()")
            review_counts.append(review)
        except:
            review_counts.append("0")

        try:
            href = card.select_one("a.product-list-item-link")["href"]
            full_link = href if href.startswith("http") else "https://www.bestbuy.com" + href
            product_links.append(full_link)
        except:
            product_links.append("N/A")

    products = []
    for i in range(len(product_names)):
        products.append({
            "name": product_names[i],
            "link": product_links[i],
            "price": product_prices[i],
            "rating": product_ratings[i],
            "reviews": review_counts[i],
            "sku": "N/A",
            "model": "N/A"
        })

    with open("data/filtered_products.json", "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)

    logging.info("✅ Product data saved to data/filtered_products.json")
    print(f"✅ {len(products)} products extracted and saved.")

def scrape_product_detail(driver, product, index):
    url = product.get("link")
    if not url or url == "N/A":
        return

    print(f"🔍 [{index+1}] Visiting: {url}")
    try:
        driver.get(url)
        time.sleep(2)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        specs = {}
        try:
            rows = soup.select("div.row")
            for row in rows:
                label = row.select_one("div.row-title")
                value = row.select_one("div.row-value")
                if label and value:
                    specs[label.text.strip()] = value.text.strip()
        except Exception as e:
            logging.warning(f"Specs not found for {url}: {e}")

        reviews = []
        try:
            while True:
                review_elements = soup.select("div.review-item")
                for r in review_elements:
                    try:
                        rating = r.select_one(".c-review-average").text.strip()
                        title = r.select_one(".review-title").text.strip()
                        body = r.select_one(".pre-white-space").text.strip()
                        reviews.append({
                            "title": title,
                            "rating": rating,
                            "body": body
                        })
                    except:
                        continue

                try:
                    next_button = driver.find_element(By.CSS_SELECTOR, ".review-pagination .pagination-button[aria-label='Next Page']")
                    if "disabled" in next_button.get_attribute("class"):
                        break
                    driver.execute_script("arguments[0].click();", next_button)
                    time.sleep(2)
                    soup = BeautifulSoup(driver.page_source, "html.parser")
                except:
                    break
        except Exception as e:
            logging.warning(f"No reviews found for {url}: {e}")

        full_data = {
            "basic_info": product,
            "specifications": specs,
            "reviews": reviews
        }

        slug = re.sub(r"[^\w\-]", "_", product["name"])[:100]
        with open(f"data/products/{slug}.json", "w", encoding="utf-8") as f:
            json.dump(full_data, f, indent=2, ensure_ascii=False)

        print(f"✅ Saved: {slug}.json")

    except TimeoutException:
        print(f"❌ Timeout loading {url}")
    except Exception as e:
        logging.error(f"Error scraping product page {url}: {e}")

def collect_advanced_data():
    driver = setup_driver()
    try:
        with open("data/filtered_products.json", "r", encoding="utf-8") as f:
            products = json.load(f)

        for i, product in enumerate(products):
            scrape_product_detail(driver, product, i)
            time.sleep(2 + i % 3)  # Rate limiting
    finally:
        driver.quit()
        print("🧹 Browser closed.")

def main():
    logging.info("Starting browser")
    driver = setup_driver()

    try:
        driver.get("https://www.bestbuy.com/?intl=nosplash")
        logging.info("Navigated to BestBuy")
        wait = WebDriverWait(driver, 15)

        try:
            us_link = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a.us-link"))
            )
            us_link.click()
            logging.info("Clicked United States link")
        except:
            logging.info("No country splash shown")

        search_bar = wait.until(EC.presence_of_element_located((By.ID, "autocomplete-search-bar")))
        search_bar.clear()
        search_bar.send_keys("laptop")
        search_button = wait.until(EC.element_to_be_clickable((By.ID, "autocomplete-search-button")))
        search_button.click()
        logging.info("Search submitted")
        time.sleep(3)

        try:
            chip = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Windows laptops')]")))
            chip.click()
            logging.info("Clicked 'Windows laptops' chip")
        except:
            logging.warning("Could not click 'Windows laptops' chip")

        time.sleep(4)
        logging.info("Applying filters...")

        for price_id in ["$500_-_$749.99", "$750_-_$999.99", "$1000_-_$1249.99"]:
            try:
                price_checkbox = driver.find_element(By.ID, price_id)
                driver.execute_script("arguments[0].click();", price_checkbox)
                logging.info(f"Applied price filter: {price_id}")
                time.sleep(1)
            except Exception as e:
                logging.warning(f"Couldn't select price {price_id}: {e}")

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

        html = driver.page_source
        with open("logs/rendered_page.html", "w", encoding="utf-8") as f:
            f.write(html)

        extract_filtered_data_from_html(html)

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
    collect_advanced_data()
