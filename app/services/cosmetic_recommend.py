from fastapi import HTTPException
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from db.database import products_collection
from schemas.recommendation import ProductRecommendation
from typing import List


def recommend_cosmetics(
    user_skin_type: str,
    user_concerns: List[str],
    preferred_cosmetic_types: List[str],
    allergic_ingredients: List[str],
    budget: int,
) -> List[ProductRecommendation]:
    # 1. 데이터 로딩
    cursor = products_collection.find()
    df = pd.DataFrame(list(cursor))

    # 1.1 고민별 성분 데이터 로딩
    concern_ingredient_df = pd.read_csv(
        "data/ingredient_effectiveness_scores.csv", encoding="utf-8-sig"
    )
    concern_ingredient_df.fillna("", inplace=True)
    # 1.2 성분별 고민 매핑 딕셔너리 생성
    ingredient_effectiveness = {}
    for index, row in concern_ingredient_df.iterrows():
        ingredient = row["Korean Name"].strip().lower()
        # 나머지 모든 열: 고민에 대한 효능 점수
        concerns = {
            concern: row[concern] for concern in concern_ingredient_df.columns[1:]
        }

        ingredient_effectiveness[ingredient] = concerns

    # 2. 데이터 전처리
    # 2.1 중복 제거 및 인덱스 재설정
    df.drop_duplicates(inplace=True)
    df.reset_index(drop=True, inplace=True)

    # 2.2 결측치 처리
    df.dropna(inplace=True)

    # 2.3 데이터 타입 변환
    df["original_price"] = df["original_price"].astype(int)
    df["selling_price"] = df["selling_price"].astype(int)
    df["review_count"] = df["review_count"].astype(int)
    df["rank"] = df["rank"].astype(int)

    # 2.4 피부 타입 및 화장품 종류 표준화
    df["skin_type"] = df["skin_type"].str.strip().str.lower()
    df["cosmetic_type"] = df["cosmetic_type"].str.strip().str.lower()

    # 2.5 성분 데이터 전처리
    df["ingredients_list"] = (
        df["ingredients"].str.replace("[^\w\s|]", "", regex=True).str.split("\|")
    )
    df["ingredients_list"] = df["ingredients_list"].apply(
        lambda x: [ingredient.strip().lower() for ingredient in x]
    )

    # 3. 추천 알고리즘 구성

    # 3.2 필터링 단계
    # 3.2.1 화장품 종류 필터링
    filtered_df = df[df["cosmetic_type"].isin(preferred_cosmetic_types)]

    # # 3.2.2 피부 타입 필터링
    # filtered_df = filtered_df[filtered_df["skin_type"] == user_skin_type.lower()]

    # 3.2.3 알레르기 및 비선호 성분 필터링
    def contains_allergic_ingredient(ingredients, allergic_ingredients):
        return any(
            allergic.lower() in ingredient
            for allergic in allergic_ingredients
            for ingredient in ingredients
        )

    filtered_df["has_allergic"] = filtered_df["ingredients_list"].apply(
        lambda x: contains_allergic_ingredient(x, allergic_ingredients)
    )
    filtered_df = filtered_df[filtered_df["has_allergic"] == False]

    # 3.2.4 가격 필터링
    filtered_df = filtered_df[filtered_df["selling_price"] <= budget]

    if filtered_df.empty:
        print("조건에 맞는 제품이 없습니다.")
        raise HTTPException(status_code=404, detail="No products found")

    # 3.3 스코어링 단계
    scaler = MinMaxScaler()

    # 가격 역정규화 (가격이 낮을수록 점수가 높음)
    filtered_df["price_score"] = 1 - scaler.fit_transform(
        filtered_df[["selling_price"]]
    )

    # 순위 역정규화 (순위 숫자가 낮을수록 좋음)
    filtered_df["rank_score"] = 1 - scaler.fit_transform(filtered_df[["rank"]])

    # 3.3.2 피부 고민 및 피부 타입 매칭 점수
    def concern_match_score(ingredients, user_concerns):
        total_effectiveness = 0
        matching_ingredients = set()
        matched_concerns = set()

        for ingredient in ingredients:
            for concern in user_concerns:
                effectiveness = ingredient_effectiveness.get(ingredient, {}).get(
                    concern, 0
                )
                total_effectiveness += effectiveness
                if effectiveness > 0:
                    matching_ingredients.add(ingredient)
                    matched_concerns.add(concern)

        max_total = len(user_concerns) * 5  # 각 고민당 최대 5점
        total_effectiveness = min(
            total_effectiveness, max_total
        )  # 최대 총점을 초과하지 않도록 캡핑

        concern_score = total_effectiveness / max_total if max_total else 0

        return concern_score, matched_concerns, matching_ingredients

    # 3. 함수 적용 및 개별 점수 저장
    filtered_df["skin_type_score"] = filtered_df["skin_type"].apply(
        lambda product_skin_type: (
            1 if product_skin_type == user_skin_type.lower() else 0
        )
    )

    # 피부 고민 점수 계산
    concern_results = filtered_df["ingredients_list"].apply(
        lambda x: concern_match_score(x, user_concerns)
    )
    filtered_df["concern_score"] = concern_results.apply(lambda x: x[0])
    filtered_df["matched_concerns"] = concern_results.apply(lambda x: x[1])
    filtered_df["matching_ingredients"] = concern_results.apply(lambda x: list(x[2]))

    # 4. 총점 계산
    # 새로운 가중치 설정
    weight_skin_type = 10  # 피부 타입 매칭 가중치
    weight_concern = 8  # 피부 고민 매칭 가중치
    weight_rank = 8  # 판매량(순위) 가중치
    weight_price = 2  # 가격 가중치

    # 가격 역정규화 (가격이 낮을수록 점수가 높음)
    scaler = MinMaxScaler()
    filtered_df["price_score"] = 1 - scaler.fit_transform(
        filtered_df[["selling_price"]]
    )
    # 순위 역정규화 (순위 숫자가 낮을수록 좋음)
    filtered_df["rank_score"] = 1 - scaler.fit_transform(filtered_df[["rank"]])

    # 총점 계산
    filtered_df["total_score"] = (
        (
            filtered_df["skin_type_score"] * weight_skin_type
            + filtered_df["concern_score"] * weight_concern
            + filtered_df["rank_score"] * weight_rank
            + filtered_df["price_score"] * weight_price
        )
        / 28
        * 100
    )
    # 5. 결과 준비
    top_products = filtered_df.sort_values(by="total_score", ascending=False).head(5)

    recommendations = []
    for index, product in top_products.iterrows():
        recommendation = ProductRecommendation(
            name=product["name"],
            brand=product["brand"],
            selling_price=product["selling_price"],
            link=product["link"],
            skin_type_score=product["skin_type_score"],
            concern_score=product["concern_score"],
            rank_score=product["rank_score"],
            price_score=product["price_score"],
            total_score=product["total_score"],
            matching_ingredients=product["matching_ingredients"],
        )
        recommendations.append(recommendation)

    return recommendations
