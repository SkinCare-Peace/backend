import csv
import json
import logging
from typing import List
import pandas as pd
from tqdm import tqdm

import openai
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_KEY")

logging.basicConfig(
    filename="data/gpt_errors.log",
    level=logging.ERROR,
    format="%(asctime)s %(levelname)s %(message)s",
)

# ingredient_functions.csv 파일 로딩
functions_df = pd.read_csv("data/ingredient_functions.csv", encoding="utf-8-sig")
functions_df = functions_df[["Korean Name", "Functions"]]

# 성분명과 기능을 딕셔너리로 생성
ingredient_functions_dict = functions_df.set_index("Korean Name")["Functions"].to_dict()


# 고민 목록 정의
concern_list = [
    "여드름",
    "피지",
    "블랙헤드",
    "각질",
    "흉터",
    "모공",
    "홍조",
    "다크서클",
]

schema = {
    "name": "ingredient_effectiveness",
    "description": "Give an efficacy score from 0 to 5 to see how effective the cosmetic ingredients provided are for each of the following skin concerns: 여드름, 피지, 블랙헤드, 각질, 흉터, 모공, 홍조, 다크서클. The score ranges from 0 (no effect) to 5 (very effective)",
    "parameters": {
        "type": "object",
        "properties": {
            "effectiveness_scores": {
                "type": "object",
                "properties": {
                    concern: {"type": "integer", "minimum": 0, "maximum": 5}
                    for concern in concern_list
                },
            }
        },
    },
}

# CSV 파일 초기화
output_file = "data/ingredient_effectiveness_scores.csv"
# with open(output_file, "w", newline="", encoding="utf-8-sig") as csvfile:
#     writer = csv.writer(csvfile, quoting=csv.QUOTE_NONNUMERIC)
#     header = ["Korean Name"] + concern_list
#     writer.writerow(header)


checkpoint = "기장추출물"
# 성분별 효능 점수 수집
for ing, functions in tqdm(ingredient_functions_dict.items()):
    if ing == checkpoint:
        checkpoint = None
        continue
    if checkpoint:
        continue

    try:

        messages = [
            {
                "role": "system",
                "content": """You are an expert assistant specializing in cosmetic recommendations.
                    Your role is to evaluate the efficacy of cosmetic ingredients for specific skin concerns and provide a score based on how effective each ingredient is for addressing the following concerns: 
                    여드름, 피지, 블랙헤드, 각질, 흉터, 모공, 홍조, 다크서클.
                    Scoring Guidelines:
                    0 point: No significant correlation between the ingredient and the concern, or the ingredient is irrelevant (e.g., only used as a solvent or fragrance).
                    1 point: Very low efficacy or minimal effect.
                    2 points: Low efficacy.
                    3 points: Moderate efficacy.
                    4 points: High efficacy.
                    5 points: Very high efficacy.

                    Instructions:
                    - If the efficacy of any ingredient is uncertain, or if available data is inconclusive, set the score for the concern to 0.
                    - Only include the scores in the response. Do not provide explanations or additional information.
                    - For each skin concern listed, assess the ingredient’s efficacy and assign a score based on the guidelines above.
                    - If an ingredient is irrelevant (e.g., primarily used as a solvent or fragrance) or if data on efficacy is insufficient, assign a score of 0 for all concerns.
                    - Format your response as JSON, following the structure below:

                    {
                    "effectiveness_scores": {
                    "여드름": [Scores],
                    "피지": [Score],
                    "블랙헤드": [Score],
                    "각질": [Score],
                    "흉터": [Scores],
                    "모공": [Scores],
                    "홍조": [Score],
                    "다크서클": [Score]
                    }
                    }
                """,
            },
            {"role": "user", "content": f"ingredient: {ing}, functions: {functions}"},
        ]

        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=messages,  # type: ignore
            functions=[schema],  # type: ignore
            function_call={"name": "ingredient_effectiveness"},
            temperature=0,
        )

        function_call = response.choices[0].message.function_call
        if not function_call:
            logging.error(f"No function_call in response for ingredient: {ing}")
            continue

        args = json.loads(function_call.arguments)
        effectiveness_scores = args.get("effectiveness_scores")
        if not effectiveness_scores:
            logging.error(f"No effectiveness_scores for ingredient: {ing}")
            continue

        # 모든 고민에 대한 점수가 있는지 확인하고, 없으면 0로 기본 설정
        scores = [effectiveness_scores.get(concern, 0) for concern in concern_list]

        with open(output_file, "a", newline="", encoding="utf-8-sig") as csvfile:
            writer = csv.writer(csvfile, quoting=csv.QUOTE_NONNUMERIC)
            row = [ing] + scores
            writer.writerow(row)

    except Exception as e:
        logging.error(f"Error for {ing}: {e}")
        continue
