import json
import os
import time
import uuid
from typing import Any, Dict, List, Optional, Set

import requests


# ============================================================
# РќРђРЎРўР РћР™РљР
# ============================================================

OUTPUT_FILE = "games.json"

# РњР°РєСЃРёРјР°Р»СЊРЅС‹Р№ СЂР°Р·РјРµСЂ РєР°С‚Р°Р»РѕРіР°.
TARGET_GAMES = 10000

# РЎРєРѕР»СЊРєРѕ СЃС‚СЂР°РЅРёС† Search API РїС‹С‚Р°С‚СЊСЃСЏ РїРѕР»СѓС‡РёС‚СЊ РґР»СЏ РєР°Р¶РґРѕРіРѕ Р·Р°РїСЂРѕСЃР°.
PAGES_PER_SEARCH = 2

# РЎРєРѕР»СЊРєРѕ СѓР¶Рµ РЅР°Р№РґРµРЅРЅС‹С… РёРіСЂ РёСЃРїРѕР»СЊР·РѕРІР°С‚СЊ РєР°Рє РёСЃС‚РѕС‡РЅРёРєРё СЂРµРєРѕРјРµРЅРґР°С†РёР№.
MAX_RECOMMENDATION_SEEDS = 25

# РЎРєРѕР»СЊРєРѕ Р·Р°РїСЂРѕСЃРѕРІ СЂРµРєРѕРјРµРЅРґР°С†РёР№ РґРµР»Р°С‚СЊ Р·Р° РѕРґРёРЅ Р·Р°РїСѓСЃРє.
MAX_RECOMMENDATION_REQUESTS = 25

# РќРµР±РѕР»СЊС€Р°СЏ РїР°СѓР·Р° РјРµР¶РґСѓ Р·Р°РїСЂРѕСЃР°РјРё, С‡С‚РѕР±С‹ РЅРµ РґРѕР»Р±РёС‚СЊ API.
REQUEST_DELAY = 0.35

SEARCH_URL = "https://apis.roblox.com/search-api/omni-search"

DETAILS_URL = "https://games.roblox.com/v1/games"

RECOMMENDATIONS_URL = (
    "https://games.roblox.com/v1/games/"
    "recommendations/game/{universe_id}"
)


HEADERS = {
    "User-Agent": "RobloxHiddenGems/4.0",
    "Accept": "application/json",
}


# ============================================================
# РџРћРРЎРљРћР’Р«Р• Р—РђРџР РћРЎР«
# ============================================================

SEARCH_TERMS = [
    # РћР±С‰РёРµ
    "a",
    "e",
    "i",
    "o",
    "s",
    "t",
    "r",
    "n",
    "m",
    "b",
    "c",
    "d",
    "f",
    "g",
    "h",
    "j",
    "k",
    "l",
    "p",
    "q",
    "u",
    "v",
    "w",
    "x",
    "y",
    "z",

    # Roblox-Р¶Р°РЅСЂС‹
    "obby",
    "obby 2",
    "obby 3",
    "simulator",
    "tycoon",
    "roleplay",
    "rp",
    "rpg",
    "horror",
    "survival",
    "adventure",
    "story",
    "pvp",
    "fps",
    "shooter",
    "racing",
    "rpg",
    "fighting",
    "battle",
    "parkour",
    "tower",
    "escape",
    "murder",
    "zombie",
    "zombies",
    "anime",
    "magic",
    "war",
    "military",
    "city",
    "school",
    "family",
    "life",
    "social",
    "hangout",
    "building",
    "sandbox",
    "strategy",
    "horror story",
    "scary",
    "survival horror",
    "open world",
    "adventure game",

    # РџРѕРїСѓР»СЏСЂРЅС‹Рµ РјРµС…Р°РЅРёРєРё
    "pets",
    "pet",
    "cars",
    "car",
    "driving",
    "house",
    "houses",
    "restaurant",
    "shop",
    "store",
    "business",
    "casino",
    "island",
    "islands",
    "space",
    "planet",
    "ocean",
    "pirate",
    "pirates",
    "prison",
    "police",
    "superhero",
    "superheroes",
    "ninja",
    "samurai",
    "knight",
    "medieval",
    "dragon",
    "dragons",
    "monster",
    "monsters",
    "dungeon",
    "dungeons",
    "quest",
    "quests",
    "boss",
    "bosses",
    "guns",
    "gun",
    "war",
    "army",
    "zombie",
    "vampire",
    "vampires",
    "witch",
    "magic",
    "fantasy",
    "sci fi",
    "sci-fi",
    "space",
    "alien",
    "aliens",

    # Р Р°Р·РЅС‹Рµ РІРёРґС‹ РёРіСЂ
    "clicker",
    "idle",
    "incremental",
    "tower defense",
    "defense",
    "defend",
    "capture",
    "capture the flag",
    "bedwars",
    "battlegrounds",
    "battle royale",
    "deathmatch",
    "duel",
    "duels",
    "1v1",
    "2v2",
    "3v3",
    "4v4",
    "team",
    "teams",
    "hide and seek",
    "hide",
    "seek",
    "escape room",
    "escape",
    "maze",
    "puzzle",
    "puzzles",
    "quiz",
    "minigames",
    "mini games",
    "party",
    "friends",
    "funny",
    "fun",

    # РўРµРјР°С‚РёРєРё
    "minecraft",
    "backrooms",
    "doors",
    "rainbow",
    "night",
    "day",
    "city",
    "town",
    "village",
    "farm",
    "farming",
    "fishing",
    "camping",
    "hospital",
    "airport",
    "train",
    "subway",
    "bus",
    "school",
    "university",
    "hotel",
    "mall",
    "supermarket",
    "bank",
    "museum",
    "theme park",
    "amusement park",

    # Anime / fandom-style searches
    "one piece",
    "naruto",
    "dragon ball",
    "bleach",
    "demon slayer",
    "jujutsu",
    "my hero",
    "pokemon",
    "anime fighters",
    "anime adventures",
    "anime battle",
    "anime rpg",
    "anime simulator",

    # РЎР»РѕРІР° РґР»СЏ РјРµРЅРµРµ РїРѕРїСѓР»СЏСЂРЅС‹С… РёРіСЂ
    "new",
    "new game",
    "indie",
    "small game",
    "hidden gem",
    "underrated",
    "beta",
    "early access",
    "testing",
    "test",
    "demo",
    "original",
    "unique",
    "random",
    "simple",
]


# ============================================================
# HTTP
# ============================================================

session = requests.Session()
session.headers.update(HEADERS)


def get_json(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    retries: int = 4,
) -> Optional[Any]:
    """
    РќР°РґС‘Р¶РЅС‹Р№ GET-Р·Р°РїСЂРѕСЃ.
    РћР±СЂР°Р±Р°С‚С‹РІР°РµС‚ РІСЂРµРјРµРЅРЅС‹Рµ РѕС€РёР±РєРё Рё rate limit.
    """

    for attempt in range(1, retries + 1):

        try:
            response = session.get(
                url,
                params=params,
                timeout=30,
            )

            if response.status_code == 200:
                return response.json()

            if response.status_code == 429:
                wait_time = min(15, attempt * 4)

                print(
                    f"Rate limit. Waiting "
                    f"{wait_time}s..."
                )

                time.sleep(wait_time)
                continue

            if response.status_code in (
                500,
                502,
                503,
                504,
            ):
                wait_time = attempt * 2

                print(
                    f"Server error "
                    f"{response.status_code}. "
                    f"Retry in {wait_time}s..."
                )

                time.sleep(wait_time)
                continue

            print(
                f"HTTP {response.status_code}: "
                f"{url}"
            )

        except requests.RequestException as error:
            print(
                f"Request error "
                f"({attempt}/{retries}): "
                f"{error}"
            )

            time.sleep(attempt * 2)

    return None


# ============================================================
# ID
# ============================================================

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


def extract_universe_id(
    item: Dict[str, Any],
) -> Optional[int]:

    keys = [
        "universeId",
        "universeID",
        "universe_id",
        "id",
        "gameId",
    ]

    for key in keys:

        value = to_int(item.get(key))

        if value:
            return value

    for key in (
        "game",
        "experience",
        "universe",
        "place",
    ):

        nested = item.get(key)

        if isinstance(nested, dict):

            result = extract_universe_id(
                nested
            )

            if result:
                return result

    return None


# ============================================================
# SEARCH API
# ============================================================

def find_search_items(
    data: Any,
) -> List[Dict[str, Any]]:

    found: List[Dict[str, Any]] = []

    def walk(value: Any):

        if isinstance(value, dict):

            universe_id = extract_universe_id(
                value
            )

            if universe_id:
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
) -> tuple[List[int], str]:

    params = {
        "searchQuery": keyword,
        "sessionId": str(uuid.uuid4()),
        "pageType": "all",
        "pageToken": page_token,
    }

    data = get_json(
        SEARCH_URL,
        params=params,
    )

    if not data:
        return [], ""

    items = find_search_items(data)

    ids: List[int] = []

    for item in items:

        universe_id = extract_universe_id(
            item
        )

        if universe_id and universe_id not in ids:
            ids.append(universe_id)

    # Search API has changed its response shape
    # over time, so support several possible names.
    next_token = ""

    for key in (
        "nextPageToken",
        "nextPageCursor",
        "nextCursor",
        "pageToken",
    ):

        value = data.get(key)

        if isinstance(value, str) and value:
            next_token = value
            break

    return ids, next_token


def search_keyword(
    keyword: str,
    known_ids: Set[int],
) -> Set[int]:

    found: Set[int] = set()

    token = ""

    for page in range(
        1,
        PAGES_PER_SEARCH + 1,
    ):

        ids, next_token = search_page(
            keyword,
            token,
        )

        if not ids:
            break

        new_count = 0

        for universe_id in ids:

            if universe_id not in known_ids:
                found.add(universe_id)
                new_count += 1

        print(
            f"    page {page}: "
            f"{len(ids)} found, "
            f"{new_count} new"
        )

        if len(found) >= TARGET_GAMES:
            break

        if not next_token:
            break

        if next_token == token:
            break

        token = next_token

        time.sleep(
            REQUEST_DELAY
        )

    return found


# ============================================================
# RECOMMENDATIONS
# ============================================================

def extract_recommendation_ids(
    data: Any,
) -> Set[int]:

    result: Set[int] = set()

    def walk(value: Any):

        if isinstance(value, dict):

            universe_id = extract_universe_id(
                value
            )

            if universe_id:
                result.add(universe_id)

            for child in value.values():
                walk(child)

        elif isinstance(value, list):

            for child in value:
                walk(child)

    walk(data)

    return result


def get_recommendations(
    universe_id: int,
) -> Set[int]:

    url = RECOMMENDATIONS_URL.format(
        universe_id=universe_id
    )

    data = get_json(url)

    if not data:
        return set()

    return extract_recommendation_ids(
        data
    )


# ============================================================
# GAME DETAILS
# ============================================================

def get_details(
    universe_ids: List[int],
) -> List[Dict[str, Any]]:

    result: List[Dict[str, Any]] = []

    for start in range(
        0,
        len(universe_ids),
        50,
    ):

        batch = universe_ids[
            start:start + 50
        ]

        params = {
            "universeIds": ",".join(
                str(x)
                for x in batch
            )
        }

        data = get_json(
            DETAILS_URL,
            params=params,
        )

        if isinstance(data, dict):

            games = data.get(
                "data",
                [],
            )

            if isinstance(
                games,
                list,
            ):
                result.extend(games)

        time.sleep(
            REQUEST_DELAY
        )

    return result


# ============================================================
# NORMALIZE
# ============================================================

THUMBNAIL_URL = (
    "https://thumbnails.roblox.com/v1/games/icons"
    "?universeIds={universe_id}"
    "&returnPolicy=PlaceHolder"
    "&size=512x512"
    "&format=Png"
    "&isCircular=false"
)


def thumbnail_url(universe_id: int) -> str:
    return THUMBNAIL_URL.format(universe_id=universe_id)


def normalize_game(
    game: Dict[str, Any],
) -> Optional[Dict[str, Any]]:

    universe_id = to_int(
        game.get("id")
    )

    if not universe_id:
        universe_id = to_int(
            game.get("universeId")
        )

    if not universe_id:
        return None

    place_id = to_int(
        game.get("rootPlaceId")
    )

    if not place_id:
        place_id = to_int(
            game.get("placeId")
        )

    creator = game.get(
        "creator"
    )

    if not isinstance(
        creator,
        dict,
    ):
        creator = None

    return {
        "universeId": universe_id,
        "placeId": place_id,
        "thumbnail": thumbnail_url(universe_id),
        "name": (
            game.get("name")
            or "Unknown game"
        ),
        "description": (
            game.get("description")
            or ""
        ),
        "playing": to_int(
            game.get("playing")
        ) or 0,
        "visits": to_int(
            game.get("visits")
        ) or 0,
        "favorites": (
            to_int(
                game.get(
                    "favoritedCount"
                )
            )
            or 0
        ),
        "maxPlayers": (
            to_int(
                game.get(
                    "maxPlayers"
                )
            )
            or 0
        ),
        "created": game.get(
            "created"
        ),
        "updated": game.get(
            "updated"
        ),
        "creator": creator,
        "genre": game.get(
            "genre"
        ),
        "url": (
            f"https://www.roblox.com/games/"
            f"{place_id}"
            if place_id
            else
            f"https://www.roblox.com/games/"
            f"{universe_id}"
        ),
    }


# ============================================================
# FILE
# ============================================================

def load_games() -> Dict[int, Dict[str, Any]]:

    if not os.path.exists(
        OUTPUT_FILE
    ):
        return {}

    try:

        with open(
            OUTPUT_FILE,
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        games = data.get(
            "games",
            [],
        )

        result: Dict[
            int,
            Dict[str, Any]
        ] = {}

        if isinstance(
            games,
            list,
        ):

            for game in games:

                if not isinstance(
                    game,
                    dict,
                ):
                    continue

                universe_id = to_int(
                    game.get(
                        "universeId"
                    )
                )

                if universe_id:
                    game.setdefault("thumbnail", thumbnail_url(universe_id))
                    result[
                        universe_id
                    ] = game

        return result

    except Exception as error:

        print(
            "Could not load games.json:"
        )

        print(error)

        return {}


def save_games(
    games: Dict[
        int,
        Dict[str, Any]
    ],
) -> None:

    values = list(
        games.values()
    )

    # РЎРѕСЂС‚РёСЂРѕРІРєР° РїРѕ РѕРЅР»Р°Р№РЅСѓ.
    values.sort(
        key=lambda game: (
            int(
                game.get(
                    "playing",
                    0
                )
                or 0
            ),
            int(
                game.get(
                    "visits",
                    0
                )
                or 0
            ),
        ),
        reverse=True,
    )

    values = values[
        :TARGET_GAMES
    ]

    output = {
        "updatedAt": time.strftime(
            "%Y-%m-%dT%H:%M:%SZ",
            time.gmtime(),
        ),
        "count": len(values),
        "games": values,
    }

    temp_file = (
        OUTPUT_FILE
        + ".tmp"
    )

    with open(
        temp_file,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            output,
            file,
            ensure_ascii=False,
            indent=2,
        )

    os.replace(
        temp_file,
        OUTPUT_FILE,
    )

    print(
        f"Saved {len(values)} "
        f"unique games."
    )


# ============================================================
# MAIN
# ============================================================



def refresh_existing_games(games: Dict[int, Dict[str, Any]]) -> None:
    """Refresh online/favorites/visits for existing games in batches."""
    ids = list(games.keys())
    ids.sort(key=lambda uid: int(games[uid].get("playing", 0) or 0), reverse=True)
    ids = ids[:1000]

    print()
    print("========== REFRESH LIVE STATS ==========")
    print(f"Refreshing {len(ids)} existing games...")

    for start in range(0, len(ids), 50):
        batch = ids[start:start + 50]
        details = get_details(batch)
        updated = 0

        for raw_game in details:
            game = normalize_game(raw_game)
            if not game:
                continue
            uid = game["universeId"]
            old = games.get(uid, {})
            for key, value in old.items():
                game.setdefault(key, value)
            game["thumbnail"] = thumbnail_url(uid)
            games[uid] = game
            updated += 1

        print(f"  {start + 1}-{min(start + 50, len(ids))}: {updated} updated")
        save_games(games)


def main() -> None:

    print()
    print(
        "========================================"
    )
    print(
        " Roblox Hidden Gems Collector 2.0"
    )
    print(
        "========================================"
    )
    print()

    games = load_games()

    known_ids: Set[int] = set(
        games.keys()
    )

    print(
        f"Existing catalog: "
        f"{len(known_ids)} games"
    )

    if len(known_ids) >= TARGET_GAMES:

        print(
            "Target already reached."
        )

        save_games(games)

        return

    # --------------------------------------------------------
    # РРўРђРџ 1: Search API
    # --------------------------------------------------------

    print()
    print(
        "========== SEARCH =========="
    )

    run_slot = int(time.time() // (6 * 60 * 60))
    terms_count = 20
    offset = (run_slot * terms_count) % len(SEARCH_TERMS)
    rotating_terms = (SEARCH_TERMS[offset:] + SEARCH_TERMS[:offset])[:terms_count]

    for index, keyword in enumerate(
        rotating_terms,
        start=1,
    ):
        if len(known_ids) >= TARGET_GAMES:
            break

        print()
        print(
            f"[{index}/{len(SEARCH_TERMS)}] "
            f"Search: {keyword}"
        )

        found = search_keyword(
            keyword,
            known_ids,
        )

        before = len(
            known_ids
        )

        known_ids.update(
            found
        )

        print(
            f"    New total: "
            f"{len(known_ids)} "
            f"(+{len(known_ids) - before})"
        )

        time.sleep(
            REQUEST_DELAY
        )

    # --------------------------------------------------------
    # РРўРђРџ 2: СЂРµРєРѕРјРµРЅРґР°С†РёРё
    # --------------------------------------------------------

    print()
    print(
        "======= RECOMMENDATIONS ======="
    )

    seeds = list(
        known_ids
    )

    # Р‘РµСЂС‘Рј СЂР°Р·РЅС‹Рµ РёРіСЂС‹, Р° РЅРµ С‚РѕР»СЊРєРѕ СЃР°РјС‹Рµ РїРѕРїСѓР»СЏСЂРЅС‹Рµ.
    # РџРѕСЌС‚РѕРјСѓ РєР°С‚Р°Р»РѕРі РЅРµ РґРѕР»Р¶РµРЅ РїСЂРµРІСЂР°С‰Р°С‚СЊСЃСЏ РІ СЃРїРёСЃРѕРє
    # С‚РѕР»СЊРєРѕ РёР· С‚РѕРїРѕРІС‹С… РёРіСЂ.
    seeds.sort()

    if len(seeds) > MAX_RECOMMENDATION_SEEDS:

        step = max(
            1,
            len(seeds)
            // MAX_RECOMMENDATION_SEEDS,
        )

        seeds = seeds[
            ::step
        ][
            :MAX_RECOMMENDATION_SEEDS
        ]

    recommendation_count = 0

    for index, universe_id in enumerate(
        seeds,
        start=1,
    ):

        if len(known_ids) >= TARGET_GAMES:
            break

        if (
            recommendation_count
            >= MAX_RECOMMENDATION_REQUESTS
        ):
            break

        print(
            f"[{index}/{len(seeds)}] "
            f"Recommendations for "
            f"{universe_id}"
        )

        recommendations = (
            get_recommendations(
                universe_id
            )
        )

        before = len(
            known_ids
        )

        for recommended_id in (
            recommendations
        ):

            known_ids.add(
                recommended_id
            )

        added = (
            len(known_ids)
            - before
        )

        print(
            f"    Found "
            f"{len(recommendations)} "
            f"recommendations, "
            f"+{added} new"
        )

        recommendation_count += 1

        time.sleep(
            REQUEST_DELAY
        )

    # --------------------------------------------------------
    # РРўРђРџ 3: Details
    # --------------------------------------------------------

    print()
    print(
        "=========== DETAILS ==========="
    )

    missing_ids = [
        universe_id
        for universe_id in known_ids
        if universe_id not in games
    ]

    # Р•СЃР»Рё РЅРѕРІС‹С… РёРіСЂ Р±РѕР»СЊС€Рµ 10k, РЅРµ РЅСѓР¶РЅРѕ
    # РґРµР»Р°С‚СЊ Р·Р°РїСЂРѕСЃС‹ РґР»СЏ РІСЃРµС….
    missing_ids = missing_ids[
        :TARGET_GAMES
    ]

    print(
        f"New games requiring details: "
        f"{len(missing_ids)}"
    )

    for start in range(
        0,
        len(missing_ids),
        50,
    ):

        batch = missing_ids[
            start:start + 50
        ]

        print(
            f"Details "
            f"{start + 1}-"
            f"{min(start + 50, len(missing_ids))}"
        )

        details = get_details(
            batch
        )

        added = 0

        for raw_game in details:

            game = normalize_game(
                raw_game
            )

            if not game:
                continue

            universe_id = (
                game[
                    "universeId"
                ]
            )

            if universe_id not in games:
                added += 1

            games[
                universe_id
            ] = game

        print(
            f"    Added/updated: "
            f"{added}"
        )

        # РЎРѕС…СЂР°РЅСЏРµРј РїРѕСЃР»Рµ РєР°Р¶РґРѕР№ РїР°С‡РєРё.
        save_games(
            games
        )

    # --------------------------------------------------------
    # REFRESH EXISTING GAMES
    # --------------------------------------------------------
    refresh_existing_games(games)

    # --------------------------------------------------------
    # Р¤РРќРђР›Р¬РќРђРЇ РћР§РРЎРўРљРђ
    # --------------------------------------------------------

    clean: Dict[
        int,
        Dict[str, Any]
    ] = {}

    for game in games.values():

        universe_id = to_int(
            game.get(
                "universeId"
            )
        )

        if universe_id:
            game["thumbnail"] = thumbnail_url(universe_id)
            clean[
                universe_id
            ] = game

    save_games(
        clean
    )

    print()
    print(
        "========================================"
    )
    print(
        f"FINAL: {min(len(clean), TARGET_GAMES)} games"
    )
    print(
        "Duplicates removed."
    )
    print(
        "========================================"
    )


if __name__ == "__main__":
    main()
