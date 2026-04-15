import json
from fastapi import HTTPException
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from db.database import db
from schemas.cosmetics import ProductRecommendation
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


async def get_gpt_response(
    name,
    brand,
    skin_type_score,
    concern_score,
    rank_score,
    price_score,
    matching_ingredients,
    user_skin_type,
    user_concerns,
) -> str:
    prompt = f"""
    당신은 전문적인 스킨케어 컨설턴트이며, 비둘기 캐릭터입니다. 아래의 정보를 바탕으로 사용자가 이해하기 쉽도록 제품을 추천하는 이유를 간결하게 작성해 주세요:

    사용자 피부 타입: {user_skin_type}
    사용자 피부 고민: {', '.join(user_concerns)}
    제품명: {name}
    브랜드: {brand}
    피부 타입 점수: {skin_type_score}
    피부 고민 점수: {concern_score}
    순위 점수: {rank_score}
    가격 점수: {price_score}
    매칭된 성분: {matching_ingredients}

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

    return reason


from services.cosmetic_services import es

CATEGORY_MAPPING = {
    "클렌징": ["클렌징"],
    "클렌징 단계 추가 케어": ["클렌징"],
    "클렌징폼": ["클렌징"],
    "클렌징오일": ["클렌징"],
    "스크럽": ["클렌징", "클렌징 단계 추가 케어"],
    "결정리": ["스킨/토너"],
    "토너": ["스킨/토너"],
    "스킨": ["스킨/토너"],
    "집중 케어": ["에센스/세럼/앰플"],
    "세럼": ["에센스/세럼/앰플"],
    "앰플": ["에센스/세럼/앰플"],
    "에센스": ["에센스/세럼/앰플"],
    "보습": ["크림", "로션"],
    "로션": ["로션", "크림"],
    "크림": ["크림", "로션"],
    "선케어": ["선케어"],
    "선크림": ["선케어"],
    "수면 중 보습 케어": ["수면 중 보습 케어", "크림"],
    "슬리핑팩": ["수면 중 보습 케어", "크림"],
    "시간 투자형 집중케어": ["시간 투자형 집중케어", "마스크팩"],
    "마스크팩": ["시간 투자형 집중케어", "마스크팩"],
}

async def recommend_cosmetics(
    user_skin_type: str,
    user_concerns: List[str],
    cosmetic_types: str,
    allergic_ingredients: List[str],
    budget: int,
) -> List[ProductRecommendation]:
    # 1. Elasticsearch를 이용한 후보군 필터링
    must_queries = []
    
    # 카테고리 매핑 적용
    mapped_categories = CATEGORY_MAPPING.get(cosmetic_types, [cosmetic_types])
    
    # 카테고리 필터 또는 이름 검색
    category_query = {
        "bool": {
            "should": [
                {"terms": {"category": mapped_categories}},
                {"match": {"name": cosmetic_types}}
            ],
            "minimum_should_match": 1
        }
    }
    must_queries.append(category_query)
    
    # 가격 필터
    must_queries.append({"range": {"price": {"lte": budget}}})
    
    # 알레르기 성분 제외
    must_not_queries = []
    if allergic_ingredients:
        must_not_queries.append({"match": {"ingredients": " ".join(allergic_ingredients)}})

    search_query = {
        "query": {
            "bool": {
                "must": must_queries,
                "must_not": must_not_queries
            }
        },
        "sort": [
            {"rank": {"order": "asc"}},
            {"_score": {"order": "desc"}}
        ],
        "size": 15 # OpenAI가 분석할 적절한 후보 수
    }

    try:
        response = await es.search(index="products", body=search_query)
        hits = response["hits"]["hits"]
    except Exception as e:
        print(f"ES Search Error: {e}")
        hits = []

    # 검색 결과가 없으면 예산 제한을 풀고 다시 검색
    if not hits:
        print(f"No products found for {cosmetic_types} with budget {budget}. Relaxing budget constraint.")
        search_query["query"]["bool"]["must"] = [category_query] # 가격 필터 제거
        try:
            response = await es.search(index="products", body=search_query)
            hits = response["hits"]["hits"]
        except Exception as e:
            print(f"ES Retry Search Error: {e}")

    if not hits:
        raise HTTPException(status_code=404, detail="조건에 맞는 제품이 없습니다.")

    # 2. 후보군 정보 가공
    candidates = []
    for hit in hits:
        s = hit["_source"]
        candidates.append({
            "id": hit["_id"],
            "name": s.get("name"),
            "brand": s.get("brand"),
            "price": s.get("price"),
            "ingredients": s.get("ingredients", ""),
            "effects": s.get("effects", ""),
            "skin_type": s.get("skin_type", "전체"),
            "rank": s.get("rank")
        })

    # 3. OpenAI를 이용한 최종 추천 및 이유 생성
    prompt = f"""
    당신은 전문적인 스킨케어 컨설턴트이며, 비둘기 캐릭터입니다. 
    사용자의 피부 정보와 제공된 제품 후보 목록을 바탕으로 가장 적합한 제품 3개를 선정하고 추천 이유를 작성해 주세요.

    [사용자 정보]
    - 피부 타입: {user_skin_type}
    - 피부 고민: {', '.join(user_concerns)}
    - 알레르기 성분: {', '.join(allergic_ingredients)}

    [제품 후보 목록]
    {json.dumps(candidates, ensure_ascii=False, indent=2)}

    [요구 사항]
    1. 후보 목록 중에서 사용자의 피부 타입과 고민에 가장 잘 맞는 제품 3개를 선정하세요. (제품의 skin_type과 effects 정보를 사용자의 고민과 대조하세요)
    2. 각 제품에 대해 피부 타입 점수, 고민 점수, 순위 점수, 가격 점수를 0.0~1.0 사이로 평가하세요.
    3. 추천 이유는 제품의 성분과 효능(effects)을 근거로 하여 전문적이면서도 친근한 말투(-요 체)로 작성하세요. (최대 2줄)
    4. 응답은 반드시 아래 JSON 형식으로만 해주세요.

    [JSON 형식]
    {{
      "recommendations": [
        {{
          "id": "제품ID",
          "skin_type_score": 0.9,
          "concern_score": 0.8,
          "rank_score": 0.9,
          "price_score": 0.7,
          "total_score": 85.5,
          "reason": "추천 이유"
        }},
        ...
      ]
    }}
    """

    try:
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "당신은 스킨케어 전문가 비둘기입니다. 반드시 JSON 형식으로만 응답하세요."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        result = json.loads(completion.choices[0].message.content)
        ai_recs = result.get("recommendations", [])
        
        # 4. 결과 매핑 및 반환
        final_recommendations = []
        hit_dict = {hit["_id"]: hit["_source"] for hit in hits}
        
        for ai_rec in ai_recs:
            p_id = ai_rec["id"]
            if p_id in hit_dict:
                s = hit_dict[p_id]
                rec = ProductRecommendation(
                    _id=p_id,
                    name=str(s.get("name")),
                    brand=str(s.get("brand")),
                    selling_price=int(s.get("price", 0)),
                    link=str(s.get("link", "")),
                    skin_type_score=float(ai_rec.get("skin_type_score", 0.5)),
                    concern_score=float(ai_rec.get("concern_score", 0.5)),
                    rank_score=float(ai_rec.get("rank_score", 0.5)),
                    price_score=float(ai_rec.get("price_score", 0.5)),
                    total_score=float(ai_rec.get("total_score", 50.0)),
                    matching_ingredients={}, 
                    reason=str(ai_rec.get("reason", "사용자 피부에 꼭 맞는 성분으로 구성되어 있어요.")),
                    image_url=str(s.get("image_url", ""))
                )
                final_recommendations.append(rec)
        
        if final_recommendations:
            return final_recommendations[:3]

    except Exception as e:
        print(f"OpenAI Recommendation Error: {e} (Falling back to local scoring)")
        
        # 5. 폴백 로직: OpenAI 실패 시 자체 스코어링으로 추천
        fallback_recommendations = []
        # 상위 3개 제품 선정 (ES 랭크 기준)
        for hit in hits[:3]:
            s = hit["_source"]
            # 피부 타입 매칭 확인
            skin_match = 1.0 if user_skin_type.lower() in str(s.get("skin_type", "")).lower() or "전체" in str(s.get("skin_type", "")) else 0.5
            
            rec = ProductRecommendation(
                _id=hit["_id"],
                name=str(s.get("name")),
                brand=str(s.get("brand")),
                selling_price=int(s.get("price", 0)),
                link=str(s.get("link", "")),
                skin_type_score=skin_match,
                concern_score=0.7, # 기본값
                rank_score=1.0 - (s.get("rank", 999) / 2000.0), # 순위 기반 점수화
                price_score=0.8,
                total_score=70.0,
                matching_ingredients={},
                reason="사용자님의 피부 타입과 고민을 고려하여 엄선한 추천 제품이에요. 꾸준히 사용하시면 효과를 보실 수 있어요!",
                image_url=str(s.get("image_url", ""))
            )
            fallback_recommendations.append(rec)
        
        return fallback_recommendations
