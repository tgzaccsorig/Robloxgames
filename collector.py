import json
import os
import time
import uuid
from typing import Any, Dict, List, Optional, Set, Tuple

import requests

OUTPUT_FILE = "games.json"
TARGET_GAMES = 10000

# РњРµРЅСЊС€Рµ Р·Р°РїСЂРѕСЃРѕРІ Р·Р° РѕРґРёРЅ Р·Р°РїСѓСЃРє = РјРµРЅСЊС€Рµ Rate Limit.
# Workflow Р·Р°РїСѓСЃРєР°РµС‚СЃСЏ РєР°Р¶РґС‹Рµ 6 С‡Р°СЃРѕРІ, РїРѕСЌС‚РѕРјСѓ РєР°С‚Р°Р»РѕРі РїРѕСЃС‚РµРїРµРЅРЅРѕ СЂР°СЃС‚С‘С‚.
PAGES_PER_SEARCH = 2
MAX_SEARCH_TERMS = 18

MAX_RECOMMENDATION_SEEDS = 30
MAX_RECOMMENDATION_REQUESTS = 30

REQUEST_DELAY = 0.35
MAX_RETRIES = 5
TIMEOUT = 25

SEARCH_URL = "https://apis.roblox.com/search-api/omni-search"
DETAILS_URL = "https://games.roblox.com/v1/games"
RECOMMENDATIONS_URL = (
    "https://games.roblox.com/v1/games/recommendations/game/{universe_id}"
)

HEADERS = {
    "User-Agent": "RobloxHiddenGems/3.0",
    "Accept": "application/json",
}

SEARCH_TERMS = [
    "obby", "simulator", "roleplay", "horror", "survival", "adventure",
    "pvp", "rpg", "racing", "tycoon", "anime", "story", "parkour",
    "murder", "zombie", "fighting", "hidden gem", "new game", "indie",
    "sandbox", "tower", "escape", "fishing", "farming", "driving",
    "city", "school", "backrooms", "magic", "pirate", "space", "pets",
    "minigames", "party", "horror story", "open world",
]

session = requests.Session()
session.headers.update(HEADERS)


def to_int(value: Any) -> Optional[int]:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        value = value.strip()
        if value.isdigit():
            return int(value)
    return None


def get_json(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    retries: int = MAX_RETRIES,
) -> Optional[Any]:
    for attempt in range(1, retries + 1):
        try:
            response = session.get(url, params=params, timeout=TIMEOUT)

            if response.status_code == 200:
                try:
                    return response.json()
                except ValueError:
                    print("Invalid JSON response.")
                    return None

            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                try:
                    wait = max(3, min(60, int(float(retry_after))))
                except (TypeError, ValueError):
                    wait = min(30, 5 * attempt)

                print(
                    f"Rate limit (429). Waiting {wait}s "
                    f"({attempt}/{retries})..."
                )
                time.sleep(wait)
                continue

            if response.status_code in (500, 502, 503, 504):
                wait = min(20, 2 * attempt)
                print(
                    f"Server error {response.status_code}. "
                    f"Waiting {wait}s..."
                )
                time.sleep(wait)
                continue

            print(f"HTTP {response.status_code}: {url}")
            return None

        except requests.RequestException as error:
            wait = min(20, 2 * attempt)
            print(
                f"Request error ({attempt}/{retries}): {error}. "
                f"Waiting {wait}s..."
            )
            time.sleep(wait)

    return None


def extract_universe_id(item: Dict[str, Any]) -> Optional[int]:
    for key in (
        "universeId", "universeID", "universe_id", "gameId", "id"
    ):
        value = to_int(item.get(key))
        if value:
            return value

    for key in ("game", "experience", "universe", "place"):
        nested = item.get(key)
        if isinstance(nested, dict):
            value = extract_universe_id(nested)
            if value:
                return value

    return None


def find_search_items(data: Any) -> List[Dict[str, Any]]:
    found: List[Dict[str, Any]] = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            if extract_universe_id(value):
                found.append(value)
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(data)
    return found


def search_page(
    keyword: str,
    page_token: str = "",
) -> Tuple[List[int], str]:
    params = {
        "searchQuery": keyword,
        "sessionId": str(uuid.uuid4()),
        "pageType": "all",
        "pageToken": page_token,
    }

    data = get_json(SEARCH_URL, params=params)
    if not data or not isinstance(data, dict):
        return [], ""

    ids: List[int] = []
    for item in find_search_items(data):
        universe_id = extract_universe_id(item)
        if universe_id and universe_id not in ids:
            ids.append(universe_id)

    next_token = ""
    for key in (
        "nextPageToken", "nextPageCursor", "nextCursor", "pageToken"
    ):
        value = data.get(key)
        if isinstance(value, str) and value:
            next_token = value
            break

    return ids, next_token


def search_keyword(keyword: str, known_ids: Set[int]) -> Set[int]:
    found: Set[int] = set()
    token = ""

    for page in range(1, PAGES_PER_SEARCH + 1):
        ids, next_token = search_page(keyword, token)

        if not ids:
            break

        new_ids = [
            universe_id
            for universe_id in ids
            if universe_id not in known_ids and universe_id not in found
        ]
        found.update(new_ids)

        print(
            f"  page {page}: {len(ids)} results, "
            f"{len(new_ids)} new"
        )

        if not next_token or next_token == token:
            break

        token = next_token
        time.sleep(REQUEST_DELAY)

    return found


def extract_recommendation_ids(data: Any) -> Set[int]:
    result: Set[int] = set()

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            universe_id = extract_universe_id(value)
            if universe_id:
                result.add(universe_id)
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(data)
    return result


def get_recommendations(universe_id: int) -> Set[int]:
    url = RECOMMENDATIONS_URL.format(universe_id=universe_id)
    data = get_json(url)
    if not data:
        return set()
    return extract_recommendation_ids(data)


def get_details(universe_ids: List[int]) -> List[Dict[str, Any]]:
    result: List[Dict[str, Any]] = []

    for start in range(0, len(universe_ids), 50):
        batch = universe_ids[start:start + 50]
        params = {"universeIds": ",".join(str(x) for x in batch)}
        data = get_json(DETAILS_URL, params=params)

        if isinstance(data, dict):
            games = data.get("data", [])
            if isinstance(games, list):
                result.extend(games)

        time.sleep(REQUEST_DELAY)

    return result


def normalize_game(game: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    universe_id = (
        to_int(game.get("id"))
        or to_int(game.get("universeId"))
    )
    if not universe_id:
        return None

    place_id = (
        to_int(game.get("rootPlaceId"))
        or to_int(game.get("placeId"))
    )

    creator = game.get("creator")
    if not isinstance(creator, dict):
        creator = None

    return {
        "universeId": universe_id,
        "placeId": place_id,
        "name": game.get("name") or "Unknown game",
        "description": game.get("description") or "",
        "playing": to_int(game.get("playing")) or 0,
        "visits": to_int(game.get("visits")) or 0,
        "favorites": to_int(game.get("favoritedCount")) or 0,
        "maxPlayers": to_int(game.get("maxPlayers")) or 0,
        "created": game.get("created"),
        "updated": game.get("updated"),
        "creator": creator,
        "genre": game.get("genre"),
        "isAllGenre": bool(game.get("isAllGenre", False)),
        "url": (
            f"https://www.roblox.com/games/{place_id}"
            if place_id
            else f"https://www.roblox.com/games/{universe_id}"
        ),
    }


def load_games() -> Dict[int, Dict[str, Any]]:
    if not os.path.exists(OUTPUT_FILE):
        return {}

    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        games = data.get("games", [])
        result: Dict[int, Dict[str, Any]] = {}

        if isinstance(games, list):
            for game in games:
                if not isinstance(game, dict):
                    continue
                universe_id = to_int(game.get("universeId"))
                if universe_id:
                    result[universe_id] = game

        return result

    except Exception as error:
        print(f"Could not load games.json: {error}")
        return {}


def save_games(games: Dict[int, Dict[str, Any]]) -> None:
    values = list(games.values())

    values.sort(
        key=lambda game: (
            to_int(game.get("playing")) or 0,
            to_int(game.get("visits")) or 0,
        ),
        reverse=True,
    )

    values = values[:TARGET_GAMES]

    output = {
        "updatedAt": time.strftime(
            "%Y-%m-%dT%H:%M:%SZ",
            time.gmtime(),
        ),
        "count": len(values),
        "games": values,
    }

    temp_file = OUTPUT_FILE + ".tmp"

    with open(temp_file, "w", encoding="utf-8") as file:
        json.dump(
            output,
            file,
            ensure_ascii=False,
            indent=2,
        )

    os.replace(temp_file, OUTPUT_FILE)
    print(f"Saved {len(values)} unique games.")


def main() -> None:
    print("========================================")
    print(" Roblox Hidden Gems Collector 3.0")
    print("========================================")

    games = load_games()
    known_ids: Set[int] = set(games.keys())

    print(f"Existing catalog: {len(known_ids)} games")

    if len(known_ids) >= TARGET_GAMES:
        print("Target already reached.")
        save_games(games)
        return

    # SEARCH
    print()
    print("============== SEARCH ==============")

    # РњРµРЅСЏРµРј Р±Р»РѕРє РїРѕРёСЃРєРѕРІС‹С… СЃР»РѕРІ РјРµР¶РґСѓ Р·Р°РїСѓСЃРєР°РјРё.
    # Р‘Р»Р°РіРѕРґР°СЂСЏ СЌС‚РѕРјСѓ СЂР°Р·РЅС‹Рµ Р·Р°РїСѓСЃРєРё РїРѕСЃС‚РµРїРµРЅРЅРѕ РїРѕРєСЂС‹РІР°СЋС‚ РєР°С‚Р°Р»РѕРі.
    run_number = int(time.time() // (6 * 60 * 60))
    offset = (run_number * MAX_SEARCH_TERMS) % len(SEARCH_TERMS)
    ordered_terms = (
        SEARCH_TERMS[offset:] + SEARCH_TERMS[:offset]
    )[:MAX_SEARCH_TERMS]

    for index, keyword in enumerate(ordered_terms, start=1):
        if len(known_ids) >= TARGET_GAMES:
            break

        print(f"[{index}/{len(ordered_terms)}] Search: {keyword}")

        found = search_keyword(keyword, known_ids)
        before = len(known_ids)
        known_ids.update(found)

        print(
            f"  New total: {len(known_ids)} "
            f"(+{len(known_ids) - before})"
        )

        time.sleep(REQUEST_DELAY)

    # RECOMMENDATIONS
    print()
    print("========== RECOMMENDATIONS ==========")

    seeds = list(known_ids)
    seeds.sort()

    if len(seeds) > MAX_RECOMMENDATION_SEEDS:
        step = max(1, len(seeds) // MAX_RECOMMENDATION_SEEDS)
        seeds = seeds[::step][:MAX_RECOMMENDATION_SEEDS]

    recommendation_count = 0

    for index, universe_id in enumerate(seeds, start=1):
        if len(known_ids) >= TARGET_GAMES:
            break
        if recommendation_count >= MAX_RECOMMENDATION_REQUESTS:
            break

        print(
            f"[{index}/{len(seeds)}] "
            f"Recommendations for {universe_id}"
        )

        recommendations = get_recommendations(universe_id)
        before = len(known_ids)
        known_ids.update(recommendations)

        print(
            f"  Found {len(recommendations)} recommendations, "
            f"+{len(known_ids) - before} new"
        )

        recommendation_count += 1
        time.sleep(REQUEST_DELAY)

    # DETAILS
    print()
    print("============== DETAILS ==============")

    missing_ids = [
        universe_id
        for universe_id in known_ids
        if universe_id not in games
    ]

    # РћРіСЂР°РЅРёС‡РёРІР°РµРј РѕР±СЉС‘Рј РѕРґРЅРѕРіРѕ Р·Р°РїСѓСЃРєР°.
    missing_ids = missing_ids[:2500]

    print(f"New games requiring details: {len(missing_ids)}")

    for start in range(0, len(missing_ids), 50):
        batch = missing_ids[start:start + 50]

        print(
            f"Details {start + 1}-"
            f"{min(start + 50, len(missing_ids))}"
        )

        details = get_details(batch)
        added = 0

        for raw_game in details:
            game = normalize_game(raw_game)
            if not game:
                continue

            universe_id = game["universeId"]

            if universe_id not in games:
                added += 1

            games[universe_id] = game

        print(f"  Added/updated: {added}")

        # РЎРѕС…СЂР°РЅСЏРµРј РїРѕСЃР»Рµ РєР°Р¶РґРѕР№ РїР°С‡РєРё.
        # Р•СЃР»Рё СЃР»РµРґСѓСЋС‰РёР№ Р·Р°РїСЂРѕСЃ СѓРїСЂС‘С‚СЃСЏ РІ Р»РёРјРёС‚, СѓР¶Рµ СЃРѕР±СЂР°РЅРЅРѕРµ РѕСЃС‚Р°РЅРµС‚СЃСЏ.
        save_games(games)

    # FINAL CLEANUP
    clean: Dict[int, Dict[str, Any]] = {}

    for game in games.values():
        universe_id = to_int(game.get("universeId"))
        if universe_id:
            clean[universe_id] = game

    save_games(clean)

    print()
    print("========================================")
    print(f"FINAL: {min(len(clean), TARGET_GAMES)} games")
    print("Duplicates removed.")
    print("========================================")


if __name__ == "__main__":
    main()
