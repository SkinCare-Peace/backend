import requests
from bs4 import BeautifulSoup
import csv
import collections
import re
import time
from tqdm import tqdm  # 진행 상황 표시를 위한 라이브러리
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

if not hasattr(collections, 'Callable'):
    collections.Callable = collections.abc.Callable

logging.basicConfig(filename='data/scraping_errors.log', level=logging.ERROR, 
                    format='%(asctime)s %(levelname)s %(message)s')

# Selenium setup
driver = webdriver.Chrome()

# Function to extract product details from the product detail page
def get_product_details(detail_url):
    driver.get(detail_url)
    
    try:
        # '구매정보' 탭 클릭을 기다리고 클릭
        buy_info_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "buyInfo"))
        )
        buy_info_tab.click()
        
        # 페이지가 로드될 시간을 기다림
        time.sleep(3)
        
        # 페이지 소스 가져오기
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
    
        # Extract product name
        product_name = soup.select_one('p.prd_name').get_text(strip=True)
    
        # Clean product name
        cleaned_name = re.sub(r"\[.*?\]|\(.*?\)|기획|증정|세트|리필|\d+[mM][lL]|\d+\+\d+|\+.*|\/.*", "", product_name).strip()
    
        # Extract product brand
        brand = soup.select_one('p.prd_brand a').get_text(strip=True)
    
        # Extract product price (may need error handling for unavailable data)
        try:
            price = soup.select_one('span.price-2 strong').get_text(strip=True)
        except AttributeError:
            price = 'N/A'
    
        # Extract ingredients from "구매정보" 탭
        try:
            ingredients = soup.find('dt', string='화장품법에 따라 기재해야 하는 모든 성분').find_next('dd').get_text(strip=True)
        except AttributeError:
            ingredients = 'N/A'
    
        return {'brand': brand, 'name': cleaned_name, 'price': price, 'ingredients': ingredients}

    except Exception as e:
        error_message = f"Failed to process {detail_url}: {e}"
        logging.error(error_message)  # 로그에 오류 기록
        return None

# Function to scrape products from a category and navigate to their detail pages
def get_product_info(catNo):
    product_list = []
    page = 1
    total_products_found = 0
    
    while True:
        # URL definition (category number and page number)
        url = f"https://www.oliveyoung.co.kr/store/display/getMCategoryList.do?dispCatNo=1000001000100{catNo}&pageIdx={page}&rowsPerPage=100&prdSort=03"
        
        # Request the page
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract category name
        category_name = soup.select_one('div.titBox h1').get_text(strip=True)
        
        # Extract all product links
        products = soup.select('ul.cate_prd_list li a')
        
        # Track total products found for progress bar
        total_products_found += len(products)
        
        if not products:
            break
        
        # Create a progress bar for the products
        for index, product in enumerate(tqdm(products, desc=f"Processing products in category {catNo} (Page {page})", total=len(products), leave=True), start=1):
            product_url = product.get('href')
            
            # Check if the URL is valid and starts with "/store/goods" (filter out "javascript:;" links)
            if product_url and product_url.startswith("https://www.oliveyoung.co.kr/"):
                full_product_url = product_url
                
                try:
                    # Get the product details from the detail page
                    product_details = get_product_details(full_product_url)
                    
                    if product_details:
                        # Add category and rank
                        product_details['category'] = category_name
                        product_details['rank'] = index + (page - 1) * 100

                        # Add the product details to the list
                        product_list.append(product_details)
                    
                except Exception as e:
                    error_message = f"Failed to process {full_product_url}: {e}"
                    logging.error(error_message)  # 로그에 오류 기록
            elif "javascript:;" not in product_url:
                logging.error(f"Invalid URL skipped: {product_url}")
        
        # Move to the next page
        page += 1
        time.sleep(1)  # Pause between requests to avoid being blocked
    
    print(f"Total products found and processed: {total_products_found}")
    return product_list

# Function to save data to a CSV file
def save_to_csv(product_list, filename):
    # Save the data to a CSV file
    with open(filename, mode='w', newline='', encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=['category', 'rank', 'brand', 'name', 'price', 'ingredients'], quoting=csv.QUOTE_NONNUMERIC)
        writer.writeheader()  # Write the header
        writer.writerows(product_list)  # Write the data
    print(f"CSV saved: {filename}")

# Crawl categories from 13 to 17
all_products = []
categories = [13, 14, 15, 16, 17, 10]

# Create a progress bar for categories
for catNo in tqdm(categories, desc="Processing categories", leave=True):
    products = get_product_info(str(catNo))
    all_products.extend(products)  # Merge all product information

# Save the data to a CSV file
filename = 'data/oliveyoung_products_with_ingredients.csv'
save_to_csv(all_products, filename)

# Close the Selenium driver after completion
driver.quit()
