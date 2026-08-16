import json
import os
import time
import uuid
from typing import Any, Dict, List, Optional, Set

import requests


# ============================================================
# НАСТРОЙКИ
# ============================================================

OUTPUT_FILE = "games.json"

# Максимальный размер каталога.
TARGET_GAMES = 10000

# Сколько страниц Search API пытаться получить для каждого запроса.
PAGES_PER_SEARCH = 8

# Сколько уже найденных игр использовать как источники рекомендаций.
MAX_RECOMMENDATION_SEEDS = 350

# Сколько запросов рекомендаций делать за один запуск.
MAX_RECOMMENDATION_REQUESTS = 350

# Небольшая пауза между запросами, чтобы не долбить API.
REQUEST_DELAY = 0.15

SEARCH_URL = "https://apis.roblox.com/search-api/omni-search"

DETAILS_URL = "https://games.roblox.com/v1/games"

RECOMMENDATIONS_URL = (
    "https://games.roblox.com/v1/games/"
    "recommendations/game/{universe_id}"
)


HEADERS = {
    "User-Agent": "RobloxHiddenGems/2.0",
    "Accept": "application/json",
}


# ============================================================
# ПОИСКОВЫЕ ЗАПРОСЫ
# ============================================================

SEARCH_TERMS = [
    # Общие
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

    # Roblox-жанры
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

    # Популярные механики
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

    # Разные виды игр
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

    # Тематики
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

    # Слова для менее популярных игр
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
    Надёжный GET-запрос.
    Обрабатывает временные ошибки и rate limit.
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

    # Сортировка по онлайну.
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
    # ЭТАП 1: Search API
    # --------------------------------------------------------

    print()
    print(
        "========== SEARCH =========="
    )

    for index, keyword in enumerate(
        SEARCH_TERMS,
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
    # ЭТАП 2: рекомендации
    # --------------------------------------------------------

    print()
    print(
        "======= RECOMMENDATIONS ======="
    )

    seeds = list(
        known_ids
    )

    # Берём разные игры, а не только самые популярные.
    # Поэтому каталог не должен превращаться в список
    # только из топовых игр.
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
    # ЭТАП 3: Details
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

    # Если новых игр больше 10k, не нужно
    # делать запросы для всех.
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

        # Сохраняем после каждой пачки.
        save_games(
            games
        )

    # --------------------------------------------------------
    # ФИНАЛЬНАЯ ОЧИСТКА
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
