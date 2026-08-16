import json
import os
import time
import uuid
from typing import Any, Dict, List, Optional, Set

import requests


# ============================================================
# SETTINGS
# ============================================================

OUTPUT_FILE = "games.json"

# Maximum number of games stored by the collector.
TARGET_GAMES = 10000

# Number of pages requested for every search term.
PAGES_PER_SEARCH = 15

# Recommendation seeds.
MAX_RECOMMENDATION_SEEDS = 500

# Maximum recommendation requests per run.
MAX_RECOMMENDATION_REQUESTS = 500

REQUEST_DELAY = 0.25

SEARCH_URL = "https://apis.roblox.com/search-api/omni-search"

DETAILS_URL = "https://games.roblox.com/v1/games"

RECOMMENDATIONS_URL = (
    "https://games.roblox.com/v1/games/"
    "recommendations/game/{universe_id}"
)

HEADERS = {
    "User-Agent": "RobloxHiddenGems/3.0",
    "Accept": "application/json",
}


# ============================================================
# SEARCH TERMS
# ============================================================

SEARCH_TERMS = [
    # Alphabet
    "a", "b", "c", "d", "e", "f", "g", "h", "i",
    "j", "k", "l", "m", "n", "o", "p", "q", "r",
    "s", "t", "u", "v", "w", "x", "y", "z",

    # General
    "roblox",
    "game",
    "new",
    "fun",
    "popular",
    "best",
    "original",
    "unique",
    "random",
    "test",
    "beta",
    "alpha",
    "adventure",
    "arcade",

    # Genres
    "obby",
    "obby game",
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
    "fighting",
    "battle",
    "parkour",
    "tower",
    "escape",
    "murder",
    "zombie",
    "anime",
    "strategy",
    "sandbox",
    "social",
    "hangout",
    "minigames",
    "party",
    "puzzle",
    "quiz",

    # Mechanics
    "pets",
    "pet",
    "cars",
    "car",
    "driving",
    "house",
    "houses",
    "building",
    "restaurant",
    "shop",
    "store",
    "business",
    "island",
    "space",
    "planet",
    "ocean",
    "pirate",
    "pirates",
    "prison",
    "police",
    "superhero",
    "ninja",
    "samurai",
    "knight",
    "medieval",
    "dragon",
    "monster",
    "dungeon",
    "quest",
    "boss",
    "magic",
    "fantasy",
    "sci fi",
    "alien",
    "vampire",
    "witch",
    "farm",
    "farming",
    "fishing",
    "camping",
    "school",
    "city",
    "town",
    "village",
    "hospital",
    "airport",
    "train",
    "subway",
    "bus",
    "hotel",
    "mall",
    "museum",
    "theme park",

    # Combat
    "war",
    "army",
    "military",
    "gun",
    "guns",
    "battle royale",
    "deathmatch",
    "duel",
    "duels",
    "1v1",
    "2v2",
    "3v3",
    "4v4",
    "team",
    "capture",
    "defense",
    "tower defense",
    "bedwars",
    "battlegrounds",

    # Horror
    "scary",
    "creepy",
    "horror story",
    "survival horror",
    "backrooms",
    "monster",
    "escape room",
    "maze",
    "night",
    "dark",

    # Anime
    "anime",
    "anime rpg",
    "anime simulator",
    "anime fighters",
    "anime battle",
    "anime adventures",
    "one piece",
    "naruto",
    "dragon ball",
    "bleach",
    "demon slayer",
    "jujutsu",
    "my hero",
    "pokemon",

    # More discovery terms
    "hidden",
    "hidden gem",
    "underrated",
    "small game",
    "indie",
    "community",
    "multiplayer",
    "friends",
    "chill",
    "casual",
    "competitive",
    "hard",
    "easy",
    "challenge",
    "speedrun",
    "clicker",
    "idle",
    "incremental",
    "grinding",
    "quest",
    "survival",
    "open world",
]


# ============================================================
# HTTP
# ============================================================

session = requests.Session()
session.headers.update(HEADERS)


def get_json(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    retries: int = 5,
) -> Optional[Any]:

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
                wait = min(30, attempt * 5)

                print(
                    f"Rate limit. Waiting {wait}s..."
                )

                time.sleep(wait)
                continue

            if response.status_code in (
                500,
                502,
                503,
                504,
            ):
                wait = attempt * 3

                print(
                    f"Server error "
                    f"{response.status_code}. "
                    f"Waiting {wait}s..."
                )

                time.sleep(wait)
                continue

            print(
                f"HTTP {response.status_code}: "
                f"{url}"
            )

        except requests.RequestException as error:

            print(
                f"Request error "
                f"{attempt}/{retries}: "
                f"{error}"
            )

            time.sleep(
                attempt * 2
            )

    return None


# ============================================================
# ID HELPERS
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

    for key in (
        "universeId",
        "universeID",
        "universe_id",
        "gameId",
        "id",
    ):

        value = to_int(
            item.get(key)
        )

        if value:
            return value

    for key in (
        "game",
        "experience",
        "universe",
    ):

        nested = item.get(key)

        if isinstance(
            nested,
            dict,
        ):

            value = extract_universe_id(
                nested
            )

            if value:
                return value

    return None


# ============================================================
# SEARCH
# ============================================================

def extract_search_items(
    data: Any,
) -> List[Dict[str, Any]]:

    result = []

    def walk(value: Any):

        if isinstance(value, dict):

            universe_id = extract_universe_id(
                value
            )

            if universe_id:
                result.append(value)

            for child in value.values():
                walk(child)

        elif isinstance(value, list):

            for child in value:
                walk(child)

    walk(data)

    return result


def search_page(
    keyword: str,
    session_id: str,
    page_token: str = "",
) -> tuple[List[int], str]:

    params = {
        "searchQuery": keyword,
        "sessionId": session_id,
        "pageType": "all",
    }

    if page_token:
        params["pageToken"] = page_token

    data = get_json(
        SEARCH_URL,
        params=params,
    )

    if not isinstance(
        data,
        dict,
    ):
        return [], ""

    items = extract_search_items(
        data
    )

    ids = []

    for item in items:

        universe_id = extract_universe_id(
            item
        )

        if (
            universe_id
            and universe_id not in ids
        ):
            ids.append(
                universe_id
            )

    next_token = ""

    for key in (
        "nextPageToken",
        "nextPageCursor",
        "nextCursor",
    ):

        value = data.get(key)

        if (
            isinstance(value, str)
            and value
        ):

            next_token = value
            break

    return ids, next_token


def search_keyword(
    keyword: str,
    known_ids: Set[int],
) -> Set[int]:

    found = set()

    # IMPORTANT:
    # The same session ID is kept for all pages
    # of this search.
    session_id = str(
        uuid.uuid4()
    )

    page_token = ""

    for page in range(
        1,
        PAGES_PER_SEARCH + 1,
    ):

        ids, next_token = search_page(
            keyword,
            session_id,
            page_token,
        )

        if not ids:
            break

        before = len(found)

        for universe_id in ids:

            if universe_id not in known_ids:
                found.add(
                    universe_id
                )

            if (
                len(found)
                >= TARGET_GAMES
            ):
                break

        print(
            f"    page {page}: "
            f"{len(ids)} results, "
            f"{len(found) - before} new"
        )

        if (
            len(found)
            >= TARGET_GAMES
        ):
            break

        if not next_token:
            break

        if next_token == page_token:
            break

        page_token = next_token

        time.sleep(
            REQUEST_DELAY
        )

    return found


# ============================================================
# RECOMMENDATIONS
# ============================================================

def extract_ids_from_any(
    data: Any,
) -> Set[int]:

    result = set()

    def walk(value: Any):

        if isinstance(value, dict):

            universe_id = extract_universe_id(
                value
            )

            if universe_id:
                result.add(
                    universe_id
                )

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

    data = get_json(
        url
    )

    if not data:
        return set()

    return extract_ids_from_any(
        data
    )


# ============================================================
# DETAILS
# ============================================================

def get_game_details(
    universe_ids: List[int],
) -> List[Dict[str, Any]]:

    result = []

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

        if isinstance(
            data,
            dict,
        ):

            games = data.get(
                "data",
                [],
            )

            if isinstance(
                games,
                list,
            ):
                result.extend(
                    games
                )

        time.sleep(
            REQUEST_DELAY
        )

    return result


# ============================================================
# NORMALIZE
# ============================================================

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

    return {
        "universeId": universe_id,
        "placeId": place_id,
        "name": (
            game.get("name")
            or "Unknown game"
        ),
        "description": (
            game.get("description")
            or ""
        ),
        "playing": (
            to_int(
                game.get("playing")
            )
            or 0
        ),
        "visits": (
            to_int(
                game.get("visits")
            )
            or 0
        ),
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
        "creator": game.get(
            "creator"
        ),
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
# LOAD / SAVE
# ============================================================

def load_games() -> Dict[
    int,
    Dict[str, Any]
]:

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

        result = {}

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
                    result[
                        universe_id
                    ] = game

        return result

    except Exception as error:

        print(
            f"games.json read error: "
            f"{error}"
        )

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

    # No duplicates because the dictionary
    # is keyed by universeId.

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
        f"Saved {len(values)} games."
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print(
        "=========================================="
    )
    print(
        " Roblox Hidden Gems Collector"
    )
    print(
        "=========================================="
    )

    games = load_games()

    known_ids = set(
        games.keys()
    )

    print(
        f"Existing games: {len(known_ids)}"
    )

    if len(known_ids) >= TARGET_GAMES:

        print(
            "Target already reached."
        )

        return

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    print()
    print(
        "=============== SEARCH =================="
    )

    for index, keyword in enumerate(
        SEARCH_TERMS,
        1,
    ):

        if len(known_ids) >= TARGET_GAMES:
            break

        print()
        print(
            f"[{index}/{len(SEARCH_TERMS)}] "
            f"Searching: {keyword}"
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
            f"    Total: "
            f"{len(known_ids)} "
            f"(+{len(known_ids) - before})"
        )

        time.sleep(
            REQUEST_DELAY
        )

    # --------------------------------------------------------
    # RECOMMENDATIONS
    # --------------------------------------------------------

    print()
    print(
        "============ RECOMMENDATIONS ==========="
    )

    seeds = list(
        known_ids
    )

    # Распределяем seeds по всему каталогу,
    # а не берём только первые ID.
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

    for index, universe_id in enumerate(
        seeds,
        1,
    ):

        if len(known_ids) >= TARGET_GAMES:
            break

        if (
            index
            > MAX_RECOMMENDATION_REQUESTS
        ):
            break

        print(
            f"[{index}/{len(seeds)}] "
            f"Game {universe_id}"
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

            if (
                len(known_ids)
                >= TARGET_GAMES
            ):
                break

        print(
            f"    Recommendations: "
            f"{len(recommendations)} | "
            f"New: "
            f"{len(known_ids) - before}"
        )

        time.sleep(
            REQUEST_DELAY
        )

    # --------------------------------------------------------
    # DETAILS
    # --------------------------------------------------------

    print()
    print(
        "=============== DETAILS ================"
    )

    missing = [
        universe_id
        for universe_id in known_ids
        if universe_id not in games
    ]

    missing = missing[
        :TARGET_GAMES
    ]

    print(
        f"Games needing details: "
        f"{len(missing)}"
    )

    for start in range(
        0,
        len(missing),
        50,
    ):

        batch = missing[
            start:start + 50
        ]

        print(
            f"Batch "
            f"{start + 1}-"
            f"{min(start + 50, len(missing))}"
        )

        details = get_game_details(
            batch
        )

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

            games[
                universe_id
            ] = game

        # Сохраняем после каждой пачки.
        save_games(
            games
        )

    # --------------------------------------------------------
    # FINAL CLEANUP
    # --------------------------------------------------------

    clean = {}

    for game in games.values():

        universe_id = to_int(
            game.get(
                "universeId"
            )
        )

        if universe_id:
            clean[
                universe_id
            ] = game

    save_games(
        clean
    )

    print()
    print(
        "=========================================="
    )
    print(
        f"Finished: "
        f"{min(len(clean), TARGET_GAMES)} games"
    )
    print(
        "Duplicates: removed"
    )
    print(
        "==========================================" 
    )


if __name__ == "__main__":
    main()
