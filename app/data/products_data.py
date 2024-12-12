from schemas.routine import Step, STEP_SEQUENCE

PRODUCTS_DATA = {
    Step.CLEANSING: {
        "cleansing_oil": {
            "name": "클렌징오일",
            "usage_time": ["evening"],
            "frequency": 1,
            "instructions": (
                "1. 깨끗하게 씻은 손에 물기를 제거해 주세요!\n"
                "2. 클렌징 오일을 한펌프 손에 짜서 마른 얼굴에 손가락으로 부드럽게 1분정도 마사지해줍니다\n"
                "3. 손에 물을 조금 묻혀서 1분정도 살살 마사지 해주세요!\n"
                "4. 미온수로 얼굴을 헹궈주세요!"
            ),
            "sequence": STEP_SEQUENCE[Step.CLEANSING],
            "time": 2,
        },
        "cleansing_foam": {
            "name": "클렌징폼",
            "usage_time": ["morning", "evening"],
            "frequency": 1,
            "instructions": (
                "1. 깨끗하게 씻은 손으로, 얼굴에 물을 묻혀주세요\n"
                "2. 엄지손톱 크기만큼 폼클렌징을 짜서 거품을 풍성하게 내주세요!\n"
                "3. 거품을 손가락으로 1분정도 살살 문질러 줍니다!\n"
                "4. 미온수로 얼굴을 헹궈주세요!"
            ),
            "sequence": STEP_SEQUENCE[Step.CLEANSING],
            "time": 2,
        },
        "cleansing_water": {
            "name": "클렌징워터",
            "usage_time": ["evening"],
            "frequency": 1,
            "instructions": (
                "1. 화장솜에 클렌징 워터를 충분히 적셔줍니다.\n"
                "2. 얼굴 전체를 화장솜으로 부드럽게 닦아냅니다.\n"
                "3. 메이크업 진한 부위는 잠시 올려둔 뒤 닦아내세요.\n"
                "4. 미온수로 가볍게 헹궈줍니다."
            ),
            "sequence": STEP_SEQUENCE[Step.CLEANSING],
            "time": 2,
        },
        "cleansing_milk": {
            "name": "클렌징밀크",
            "usage_time": ["evening"],
            "frequency": 1,
            "instructions": (
                "1. 손에 1~2 펌프의 클렌징 밀크를 덜어냅니다.\n"
                "2. 마른 얼굴에 부드럽게 마사지하듯 펴 발라줍니다.\n"
                "3. 메이크업이 녹을 때까지 마사지 후, 화장솜 또는 미온수로 헹궈내세요."
            ),
            "sequence": STEP_SEQUENCE[Step.CLEANSING],
            "time": 2,
        },
        "cleansing_gel": {
            "name": "클렌징젤",
            "usage_time": ["evening"],
            "frequency": 1,
            "instructions": (
                "1. 깨끗하게 씻은 손에 500원 크기 정도의 클렌징젤을 덜어냅니다.\n"
                "2. 마른 얼굴에 부드럽게 손가락으로 마사지하며 메이크업을 녹여줍니다.\n"
                "3. 손에 물을 묻혀 젤이 밀키한 색으로 변할 때까지 마사지합니다.\n"
                "4. 미온수로 깨끗이 헹궈냅니다."
            ),
            "sequence": STEP_SEQUENCE[Step.CLEANSING],
            "time": 2,
        },
        "cleansing_balm": {
            "name": "클렌징밤",
            "usage_time": ["evening"],
            "frequency": 1,
            "instructions": (
                "1. 깨끗하게 씻은 손에 500원 크기 정도의 클렌징밤을 덜어내 주세요.\n"
                "2. 마른 얼굴에 부드럽게 펴 바르고 마사지하여 메이크업을 녹입니다.\n"
                "3. 물을 조금 묻혀 유화 후 깨끗이 헹궈냅니다."
            ),
            "sequence": STEP_SEQUENCE[Step.CLEANSING],
            "time": 2,
        },
    },
    Step.CLEANSING_CARE: {
        "scrub": {
            "name": "스크럽",
            "usage_time": ["evening"],
            "frequency": 1,
            "instructions": (
                "1. 세안 후 물기 제거 없이 500원 크기 정도 스크럽을 손에 덜어냅니다.\n"
                "2. 눈가 제외 얼굴 전체를 1~2분 부드럽게 문질러 각질 제거.\n"
                "3. 각질 많은 부위 집중 마사지.\n"
                "4. 미온수로 깨끗이 씻어냅니다."
            ),
            "sequence": STEP_SEQUENCE[Step.CLEANSING_CARE],
            "time": 2,
        },
        "peeling": {
            "name": "필링",
            "usage_time": ["evening"],
            "frequency": 1,
            "instructions": (
                "1. 세안 후 물기를 제거한 상태에서 1~2 펌프 필링제를 손에 덜어냅니다.\n"
                "2. 얼굴 전체에 바르고 1~2분 후 부드럽게 문질러 각질 제거.\n"
                "3. 미온수로 깨끗이 씻어냅니다.\n*주 1~2회 사용 권장*"
            ),
            "sequence": STEP_SEQUENCE[Step.CLEANSING_CARE],
            "time": 2,
        },
    },
    Step.TONER: {
        "skin": {
            "name": "스킨",
            "usage_time": ["morning", "evening"],
            "frequency": 1,
            "instructions": (
                "1. 화장솜에 스킨을 충분히 적시거나, 적당량을 손에 덜어냅니다.\n"
                "2. 얼굴 중앙에서 바깥쪽 방향으로 부드럽게 닦아냅니다.\n"
                "3. 손바닥으로 가볍게 눌러 흡수시켜주세요."
            ),
            "sequence": STEP_SEQUENCE[Step.TONER],
            "time": 1,
        },
        "toner": {
            "name": "토너",
            "usage_time": ["morning", "evening"],
            "frequency": 1,
            "instructions": (
                "1. 화장솜에 토너를 충분히 적시거나, 적당량을 손에 덜어냅니다.\n"
                "2. 얼굴 중앙에서 바깥쪽으로 부드럽게 닦아냅니다.\n"
                "3. 가볍게 두드려 흡수시켜줍니다."
            ),
            "sequence": STEP_SEQUENCE[Step.TONER],
            "time": 1,
        },
    },
    Step.CONCENTRATION_CARE: {
        "essence": {
            "name": "에센스",
            "usage_time": ["morning", "evening"],
            "frequency": 1,
            "instructions": (
                "1. 한 번 펌핑한 에센스를 손바닥에 덜어 얼굴에 부드럽게 발라주세요.\n"
                "2. 손바닥으로 가볍게 눌러 흡수시켜줍니다."
            ),
            "sequence": STEP_SEQUENCE[Step.CONCENTRATION_CARE],
            "time": 1,
        },
        "serum": {
            "name": "세럼",
            "usage_time": ["morning", "evening"],
            "frequency": 1,
            "instructions": (
                "1. 스포이드로 한 펌프 덜어 손에 놓습니다.\n"
                "2. 얼굴 전체에 부드럽게 펴 바르고 톡톡 두드려 흡수시킵니다."
            ),
            "sequence": STEP_SEQUENCE[Step.CONCENTRATION_CARE],
            "time": 1,
        },
        "ampoule": {
            "name": "앰플",
            "usage_time": ["morning", "evening"],
            "frequency": 1,
            "instructions": (
                "1. 스포이드로 한 펌프 덜어냅니다.\n"
                "2. 얼굴 전체에 부드럽게 펴 바르고 톡톡 두드려 흡수시킵니다."
            ),
            "sequence": STEP_SEQUENCE[Step.CONCENTRATION_CARE],
            "time": 1,
        },
    },
    Step.MOISTURIZING: {
        "cream": {
            "name": "크림",
            "usage_time": ["morning", "evening"],
            "frequency": 1,
            "instructions": (
                "1. 500원 크기 만큼 크림을 손등에 덜어냅니다.\n"
                "2. 이마, 양 볼, 코, 턱에 점을 찍듯 바릅니다.\n"
                "3. 부드럽게 펴 바른 후 손바닥으로 가볍게 눌러 흡수시킵니다."
            ),
            "sequence": STEP_SEQUENCE[Step.MOISTURIZING],
            "time": 1,
        },
        "lotion": {
            "name": "로션",
            "usage_time": ["morning", "evening"],
            "frequency": 1,
            "instructions": (
                "1. 50원 동전 크기 정도 로션을 손등에 덜어냅니다.\n"
                "2. 이마, 양 볼, 코, 턱에 점을 찍듯 나눠 바릅니다.\n"
                "3. 손끝으로 마사지하듯 흡수시켜주세요."
            ),
            "sequence": STEP_SEQUENCE[Step.MOISTURIZING],
            "time": 1,
        },
    },
    Step.SUN_CARE: {
        "suncream": {
            "name": "선크림",
            "usage_time": ["morning"],
            "frequency": 1,
            "instructions": (
                "1. 외출 30분 전에 사용합니다.\n"
                "2. 손가락 한 마디 정도 짜서 이마, 볼, 코, 턱에 점 찍듯 바릅니다.\n"
                "3. 고르게 펴 발라줍니다."
            ),
            "sequence": STEP_SEQUENCE[Step.SUN_CARE],
            "time": 1,
        },
        "sunstick": {
            "name": "선스틱",
            "usage_time": ["morning"],
            "frequency": 1,
            "instructions": "1. 얼굴이나 목에 스틱을 2~3회 문질러 균일하게 바릅니다.",
            "sequence": STEP_SEQUENCE[Step.SUN_CARE],
            "time": 1,
        },
    },
    Step.SLEEPING_PACK: {
        "sleeping_pack": {
            "name": "슬리핑팩",
            "usage_time": ["evening"],
            "frequency": 1,
            "instructions": (
                "1. 저녁 스킨케어 마지막 단계에서 슬리핑팩을 적당량 덜어냅니다.\n"
                "2. 얼굴 전체에 부드럽게 펴 발라줍니다.\n"
                "3. 다음날 아침 미온수로 가볍게 씻어내세요."
            ),
            "sequence": STEP_SEQUENCE[Step.SLEEPING_PACK],
            "time": 1,
        }
    },
    Step.MASK_PACK: {
        "mask_pack": {
            "name": "마스크팩",
            "usage_time": ["evening"],
            "frequency": 3,
            "instructions": (
                "1. 세안 후 토너로 피부결 정돈 후 마스크팩을 붙입니다.\n"
                "2. 10~20분 후 마스크를 제거합니다.\n"
                "3. 남은 에센스를 톡톡 두드려 흡수시켜주세요."
            ),
            "sequence": STEP_SEQUENCE[Step.MASK_PACK],
            "time": 15,
        },
    },
}
