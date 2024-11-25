from schemas.routine_generate import (
    PRODUCT_TYPES,
    UserType,
    ROUTINE_BY_USER_TYPE,
    Routine,
)


def get_time_level(time_minutes):
    if time_minutes < 5:
        return "low"
    elif time_minutes <= 20:
        return "medium"
    else:
        return "high"


def get_money_level(money_won):
    if money_won < 30000:
        return "low"
    elif money_won <= 100000:
        return "medium"
    else:
        return "high"


def get_user_type(time_level, money_level) -> UserType:
    if time_level == "low" and money_level == "low":
        return UserType.LTLC
    elif time_level == "low" and money_level == "medium":
        return UserType.LTMC
    elif time_level == "low" and money_level == "high":
        return UserType.LTHC
    elif time_level == "medium" and money_level == "low":
        return UserType.MTLC
    elif time_level == "medium" and money_level == "medium":
        return UserType.MTMC
    elif time_level == "medium" and money_level == "high":
        return UserType.MTHC
    elif time_level == "high" and money_level == "low":
        return UserType.HTLC
    elif time_level == "high" and money_level == "medium":
        return UserType.HTMC
    elif time_level == "high" and money_level == "high":
        return UserType.HTHC
    else:
        raise ValueError("Invalid time_level or money_level")


def get_routine(time_minutes, money_won):
    time_level = get_time_level(time_minutes)
    money_level = get_money_level(money_won)
    user_type = get_user_type(time_level, money_level)
    routine_list = ROUTINE_BY_USER_TYPE[user_type]

    return Routine(routine=[PRODUCT_TYPES[step] for step in routine_list])
