import pandas as pd
from sklearn.preprocessing import MinMaxScaler

# 전역 변수 선언: 피부 고민 및 피부 타입별 추천 성분 사전
concern_ingredient_dict = {
    "여드름성": [
        "노니추출물",
        "노니열매추출물",
        "병풀추출물",
        "병풀단백질추출물",
        "병풀오일",
        "병풀잎수",
        "프로폴리스추출물",
        "알란토인",
        "캐모마일꽃추출물",
        "캐모마일꽃수",
        "캐모마일꽃오일",
        "감초추출물",
        "녹차수",
        "녹차오일",
        "녹차추출물",
        "약모밀추출물",
        "브로콜리추출물",
        "브로콜리싹추출물",
        "창포뿌리추출물",
        "오이열매추출물",
        "오이추출물",
    ],
    "건성": [
        "노니추출물",
        "노니열매추출물",
        "바다포도추출물",
        "꿀",
        "꿀추출물",
        "베타인",
        "브로콜리추출물",
        "브로콜리싹추출물",
        "맥주효모추출물",
    ],
    "지성": [
        "오이열매추출물",
        "오이추출물",
        "노니추출물",
        "노니열매추출물",
        "알란토인",
        "황금추출물",
        "프로폴리스추출물",
        "녹차수",
        "녹차오일",
        "녹차추출물",
        "개똥쑥추출물",
        "브로콜리추출물",
        "브로콜리싹추출물",
        "병풀뿌리추출물",
        "병풀오일",
        "병풀잎수",
        "병풀잎추출물",
        "병풀추출물",
    ],
    "민감성": [
        "노니추출물",
        "노니열매추출물",
        "황금추출물",
        "알란토인",
        "바다포도추출물",
        "프로폴리스추출물",
        "캐모마일꽃수",
        "캐모마일꽃오일",
        "캐모마일꽃추출물",
        "오이열매추출물",
        "오이추출물",
        "개똥쑥추출물",
        "브로콜리싹추출물",
        "브로콜리추출물",
        "맥주효모추출물",
    ],
}


def recommend_cosmetics(
    csv_file_path,
    user_skin_type,
    user_concerns,
    preferred_cosmetic_types,
    allergic_ingredients,
    budget,
):
    # 1. 데이터 로딩
    df = pd.read_csv(csv_file_path)

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

    # 3.2.2 피부 타입 필터링
    filtered_df = filtered_df[filtered_df["skin_type"] == user_skin_type]

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
        return

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
        total_concerns = len(user_concerns)
        matched_concerns = 0
        matching_ingredients = set()

        for concern in user_concerns:
            concern_ingredients = concern_ingredient_dict.get(concern, [])
            concern_ingredients_lower = [ing.lower() for ing in concern_ingredients]
            if concern_ingredients_lower:
                matched = set(ingredients) & set(concern_ingredients_lower)
                if matched:
                    matched_concerns += 1
                    matching_ingredients.update(matched)

        if total_concerns > 0:
            concern_score = matched_concerns / total_concerns  # 매칭된 고민의 비율
        else:
            concern_score = 0

        return concern_score, matching_ingredients

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
    filtered_df["matching_ingredients"] = concern_results.apply(lambda x: list(x[1]))

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

    # 5. 결과 출력
    top_products = filtered_df.sort_values(by="total_score", ascending=False).head(5)

    for index, product in top_products.iterrows():
        print(f"제품명: {product['name']}")
        print(f"브랜드: {product['brand']}")
        print(f"판매가: {product['selling_price']}원")
        print(f"링크: {product['link']}")
        print(f"총점: {product['total_score']:.2f}")

        # 추천 이유 표시
        reasons = []
        if product["skin_type_score"] == 1:
            reasons.append("사용자의 피부 타입과 일치함")
        if product["matching_ingredients"]:
            matching_ings = ", ".join(product["matching_ingredients"])
            reasons.append(f"피부 고민에 맞는 성분 포함: {matching_ings}")
        print("추천 이유:", "; ".join(reasons))
        print("----------------------------------------------------")


if __name__ == "__main__":
    # csv_file_path: CSV 파일의 경로 또는 링크
    csv_file_path = "data/oliveyoung_products_all.csv"

    # 사용자 입력값 설림림
    user_skin_type = "수부지"  # 사용자 피부 타입
    user_concerns = ["여드름성"]  # 사용자 피부 고민 리스트
    preferred_cosmetic_types = ["앰플"]  # 추천받고자 하는 화장품 종류 리스트
    allergic_ingredients = ["녹차추출물", "파라벤"]  # 알레르기나 기피 성분 리스트
    budget = 25000  # 예산 상한선

    # 함수 호출
    recommend_cosmetics(
        csv_file_path,
        user_skin_type,
        user_concerns,
        preferred_cosmetic_types,
        allergic_ingredients,
        budget,
    )
