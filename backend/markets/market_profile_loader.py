import json

from backend.config.paths import MARKET_PROFILES_FILE


DEFAULT_MARKET_PROFILE_ID = "de_lu_day_ahead"


def load_market_profiles(config_file=MARKET_PROFILES_FILE):
    if not config_file.exists():
        return []

    with open(config_file, "r", encoding="utf-8") as file:
        data = json.load(file)

    return data.get("markets", [])


def get_market_profile(market_profile_id=DEFAULT_MARKET_PROFILE_ID):
    profiles = load_market_profiles()

    for profile in profiles:
        if profile.get("market_profile_id") == market_profile_id:
            return profile

    raise ValueError(f"Market profile not found: {market_profile_id}")


def get_default_market_profile():
    return get_market_profile(DEFAULT_MARKET_PROFILE_ID)


def get_market_time_unit_minutes(market_profile_id=DEFAULT_MARKET_PROFILE_ID):
    profile = get_market_profile(market_profile_id)
    return int(profile.get("market_time_unit_minutes", 60))


def get_expected_intervals_per_day(market_profile_id=DEFAULT_MARKET_PROFILE_ID):
    profile = get_market_profile(market_profile_id)
    return int(profile.get("expected_intervals_per_day", 24))



