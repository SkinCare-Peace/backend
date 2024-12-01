import collections
import sys
import os

import gridfs
import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import re
import time
from tqdm import tqdm
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from db.database import db
from urllib.parse import urljoin

if not hasattr(collections, "Callable"):
    collections.Callable = collections.abc.Callable  # type: ignore

logging.basicConfig(
    filename="data/scraping_errors.log",
    level=logging.ERROR,
    format="%(asctime)s %(levelname)s %(message)s",
)

fs = gridfs.GridFS(db)

# Chrome 드라이버 초기화
driver = webdriver.Chrome()

# 화장품 유형 및 피부 유형 정의, cateId, cateId2
cosmetic_types = {
    "에센스": ["10000010001", "100000100010014"],
    "크림": ["10000010001", "100000100010015"],
    "로션": ["10000010001", "100000100010016"],
    "미스트": ["10000010001", "100000100010010"],
    "클렌징폼": ["10000010010", "100000100100001"],
    "클렌징오일": ["10000010010", "100000100100004"],
    "스크럽": ["10000010010", "100000100100007"],
    "필링": ["10000010010", "100000100100007"],
    "클렌징워터": ["10000010010", "100000100100005"],
    "클렌징밀크": ["10000010010", "100000100100005"],
    "선크림": ["10000010011", "100000100110006"],
    "선스틱": ["10000010011", "100000100110003"],
    "스킨": ["10000010001", "100000100010013"],
    "토너": ["10000010001", "100000100010013"],
    "세럼": ["10000010001", "100000100010014"],
    "앰플": ["10000010001", "100000100010014"],
    "오일": ["10000010001", "100000100010010"],
    "클렌징젤": ["10000010010", "100000100100001"],
    "클렌징밤": ["10000010010", "100000100100004"],
}

skin_types = {
    "민감성": "4656d6583a85bf2c2b893ad834260537",
    "건성": "379d3e9e0e9ee3482f209611ffe7028d",
    "여드름성": "0319bfdd22025888bbf9ce68042ddbc9",
    "지성": "a503660b7d1ea65e093646c5332ae0e7",
    "트러블성": "f927c44e51df9bc2e8d58d65fecc04ab",
    "복합성": "4a173d661a65b65a965f9613a813468f",
    "수부지": "7bc900f09a13ce16223a515dda501412",
    "중성": "032bf5b37e5032d4634d92e03637c0ea",
    "약건성": "1868965f7589d232c16e74e6bf07a529",
}


# 제품 상세 정보 추출 함수
def get_product_details(detail_url):

    try:
        driver.get(detail_url)
        # '구매정보' 탭 클릭을 기다리고 클릭
        buy_info_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "buyInfo"))
        )
        buy_info_tab.click()

        # 페이지가 로드될 시간을 기다림
        time.sleep(3)

        # 페이지 소스 파싱
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, "html.parser")

        # 제품명 추출 및 정리
        product_name_elem = soup.select_one(
            "#Contents > div.prd_detail_box.renew > div.right_area > div > p.prd_name"
        )
        if product_name_elem:
            product_name = product_name_elem.get_text(strip=True)
            cleaned_name = re.sub(
                r"\[.*?\]|\(.*?\)|기획|증정|세트|리필|\d+[mM][lL]|\d+\+\d+|\+.*|\/.*",
                "",
                product_name,
            ).strip()
        else:
            cleaned_name = "N/A"

        # 브랜드 추출
        brand_elem = soup.select_one("#moveBrandShop")
        brand = brand_elem.get_text(strip=True) if brand_elem else "N/A"

        # 가격 추출
        original_price_elem = soup.select_one(
            "#Contents > div.prd_detail_box.renew > div.right_area > div > div.price > span.price-1 > strike"
        )
        selling_price_elem = soup.select_one(
            "#Contents > div.prd_detail_box.renew > div.right_area > div > div.price > span.price-2 > strong"
        )
        selling_price = (
            selling_price_elem.get_text(strip=True).replace(",", "")
            if selling_price_elem
            else "0"
        )
        try:
            selling_price = int(selling_price)
        except ValueError:
            selling_price = 0

        original_price = (
            original_price_elem.get_text(strip=True).replace(",", "")
            if original_price_elem
            else selling_price
        )
        try:
            original_price = int(original_price)
        except ValueError:
            original_price = selling_price

        # 성분 추출
        try:
            ingredients_dt = soup.find(
                "dt", string=re.compile("화장품법에 따라 기재해야 하는 모든 성분")
            )
            if not ingredients_dt:
                raise AttributeError
            ingredients_dd = ingredients_dt.find_next_sibling("dd")
            if not ingredients_dd:
                raise AttributeError
            ingredients = ingredients_dd.get_text(strip=True)
            ing_list = re.sub(r"(?<!\d),(?!\d)", "\n", ingredients).split("\n")
            ingredients = " | ".join([ing.strip() for ing in ing_list])
        except AttributeError:
            ingredients = "N/A"
        try:
            volume_dt = soup.find("dt", string=re.compile("내용물의 용량 또는 중량"))
            if not volume_dt:
                raise AttributeError
            volume_dd = volume_dt.find_next_sibling("dd")
            if not volume_dd:
                raise AttributeError
            volume = volume_dd.get_text(strip=True)
        except AttributeError:
            volume = "N/A"

        # 리뷰 수 추출
        review_count_elem = soup.select_one("#repReview > em")
        if review_count_elem:
            review_count_text = review_count_elem.get_text(strip=True)
            review_count = int(re.sub(r"[^\d]", "", review_count_text))
        else:
            review_count = 0

        # 이미지 URL 추출 및 이미지 데이터 저장
        image_elem = soup.select_one("#mainImg")
        if image_elem and "src" in image_elem.attrs:
            image_url = image_elem["src"]
            if isinstance(image_url, list):
                image_url = image_url[0]
            # 이미지 URL이 상대경로일 경우 절대경로로 변환
            if not image_url.startswith("http"):
                image_url = urljoin(detail_url, image_url)
            # 이미지 다운로드 및 MongoDB에 저장
            try:
                image_response = requests.get(image_url)
                image_data = image_response.content

                # 이미지 데이터를 GridFS에 저장
                image_filename = image_url.split("/")[-1]
                image_id = fs.put(image_data, filename=image_filename)

            except Exception as e:
                logging.error(
                    f"Failed to download or store image from {image_url}: {e}"
                )
                image_id = None
        else:
            image_url = "N/A"
            image_id = None

        return {
            "brand": brand,
            "name": cleaned_name,
            "original_price": original_price,
            "selling_price": selling_price,
            "volume": volume,
            "ingredients": ingredients,
            "review_count": review_count,
            "link": detail_url,
            "image_url": image_url,
            "image_id": image_id,
        }
    except Exception as e:
        error_message = f"Failed to process {detail_url}: {str(e)}"
        logging.error(error_message)
        return None


# 제품 정보 스크래핑 함수
def get_product_info(
    cosmetic_type, cateId, cateId2, skin_type_name, skin_type_id, filename
):
    page = 1
    total_products_found = 0

    while total_products_found < 20:
        # 검색 URL 생성
        url = f"https://www.oliveyoung.co.kr/store/search/getSearchMain.do?query={cosmetic_type}&attr_check3={skin_type_id}&pageIdx={page}&cateId={cateId}&cateId2={cateId2}"

        try:
            driver.get(url)

            # 제품 목록 로딩 대기
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, "ul#w_cate_prd_list li.flag.li_result")
                )
            )

            # 페이지 소스 파싱
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, "html.parser")

            # 제품 목록 추출
            products = soup.select("ul#w_cate_prd_list li.flag.li_result")
            if not products or total_products_found + len(products) > 20:
                products = products[
                    : 20 - total_products_found
                ]  # Limit to remaining products if close to 70

            total_products_found += len(products)

            for index, product in enumerate(
                tqdm(
                    products,
                    desc=f"Processing {cosmetic_type} & {skin_type_name} (Page {page})",
                    total=len(products),
                    leave=True,
                ),
                start=1,
            ):
                a_tag = product.find("a", class_="prd_thumb", href=True)
                if a_tag:
                    product_url: str = a_tag["href"]  # type: ignore
                    if product_url.startswith("https://www.oliveyoung.co.kr"):
                        full_product_url = product_url

                        try:
                            # 제품 상세 정보 추출
                            product_details = get_product_details(full_product_url)

                            if product_details:
                                # 추가 정보 삽입
                                product_details["cosmetic_type"] = cosmetic_type
                                product_details["skin_type"] = skin_type_name
                                product_details["rank"] = (
                                    index + (page - 1) * 24
                                )  # 페이지당 24개 가정

                                db["oliveyoung_products"].insert_one(product_details)  # type: ignore

                        except Exception as e:
                            error_message = f"Failed to process {full_product_url}: {e}"
                            logging.error(error_message)
                    elif "javascript:;" not in product_url:
                        logging.error(f"Invalid URL skipped: {product_url}")
                else:
                    logging.error(
                        f"No product URL found for product index {index} on page {page}"
                    )

            # 다음 페이지로 이동
            try:
                if page % 10 == 0:
                    # Case 2: For multiples of 10, check if the "Next" button is available
                    next_button = driver.find_elements(
                        By.CSS_SELECTOR, "#Contents > div > div.pageing.new > a.next"
                    )
                    if next_button:
                        page += 1
                    else:
                        break  # No "Next" button found, exit the loop
                else:
                    # Case 1: For pages 1–9, check if a link for the next page exists
                    paging_links = driver.find_elements(
                        By.CSS_SELECTOR, "div.pageing.new a[title='Paging']"
                    )
                    next_page_exists = any(
                        int(link.get_attribute("onclick").split("'")[1]) == (page * 24)  # type: ignore
                        for link in paging_links
                    )

                    if next_page_exists:
                        page += 1
                    else:
                        break  # No further pages; exit the loop for this skin type-cosmetic type

                time.sleep(1)  # 요청 사이 대기

            except Exception:
                # Case 3: Exit the loop if neither condition is met or no "Next" button is available
                break

        except Exception as e:
            error_message = f"Failed to load or process page {page} for {cosmetic_type} and {skin_type_name}: {e}"
            logging.error(error_message)
            break

    print(
        f"Total products found and processed for {cosmetic_type} and {skin_type_name}: {total_products_found}"
    )


# 메인 스크래핑 로직
def main():
    filename = "data/oliveyoung_products_all.csv"

    for type_name, cat_list in cosmetic_types.items():
        cateId, cateId2 = cat_list
        for skin_type_name, skin_type_id in skin_types.items():
            print(
                f"Starting scraping for cosmetic type: {type_name}, skin type: {skin_type_name}"
            )
            get_product_info(
                type_name, cateId, cateId2, skin_type_name, skin_type_id, filename
            )

    driver.quit()


if __name__ == "__main__":
    main()
