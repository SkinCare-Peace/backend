import json
from fastapi import HTTPException
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from db.database import db
from schemas.cosmetic_recommendation import ProductRecommendation
from typing import Dict, List
from collections import defaultdict
from core.config import settings
from openai import OpenAI

OPENAI_KEY = settings.openai_key

client = OpenAI(api_key=OPENAI_KEY)
function_schema = {
    "name": "generate_recommendation_reason",
    "description": "사용자의 피부 타입과 고민, 제품 정보를 기반으로 추천 이유를 생성합니다.",
    "parameters": {
        "type": "object",
        "properties": {
            "reason": {
                "type": "string",
                "description": "제품을 추천하는 이유",
            },
        },
        "required": ["reason"],
    },
}


def recommend_cosmetics(
    user_skin_type: str,
    user_concerns: List[str],
    cosmetic_types: str,
    allergic_ingredients: List[str],
    budget: int,
) -> List[ProductRecommendation]:
    # 1. 데이터 로딩
    cursor = db["oliveyoung_products"].find()
    df = pd.DataFrame(list(cursor))

    # 1.1 고민별 성분 데이터 로딩
    concern_ingredient_df = pd.DataFrame(list(db["ing_concern_score"].find()))
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
        df["ingredients"].str.replace(r"[^\w\s|]", "", regex=True).str.split(r"\|")
    )
    df["ingredients_list"] = df["ingredients_list"].apply(
        lambda x: [ingredient.strip().lower() for ingredient in x]
    )

    # 3. 추천 알고리즘 구성

    # 3.2 필터링 단계
    # 3.2.1 화장품 종류 필터링
    filtered_df = df[df["cosmetic_type"].isin([cosmetic_types])]

    # 3.2.3 알레르기 및 비선호 성분 필터링
    def contains_allergic_ingredient(ingredients, allergic_ingredients):
        return any(
            allergic.lower() in ingredient
            for allergic in allergic_ingredients
            for ingredient in ingredients
        )

    print(filtered_df["ingredients_list"])

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
        matching_ingredients: Dict[str, Dict[str, int]] = defaultdict(dict)

        for ingredient in ingredients:
            for concern in user_concerns:
                effectiveness = ingredient_effectiveness.get(ingredient, {}).get(
                    concern, 0
                )
                total_effectiveness += effectiveness
                if effectiveness > 0:
                    matching_ingredients[concern][ingredient] = effectiveness

        # max_total = len(user_concerns) * 5  # 각 고민당 최대 5점
        # total_effectiveness = min(
        #     total_effectiveness, max_total
        # )  # 최대 총점을 초과하지 않도록 캡핑

        # concern_score = total_effectiveness / max_total if max_total else 0

        # return concern_score, matching_ingredients
        return total_effectiveness, matching_ingredients

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
    concern_scores = pd.DataFrame(concern_results.apply(lambda x: x[0]))
    filtered_df["concern_score"] = scaler.fit_transform(concern_scores)
    filtered_df["matching_ingredients"] = concern_results.apply(lambda x: x[1])

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
    top_products = filtered_df.sort_values(by="total_score", ascending=False).head(3)

    recommendations = []
    for index, product in top_products.iterrows():
        prompt = f"""
        당신은 전문적인 스킨케어 컨설턴트이며, 비둘기 캐릭터입니다. 아래의 정보를 바탕으로 사용자가 이해하기 쉽도록 제품을 추천하는 이유를 간결하게 작성해 주세요:

        사용자 피부 타입: {user_skin_type}
        사용자 피부 고민: {', '.join(user_concerns)}
        제품명: {product['name']}
        브랜드: {product['brand']}
        피부 타입 점수: {product['skin_type_score']}
        피부 고민 점수: {product['concern_score']}
        순위 점수: {product['rank_score']}
        가격 점수: {product['price_score']}
        매칭된 성분: {product['matching_ingredients']}

        추천 이유는 제품이 사용자의 피부 타입과 고민에 어떻게 부합하는지, 매칭된 성분과 전반적인 이점을 강조하여 작성해 주세요.
        모든 점수는 0부터 1까지 이루어진다.
        
        응답은 한국어로 한다. 최소 1줄 최대 2줄로 작성한다. 문장은 '-요'체로 작성한다.
        제품명을 이유에 언급하지 않는다. 성분을 근거로 한 설명만을 작성한다. 구체적인 점수는 언급하지 않는다.
        ex) '건성 피부에 적합한 히알루론산이 함유되어 있고, 여드름 고민 해결에 도움이되는 샐리실릭산이 함유되어 있어요.'
        """
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "당신은 전문적인 스킨케어 컨설턴트이며, 비둘기 캐릭터입니다. 아래의 정보를 바탕으로 사용자가 이해하기 쉽도록 제품을 추천하는 이유를 간결하게 작성해 주세요:",
                },
                {"role": "user", "content": prompt},
            ],
            functions=[function_schema],  # type: ignore
            function_call={"name": "generate_recommendation_reason"},
        )
        response = response.choices[0].message.function_call
        if not response:
            raise HTTPException(
                status_code=500, detail="Failed to generate recommendation reason"
            )
        reason = json.loads(response.arguments)["reason"]

        recommendation = ProductRecommendation(
            _id=str(product["_id"]),
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
            reason=reason,
            image_url=product.get("image_url", ""),
        )
        recommendations.append(recommendation)

    return recommendations
