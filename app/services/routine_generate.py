import math
import random
from typing import Dict, List

from data.products_data import PRODUCTS_DATA
from db.database import get_db
from schemas.routine import RoutineCreate, Step, SubProductType
from pymongo.errors import PyMongoError

db = get_db()
PRICE_SEGMENTS: Dict[str, Dict[str, float]] = {}


async def init_price_segments():
    """서버 시작 시 1회 호출되어 가격 구간(low, mid, high)을 MongoDB로부터 계산"""
    collection = db["oliveyoung_products_integrated"]

    pipeline = [
        {"$unwind": "$cosmetic_type"},
        {
            "$group": {
                "_id": "$cosmetic_type",
                "low_price": {
                    "$percentile": {
                        "input": "$selling_price",
                        "p": [0.1],
                        "method": "approximate",
                    }
                },
                "mid_price": {
                    "$percentile": {
                        "input": "$selling_price",
                        "p": [0.50],
                        "method": "approximate",
                    }
                },
                "high_price": {
                    "$percentile": {
                        "input": "$selling_price",
                        "p": [0.9],
                        "method": "approximate",
                    }
                },
            }
        },
        {"$sort": {"_id": 1}},  # 카테고리 기준 정렬
    ]

    result_dict = {}
    try:
        async for doc in collection.aggregate(pipeline):
            ctype = doc["_id"]
            low_price = round(doc["low_price"][0], 2)  # Percentile 결과는 배열
            mid_price = round(doc["mid_price"][0], 2)
            high_price = round(doc["high_price"][0], 2)
            result_dict[ctype] = {
                "low": low_price,
                "mid": mid_price,
                "high": high_price,
            }
    except PyMongoError as e:
        # 에러 처리 로직 필요 시 추가
        print(f"MongoDB Error while calculating price segments: {e}")

    global PRICE_SEGMENTS
    PRICE_SEGMENTS = result_dict


# 우선순위 정의
PRIORITY_STEPS = [
    (Step.CLEANSING, "cleansing_foam"),  # 1. 클렌징 폼
    (Step.SUN_CARE, None),  # 2. 선케어
    (Step.MOISTURIZING, None),  # 3. 보습
    (Step.TONER, None),  # 4. 결정리
    (Step.MASK_PACK, None),  # 5. 마스크팩
    (Step.CONCENTRATION_CARE, None),  # 6. 집중케어
    (Step.CLEANSING, None),  # 7. 클렌징(폼 제외)
    (Step.CLEANSING_CARE, None),  # 8. 클렌징 중 추가 케어
    (Step.SLEEPING_PACK, None),  # 9. 슬리핑팩
]


def select_random_product(step_products, excluded_keys, owned_cosmetics):
    """주어진 단계의 제품 중에서 제외할 제품을 빼고 랜덤으로 선택"""
    eligible_products = {
        key: data for key, data in step_products.items() if key not in excluded_keys
    }
    if not eligible_products:
        return None, 0.0

    ck = random.choice(list(eligible_products.keys()))
    product_data = eligible_products[ck]
    owned = ck in owned_cosmetics
    price = (
        0.0
        if owned
        else random.uniform(
            PRICE_SEGMENTS.get(product_data["name"], {"low": 5000, "high": 15000})[
                "low"
            ],
            PRICE_SEGMENTS.get(product_data["name"], {"low": 5000, "high": 15000})[
                "high"
            ],
        )
    )
    return ck, price


def evaluate_solution(
    solution, steps, time_minutes, money_won, priority_weights, penalty_weight=500
):
    """솔루션 평가: 우선순위를 강하게 반영한 점수 계산"""
    used_time = 0
    used_money = 0
    num_steps_selected = 0
    priority_penalty = 0
    deviations = []

    mean_price = 0

    for step_tuple, solution_item in zip(steps, solution):
        step, _ = step_tuple
        ck, chosen_price = solution_item
        if ck is None:
            # 우선순위가 높은 단계가 포함되지 않으면 큰 패널티
            priority_penalty += priority_weights[step] * penalty_weight
            continue
        product_data = PRODUCTS_DATA[step][ck]
        used_time += product_data["time"]
        used_money += max(0, chosen_price)
        num_steps_selected += 1

        # 금액 불균형 척도를 위한 벗어남 비율 계산
        category = product_data["name"]
        if category in PRICE_SEGMENTS:
            mid_price = PRICE_SEGMENTS[category]["mid"]
            deviation = abs((chosen_price - mid_price) / mid_price)
            deviations.append(deviation)
            mean_price += chosen_price

    # 마스크팩 강제 포함 시 페널티 제거
    if Step.MASK_PACK in [s[0] for s in steps] and time_minutes >= 15:
        priority_penalty = max(
            priority_penalty - priority_weights[Step.MASK_PACK] * penalty_weight, 0
        )

    if used_time > time_minutes or used_money > money_won:
        return math.inf  # 불가능한 해는 무한대 점수 반환

    time_left = time_minutes - used_time
    money_left = money_won - used_money
    # 금액 불균형 계산 (표준 편차)
    if deviations:
        mean_deviation = sum(deviations) / len(deviations)
        std_dev = math.sqrt(
            sum((dev - mean_deviation) ** 2 for dev in deviations) / len(deviations)
        )
        imbalance_score = std_dev  # 표준 편차로 불균형 측정
    else:
        imbalance_score = 0

    return (
        time_left**2
        + money_left**2
        - imbalance_score * penalty_weight  # 불균형 반영
        + priority_penalty
    )


def generate_minimal_solution(steps, owned_cosmetics, time_minutes):
    """최소한의 필수 단계만 포함하는 초기 솔루션 생성"""
    solution = []
    used_time = 0  # 누적 사용 시간

    for step, forced_key in steps:
        step_products = PRODUCTS_DATA.get(step, {})
        if not step_products:
            solution.append((None, 0.0))
            continue

        chosen_key = None
        chosen_price = 0.0

        # 소유한 제품 우선 포함
        for product_key, product_data in step_products.items():
            if product_data["name"] in owned_cosmetics:
                if used_time + product_data["time"] <= time_minutes:
                    # 1단계에는 클렌징 폼만, 7단계에는 클렌징 폼 금지
                    if (
                        step == Step.CLEANSING
                        and forced_key == "cleansing_foam"
                        and product_key != "cleansing_foam"
                    ):
                        continue
                    if (
                        step == Step.CLEANSING
                        and forced_key is None
                        and product_key == "cleansing_foam"
                    ):
                        continue

                    chosen_key = product_key
                    chosen_price = -100.0  # 소유 제품은 가격 -100
                    used_time += product_data["time"]
                    break

        if chosen_key:
            # 소유한 제품이 포함된 경우
            solution.append((chosen_key, chosen_price))
        else:
            # 소유 제품이 없으면 강제 포함 제품(예: 클렌징폼, 선크림 등) 처리
            if step == Step.CLEANSING and forced_key == "cleansing_foam":
                product_data = step_products[forced_key]
                price = PRICE_SEGMENTS.get(
                    product_data["name"], {"low": 5000, "high": 15000}
                )["low"]
                if used_time + product_data["time"] <= time_minutes:
                    solution.append((forced_key, price))
                    used_time += product_data["time"]
                else:
                    solution.append((None, 0.0))
            elif step == Step.SUN_CARE:
                forced_key = list(step_products.keys())[0]  # 첫 번째 제품 선택
                product_data = step_products[forced_key]
                price = PRICE_SEGMENTS.get(
                    product_data["name"], {"low": 5000, "high": 15000}
                )["low"]
                if used_time + product_data["time"] <= time_minutes:
                    solution.append((forced_key, price))
                    used_time += product_data["time"]
                else:
                    solution.append((None, 0.0))
            elif step == Step.MASK_PACK and time_minutes >= 15:
                # 마스크팩 강제 포함
                forced_key = list(step_products.keys())[0]
                product_data = step_products[forced_key]
                price = PRICE_SEGMENTS.get(
                    product_data["name"], {"low": 1000, "high": 2000}
                )["low"]
                if used_time + 8 <= time_minutes:  # 시간 8분으로 조정
                    product_data["time"] = 8
                    solution.append((forced_key, price))
                    used_time += 8
                else:
                    solution.append((None, 0.0))
            else:
                solution.append((None, 0.0))  # 선택 불가능하면 제외

    print(f"Generated minimal solution: {solution}")  # 디버깅 출력
    return solution


def routine_optimization_step(solution, steps, time_minutes, money_won):
    """루틴 최적화 단계: 시간을 초과하지 않는 범위에서 가능한 많은 루틴 추가 (low cost 고려)"""
    optimized_solution = solution[:]
    used_time = sum(
        PRODUCTS_DATA[step][ck]["time"]
        for (step, _), (ck, _) in zip(steps, solution)
        if ck is not None
    )
    used_money = sum(price for _, price in solution if price > 0)  # 초기 비용 계산

    for i, (step, _) in enumerate(steps):
        if optimized_solution[i][0] is not None:
            continue  # 이미 포함된 경우 건너뜀

        step_products = PRODUCTS_DATA.get(step, {})
        if not step_products:
            continue

        # low cost 제품 기준 추가
        for product_key, product_data in step_products.items():
            price = PRICE_SEGMENTS.get(product_data["name"], {"low": 5000})["low"]
            if (
                used_time + product_data["time"] <= time_minutes
                and used_money + price <= money_won
            ):
                optimized_solution[i] = (product_key, price)
                used_time += product_data["time"]
                used_money += price
                break

    print(f"Routine Optimized Solution: {optimized_solution}")  # 디버깅 출력
    return optimized_solution


def cost_optimization_step(
    solution, steps, time_minutes, money_won, priority_weights, max_iterations=5000
):
    """비용 최적화 단계: 선택된 제품의 비용을 조정하며 최적화를 진행"""
    current_solution = solution[:]
    current_score = evaluate_solution(
        current_solution, steps, time_minutes, money_won, priority_weights
    )
    best_solution = current_solution
    best_score = current_score

    T = 10000.0
    cooling_rate = 0.99

    for iteration in range(max_iterations):
        new_sol = neighbor_solution_with_addition(
            current_solution, steps, [], priority_weights
        )
        new_score = evaluate_solution(
            new_sol, steps, time_minutes, money_won, priority_weights
        )

        if new_score < current_score:
            current_solution = new_sol
            current_score = new_score
            if new_score < best_score:
                best_solution = new_sol
                best_score = new_score
        else:
            diff = new_score - current_score
            if random.random() < math.exp(-diff / T):
                current_solution = new_sol
                current_score = new_score

        T *= cooling_rate
        if iteration % 100 == 0:
            print(f"{iteration}: Solution:{current_solution} Score: {best_score}")

    print(f"Cost Optimized Solution: {best_solution}, Score: {best_score}")
    return best_solution


def neighbor_solution_with_addition(solution, steps, owned_cosmetics, priority_weights):
    """이웃 생성: 기존 솔루션에서 제품 추가 또는 변경"""
    new_sol = solution[:]
    idx = random.choices(
        range(len(solution)),
        weights=[1 / (priority_weights[step] + 1) for step, _ in steps],
        k=1,
    )[0]

    ck, chosen_price = new_sol[idx]
    step, forced_key = steps[idx]
    step_products = PRODUCTS_DATA.get(step, {})

    # 소유 제품은 변경하지 않음
    if chosen_price == -100.0:
        return new_sol

    # 필수 단계도 가격만 랜덤 변경 허용
    if step in {Step.CLEANSING, Step.SUN_CARE} and ck is not None:
        product_data = step_products.get(ck, {})
        if product_data:
            low_price = PRICE_SEGMENTS.get(product_data["name"], {"low": 5000})["low"]
            high_price = PRICE_SEGMENTS.get(product_data["name"], {"high": 15000})[
                "high"
            ]
            new_price = random.uniform(low_price, high_price)
            new_sol[idx] = (ck, new_price)
        return new_sol

    if not step_products:
        return new_sol

    if random.random() < 0.5:
        new_sol[idx] = (None, 0.0)
        return new_sol

    # 7단계 클렌징(폼 제외)이 선택된 경우
    if step == Step.CLEANSING and forced_key is None:
        excluded_keys = ["cleansing_foam"]
        ck, price = select_random_product(step_products, excluded_keys, owned_cosmetics)
        new_sol[idx] = (ck, price)
    else:
        # 다른 단계의 경우 랜덤으로 교체
        ck, price = select_random_product(step_products, [], owned_cosmetics)
        new_sol[idx] = (ck, price)
    return new_sol


async def get_routine(
    time_minutes: int, money_won: int, owned_cosmetics: List[str]
) -> RoutineCreate:
    steps = PRIORITY_STEPS

    # 1. 최소 솔루션 생성
    minimal_solution = generate_minimal_solution(steps, owned_cosmetics, time_minutes)

    # 2. 루틴 최적화 단계
    routine_solution = routine_optimization_step(
        minimal_solution, steps, time_minutes, money_won
    )

    # 3. 비용 최적화 단계
    priority_weights = {step: i + 1 for i, (step, _) in enumerate(steps)}
    final_solution = cost_optimization_step(
        routine_solution, steps, time_minutes, money_won, priority_weights
    )

    # 최종 루틴 구성
    selected_products = []
    for step_tuple, (ck, chosen_price) in zip(steps, final_solution):
        step, _ = step_tuple
        if ck is None:
            continue
        product_data = PRODUCTS_DATA[step][ck]
        sub_product = SubProductType(
            name=product_data["name"],
            usage_time=product_data["usage_time"],
            frequency=product_data["frequency"],
            instructions=product_data["instructions"],
            sequence=product_data["sequence"],
            time=product_data["time"],
            cost=int(chosen_price),
        )
        selected_products.append(sub_product)

    return split_routine_by_time(selected_products)


def split_routine_by_time(products: List[SubProductType]) -> RoutineCreate:
    morning_products = []
    evening_products = []

    # 아침, 저녁 나누기
    for p in products:
        if "morning" in p.usage_time:
            morning_products.append(p)
        if "evening" in p.usage_time:
            evening_products.append(p)

    # sequence로 정렬
    morning_products.sort(key=lambda x: x.sequence)
    evening_products.sort(key=lambda x: x.sequence)

    # 코스트가 음수인 경우 0으로 바꾸어서 리턴
    morning_products = [
        p if p.cost >= 0 else p.copy(update={"cost": 0}) for p in morning_products
    ]
    evening_products = [
        p if p.cost >= 0 else p.copy(update={"cost": 0}) for p in evening_products
    ]

    # 저녁 루틴에 마스크팩이 있는 경우, 시간을 15로 재설정
    for p in evening_products:
        if p.name == "마스크팩":
            p.time = 15

    return RoutineCreate(
        morning_routine=morning_products, evening_routine=evening_products
    )
