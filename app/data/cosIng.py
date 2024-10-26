import pandas as pd
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver import ActionChains
import time
from tqdm import tqdm
import csv
import os

# 드라이버 설정
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.get("https://ec.europa.eu/growth/tools-databases/cosing/")
action = ActionChains(driver)


def get_eff(ingr_eng_name):
    try:
        # 성분명 입력 후 검색
        search_box = WebDriverWait(driver, 6).until(
            EC.presence_of_element_located((By.ID, "keyword"))
        )
        search_box.clear()
        search_box.send_keys(ingr_eng_name)

        # 검색 버튼 클릭
        search_button = WebDriverWait(driver, 6).until(
            EC.element_to_be_clickable(
                (
                    By.CSS_SELECTOR,
                    "body > app-root > ecl-app > div > div > div > div > main > ng-component > form > div > div:nth-child(5) > div > button",
                )
            )
        )
        driver.execute_script("arguments[0].click();", search_button)

        # 검색 결과가 로드될 때까지 대기하고 검색 결과 테이블을 찾음
        ing_link = WebDriverWait(driver, 6).until(
            EC.element_to_be_clickable(
                (
                    By.CSS_SELECTOR,
                    "body > app-root > ecl-app > div > div > div > div > main > ng-component > app-results-subs > table > tbody > tr:nth-child(1) > td:nth-child(2) > a",
                )
            )
        )
        driver.execute_script("arguments[0].click();", ing_link)

        try:

            # 성분 효능 부분 로딩 대기
            functions_table = WebDriverWait(driver, 6).until(
                EC.presence_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        "body > app-root > ecl-app > div > div > div > div > main > ng-component > table > tbody > tr:nth-child(7) > td:nth-child(2) > ul",
                    )
                )
            )
            element = driver.find_element(
                By.CSS_SELECTOR,
                "body > app-root > ecl-app > div > div > div > div > main > ng-component > h1",
            )
            searched_ingr = element.text.replace("Ingredient: ", "")

            # 효능 정보 추출
            functions_list = functions_table.find_elements(By.TAG_NAME, "li")
            functions = [func.text for func in functions_list]
            functions_str = " | ".join(functions)

            # 검색 페이지로 다시 돌아가기
            driver.back()
            time.sleep(2)  # 로딩 시간 고려하여 잠시 대기

            return searched_ingr, functions_str
        except Exception as e:
            driver.back()
            time.sleep(2)  # 로딩 시간 고려하여 잠시 대기
            raise e

    except Exception as e:
        with open("data/error_log.txt", "a", encoding="utf-8-sig") as log_file:
            log_file.write(f"cosIng: Error processing {ingr_eng_name}: {e}\n")
        return None


def get_eng(ingr_kor_name):
    params = {
        "serviceKey": "3XXaWVycuT/8K4JD0vZ6htcaMaTJyGlZ9DTutVeaFa+Z+FQbvamRg9LIqn7BOSmHGRd9WVKoH4Iut2llh48h5A==",
        "pageNo": 1,
        "numOfRows": 10,
        "type": "json",
        "INGR_KOR_NAME": ingr_kor_name,
    }
    headers = {"accept": "*/*"}
    try:
        response = requests.get(
            "http://apis.data.go.kr/1471000/CsmtcsIngdCpntInfoService01/getCsmtcsIngdCpntInfoService01",
            params=params,
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()
        items = data.get("body", {}).get("items", {})
        if not items:
            return "영어명 없음"
        for item in items:
            if item.get("INGR_KOR_NAME") == ingr_kor_name:
                eng_name = item.get("INGR_ENG_NAME", "영어명 없음")
                return eng_name
        return "영어명 없음"

    except requests.exceptions.RequestException as e:
        with open("data/error_log.txt", "a", encoding="utf-8-sig") as log_file:
            log_file.write(f"cosIng:Request error for {ingr_kor_name}: {e}\n")
        return None
    except Exception as e:
        with open("data/error_log.txt", "a", encoding="utf-8-sig") as log_file:
            log_file.write(f"cosIng:Unknown error for {ingr_kor_name}: {e}\n")
        return None


def extract_unique_ingredients(csv_file_path):
    df = pd.read_csv(csv_file_path, encoding="utf-8-sig")
    ingredients_series = df["ingredients"].astype(str).fillna("")
    unique_ingredients = set()
    for ingredients in ingredients_series:
        ingredient_list = ingredients.split("|")
        for ingredient in ingredient_list:
            cleaned_ingredient = ingredient.strip()
            unique_ingredients.add(cleaned_ingredient)
    return sorted(unique_ingredients)


if __name__ == "__main__":
    csv_file = "data/products_with_ing_formatted_kor.csv"
    output_file = "data/ingredient_functions.csv"

    # 결과 CSV 파일의 헤더 확인 및 파일 초기화
    if not os.path.exists(output_file):
        with open(output_file, "w", newline="", encoding="utf-8-sig") as csvfile:
            writer = csv.writer(csvfile, quoting=csv.QUOTE_NONNUMERIC)
            writer.writerow(
                ["Korean Name", "English Name", "Searched Eng Name", "Functions"]
            )

    unique_ingredients = extract_unique_ingredients(csv_file)
    found = False
    for ingr in tqdm(unique_ingredients, desc="Processing ingredients", leave=True):
        if ingr == "더덕뿌리추출물":
            found = True
            continue
        if not found:
            continue
        if len(ingr) > 25:
            with open("data/error_log.txt", "a", encoding="utf-8-sig") as log_file:
                log_file.write(f"cosIng: Ingredient name too long: {ingr[:25]}...\n")
            continue

        eng_name = get_eng(ingr)

        if eng_name and eng_name != "영어명 없음":
            temp = get_eff(eng_name)
            if temp:
                searched_ingr, functions = temp
                # 정보를 CSV에 저장
                with open(
                    output_file, "a", newline="", encoding="utf-8-sig"
                ) as csvfile:
                    writer = csv.writer(csvfile, quoting=csv.QUOTE_NONNUMERIC)
                    writer.writerow([ingr, eng_name, searched_ingr, functions])
            else:
                with open("data/error_log.txt", "a", encoding="utf-8-sig") as log_file:
                    log_file.write(f"cosIng: No functions for {ingr} : {eng_name}\n")
        else:
            with open("data/error_log.txt", "a", encoding="utf-8-sig") as log_file:
                log_file.write(f"cosIng: No English for {ingr}\n")
