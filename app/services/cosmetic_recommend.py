import json
from fastapi import HTTPException
import pandas as pd
from db.database import db
from schemas.cosmetics import ProductRecommendation
from typing import Dict, List, TypedDict, Optional, Any
from collections import defaultdict
from core.config import settings
from openai import OpenAI

# LangChain & LangGraph imports
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field

OPENAI_KEY = settings.openai_key

client = OpenAI(api_key=OPENAI_KEY)

# --- LangChain & LangGraph Setup ---

# 1. Structured Output Schema for OpenAI
class AIRecommendation(BaseModel):
    id: str = Field(description="제품 ID")
    skin_type_score: float = Field(description="피부 타입 점수 (0.0~1.0)")
    concern_score: float = Field(description="피부 고민 점수 (0.0~1.0)")
    rank_score: float = Field(description="순위 점수 (0.0~1.0)")
    price_score: float = Field(description="가격 점수 (0.0~1.0)")
    total_score: float = Field(description="총점 (0~100)")
    reason: str = Field(description="추천 이유 (최대 2줄, 전문적이고 친근한 말투)")

class AIRecommendationList(BaseModel):
    recommendations: List[AIRecommendation]

# 2. Graph State Definition
class RecommendationState(TypedDict):
    # Input
    user_skin_type: str
    user_concerns: List[str]
    cosmetic_types: str
    allergic_ingredients: List[str]
    budget: int
    
    # Intermediate / Output
    candidates: List[dict]
    hits_dict: Dict[str, Any]
    final_recommendations: List[ProductRecommendation]
    error: Optional[str]

# 3. Nodes Implementation

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

async def retrieve_candidates_node(state: RecommendationState):
    """Elasticsearch를 이용하여 후보군을 검색하는 노드"""
    must_queries = []
    mapped_categories = CATEGORY_MAPPING.get(state["cosmetic_types"], [state["cosmetic_types"]])
    
    category_query = {
        "bool": {
            "should": [
                {"terms": {"category": mapped_categories}},
                {"match": {"name": state["cosmetic_types"]}}
            ],
            "minimum_should_match": 1
        }
    }
    must_queries.append(category_query)
    must_queries.append({"range": {"price": {"lte": state["budget"]}}})
    
    must_not_queries = []
    if state["allergic_ingredients"]:
        must_not_queries.append({"match": {"ingredients": " ".join(state["allergic_ingredients"])}})

    search_query = {
        "query": {
            "bool": {
                "must": must_queries,
                "must_not": must_not_queries
            }
        },
        "sort": [{"rank": {"order": "asc"}}, {"_score": {"order": "desc"}}],
        "size": 15
    }

    try:
        response = await es.search(index="products", body=search_query)
        hits = response["hits"]["hits"]
        
        # 검색 결과가 없으면 예산 제한 완화 재검색
        if not hits:
            search_query["query"]["bool"]["must"] = [category_query]
            response = await es.search(index="products", body=search_query)
            hits = response["hits"]["hits"]
            
    except Exception as e:
        print(f"ES Search Error: {e}")
        hits = []

    if not hits:
        return {"error": "No products found", "candidates": []}

    candidates = []
    hits_dict = {}
    for hit in hits:
        s = hit["_source"]
        hits_dict[hit["_id"]] = s
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
    
    return {"candidates": candidates, "hits_dict": hits_dict}

async def generate_recommendations_node(state: RecommendationState):
    """OpenAI(LangChain)를 사용하여 최종 추천을 생성하는 노드"""
    if not state["candidates"]:
        return {"final_recommendations": []}

    llm = ChatOpenAI(
        # model="gpt-4o",
        model="gpt-5.4-nano", 
        temperature=0, 
        api_key=OPENAI_KEY
    ).with_structured_output(AIRecommendationList)

    prompt = ChatPromptTemplate.from_template("""
    당신은 전문적인 스킨케어 컨설턴트이며, 비둘기 캐릭터입니다. 
    사용자의 피부 정보와 제공된 제품 후보 목록을 바탕으로 가장 적합한 제품 3개를 선정하고 추천 이유를 작성해 주세요.

    [사용자 정보]
    - 피부 타입: {user_skin_type}
    - 피부 고민: {user_concerns}
    - 알레르기 성분: {allergic_ingredients}

    [제품 후보 목록]
    {candidates_json}

    [요구 사항]
    1. 후보 목록 중에서 사용자의 피부 타입과 고민에 가장 잘 맞는 제품 3개를 선정하세요. (제품의 skin_type과 effects 정보를 사용자의 고민과 대조하세요)
    2. 추천 이유는 제품의 성분과 효능(effects)을 근거로 하여 전문적이면서도 친근한 말투(-요 체)로 작성하세요. (최대 2줄)
    """)

    try:
        chain = prompt | llm
        result = await chain.ainvoke({
            "user_skin_type": state["user_skin_type"],
            "user_concerns": ", ".join(state["user_concerns"]),
            "allergic_ingredients": ", ".join(state["allergic_ingredients"]),
            "candidates_json": json.dumps(state["candidates"], ensure_ascii=False, indent=2)
        })
        
        final_recs = []
        for ai_rec in result.recommendations:
            p_id = ai_rec.id
            if p_id in state["hits_dict"]:
                s = state["hits_dict"][p_id]
                final_recs.append(ProductRecommendation(
                    _id=p_id,
                    name=str(s.get("name")),
                    brand=str(s.get("brand")),
                    selling_price=int(s.get("price", 0)),
                    link=str(s.get("link", "")),
                    skin_type_score=ai_rec.skin_type_score,
                    concern_score=ai_rec.concern_score,
                    rank_score=ai_rec.rank_score,
                    price_score=ai_rec.price_score,
                    total_score=ai_rec.total_score,
                    matching_ingredients={},
                    reason=ai_rec.reason,
                    image_url=str(s.get("image_url", ""))
                ))
        return {"final_recommendations": final_recs[:3]}
        
    except Exception as e:
        print(f"OpenAI (LangChain) Error: {e}")
        return {"error": "OpenAI Error"}

async def fallback_node(state: RecommendationState):
    """OpenAI 실패 시 또는 결과가 없을 때 실행되는 폴백 노드"""
    if state.get("final_recommendations"):
        return state

    fallback_recs = []
    candidates = state.get("candidates", [])[:3]
    
    for c in candidates:
        p_id = c["id"]
        s = state["hits_dict"].get(p_id, {})
        skin_match = 1.0 if state["user_skin_type"].lower() in str(s.get("skin_type", "")).lower() or "전체" in str(s.get("skin_type", "")) else 0.5
        
        fallback_recs.append(ProductRecommendation(
            _id=p_id,
            name=str(s.get("name")),
            brand=str(s.get("brand")),
            selling_price=int(s.get("price", 0)),
            link=str(s.get("link", "")),
            skin_type_score=skin_match,
            concern_score=0.7,
            rank_score=1.0 - (s.get("rank", 999) / 2000.0),
            price_score=0.8,
            total_score=70.0,
            matching_ingredients={},
            reason="사용자님의 피부 타입과 고민을 고려하여 엄선한 추천 제품이에요. 꾸준히 사용하시면 효과를 보실 수 있어요!",
            image_url=str(s.get("image_url", ""))
        ))
    
    return {"final_recommendations": fallback_recs}

def route_after_recommendation(state: RecommendationState):
    """추천 노드 이후 어디로 갈지 결정"""
    if state.get("error") == "OpenAI Error" or not state.get("final_recommendations"):
        return "fallback"
    return END

# 4. Graph Construction
workflow = StateGraph(RecommendationState)

workflow.add_node("retrieve", retrieve_candidates_node)
workflow.add_node("recommend", generate_recommendations_node)
workflow.add_node("fallback", fallback_node)

workflow.set_entry_point("retrieve")
workflow.add_edge("retrieve", "recommend")
workflow.add_conditional_edges(
    "recommend",
    route_after_recommendation,
    {
        "fallback": "fallback",
        END: END
    }
)
workflow.add_edge("fallback", END)

recommendation_app = workflow.compile()

# --- Legacy Compatibility & Entry Point ---

async def recommend_cosmetics(
    user_skin_type: str,
    user_concerns: List[str],
    cosmetic_types: str,
    allergic_ingredients: List[str],
    budget: int,
) -> List[ProductRecommendation]:
    """LangGraph 워크플로우를 실행하여 화장품을 추천합니다."""
    
    initial_state = {
        "user_skin_type": user_skin_type,
        "user_concerns": user_concerns,
        "cosmetic_types": cosmetic_types,
        "allergic_ingredients": allergic_ingredients,
        "budget": budget,
        "candidates": [],
        "hits_dict": {},
        "final_recommendations": [],
        "error": None
    }
    
    try:
        final_state = await recommendation_app.ainvoke(initial_state)
        
        if not final_state.get("final_recommendations"):
            raise HTTPException(status_code=404, detail="조건에 맞는 제품이 없습니다.")
            
        return final_state["final_recommendations"]
        
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Recommendation Workflow Error: {e}")
        raise HTTPException(status_code=500, detail="추천 시스템 내부 오류가 발생했습니다.")

# --- Remaining Functions ---

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
        # model="gpt-4o",
        model="gpt-5.4-nano",
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
