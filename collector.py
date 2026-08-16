import json
import os
import time
import uuid
from typing import Any, Dict, List

import requests


OUTPUT_FILE = "games.json"
TARGET_GAMES = 10000

SEARCH_URL = "https://apis.roblox.com/search-api/omni-search"
DETAILS_URL = "https://games.roblox.com/v1/games"

HEADERS = {
    "User-Agent": "RobloxGameFinder/1.0",
    "Accept": "application/json",
}


# Слова нужны для того, чтобы находить разные категории игр.
# Это не означает, что игра обязана содержать слово в названии.
SEARCH_TERMS = [
    "a",
    "b",
    "c",
    "d",
    "e",
    "f",
    "g",
    "h",
    "i",
    "j",
    "k",
    "l",
    "m",
    "n",
    "o",
    "p",
    "q",
    "r",
    "s",
    "t",
    "u",
    "v",
    "w",
    "x",
    "y",
    "z",
    "roblox",
    "obby",
    "simulator",
    "tycoon",
    "horror",
    "survival",
    "roleplay",
    "rpg",
    "anime",
    "fps",
    "shooter",
    "racing",
    "adventure",
    "story",
    "pvp",
    "battle",
    "parkour",
    "tower",
    "escape",
    "obby",
    "fighting",
    "school",
    "city",
    "murder",
    "zombie",
    "halloween",
    "fun",
    "friends",
]


session = requests.Session()
session.headers.update(HEADERS)


def request_json(
    url: str,
    params: Dict[str, Any] | None = None,
    retries: int = 3,
) -> Any:
    """GET JSON с несколькими попытками."""

    for attempt in range(1, retries + 1):
        try:
            response = session.get(
                url,
                params=params,
                timeout=30,
            )

            if response.status_code == 200:
                return response.json()

            print(
                f"HTTP {response.status_code}: "
                f"{url}"
            )

        except requests.RequestException as error:
            print(
                f"Request error ({attempt}/{retries}): "
                f"{error}"
            )

        time.sleep(attempt * 2)

    return None


def extract_universe_id(item: Dict[str, Any]) -> int | None:
    """Пытается найти Universe ID в разных форматах ответа."""

    possible_keys = [
        "universeId",
        "universeID",
        "id",
        "gameId",
    ]

    for key in possible_keys:
        value = item.get(key)

        if isinstance(value, int):
            return value

        if isinstance(value, str) and value.isdigit():
            return int(value)

    # Иногда данные могут находиться внутри nested-полей.
    for key in ["game", "experience", "universe"]:
        nested = item.get(key)

        if isinstance(nested, dict):
            result = extract_universe_id(nested)

            if result:
                return result

    return None


def extract_search_games(data: Any) -> List[Dict[str, Any]]:
    """Извлекает игры из ответа Search API."""

    result: List[Dict[str, Any]] = []

    if not isinstance(data, dict):
        return result

    # Рекурсивно ищем объекты, похожие на игры.
    def walk(value: Any) -> None:
        if isinstance(value, dict):
            universe_id = extract_universe_id(value)

            if universe_id:
                result.append(value)

            for child in value.values():
                walk(child)

        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(data)

    return result


def search_games(keyword: str) -> List[int]:
    """Ищет Universe IDs через Roblox Search API."""

    session_id = str(uuid.uuid4())

    params = {
        "searchQuery": keyword,
        "sessionId": session_id,
        "pageType": "all",
    }

    data = request_json(
        SEARCH_URL,
        params=params,
    )

    if data is None:
        return []

    items = extract_search_games(data)

    ids: List[int] = []

    for item in items:
        universe_id = extract_universe_id(item)

        if universe_id and universe_id not in ids:
            ids.append(universe_id)

    return ids


def get_game_details(universe_ids: List[int]) -> List[Dict[str, Any]]:
    """Получает подробную информацию об играх."""

    if not universe_ids:
        return []

    results: List[Dict[str, Any]] = []

    # Roblox принимает список universeIds.
    # Небольшие пачки безопаснее для запроса.
    for start in range(0, len(universe_ids), 50):
        batch = universe_ids[start:start + 50]

        params = {
            "universeIds": ",".join(
                str(game_id)
                for game_id in batch
            )
        }

        data = request_json(
            DETAILS_URL,
            params=params,
        )

        if not data:
            continue

        games = data.get("data", [])

        if isinstance(games, list):
            results.extend(games)

        time.sleep(0.2)

    return results


def normalize_game(game: Dict[str, Any]) -> Dict[str, Any] | None:
    """Приводит игру к удобному формату для сайта."""

    universe_id = game.get("id")

    if not universe_id:
        universe_id = game.get("universeId")

    root_place_id = game.get("rootPlaceId")

    name = game.get("name") or "Без названия"

    if not universe_id:
        return None

    try:
        universe_id = int(universe_id)
    except (TypeError, ValueError):
        return None

    if root_place_id:
        try:
            root_place_id = int(root_place_id)
        except (TypeError, ValueError):
            root_place_id = None

    return {
        "universeId": universe_id,
        "placeId": root_place_id,
        "name": name,
        "description": game.get("description") or "",
        "playing": int(game.get("playing") or 0),
        "visits": int(game.get("visits") or 0),
        "favorites": int(game.get("favoritedCount") or 0),
        "maxPlayers": int(game.get("maxPlayers") or 0),
        "created": game.get("created"),
        "updated": game.get("updated"),
        "creator": game.get("creator"),
        "genre": game.get("genre"),
        "isAllGenre": game.get("isAllGenre"),
        "url": (
            f"https://www.roblox.com/games/"
            f"{root_place_id}"
        )
        if root_place_id
        else (
            f"https://www.roblox.com/games/"
            f"{universe_id}"
        ),
    }


def load_existing_games() -> Dict[int, Dict[str, Any]]:
    """Загружает уже существующий games.json."""

    if not os.path.exists(OUTPUT_FILE):
        return {}

    try:
        with open(
            OUTPUT_FILE,
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        games = data.get("games", [])

        result: Dict[int, Dict[str, Any]] = {}

        for game in games:
            universe_id = game.get("universeId")

            if universe_id:
                result[int(universe_id)] = game

        return result

    except Exception as error:
        print(
            f"Could not read existing games.json: "
            f"{error}"
        )

        return {}


def save_games(games: List[Dict[str, Any]]) -> None:
    """Сохраняет каталог."""

    games.sort(
        key=lambda game: (
            int(game.get("playing") or 0),
            int(game.get("visits") or 0),
        ),
        reverse=True,
    )

    games = games[:TARGET_GAMES]

    output = {
        "updatedAt": time.strftime(
            "%Y-%m-%dT%H:%M:%SZ",
            time.gmtime(),
        ),
        "count": len(games),
        "games": games,
    }

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            output,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print(
        f"Saved {len(games)} unique games "
        f"to {OUTPUT_FILE}"
    )


def main() -> None:
    print("================================")
    print(" Roblox Game Collector")
    print("================================")
    print()

    existing = load_existing_games()

    print(
        f"Existing games: {len(existing)}"
    )

    universe_ids = set(existing.keys())

    # Ищем игры по разным запросам.
    for index, keyword in enumerate(
        SEARCH_TERMS,
        start=1,
    ):
        if len(universe_ids) >= TARGET_GAMES:
            break

        print(
            f"[{index}/{len(SEARCH_TERMS)}] "
            f"Searching: {keyword}"
        )

        ids = search_games(keyword)

        before = len(universe_ids)

        for universe_id in ids:
            universe_ids.add(universe_id)

            if len(universe_ids) >= TARGET_GAMES:
                break

        added = len(universe_ids) - before

        print(
            f"  Found: {len(ids)} | "
            f"New: {added} | "
            f"Total: {len(universe_ids)}"
        )

        time.sleep(0.5)

    # Получаем детали новых игр.
    new_ids = [
        game_id
        for game_id in universe_ids
        if game_id not in existing
    ]

    print()
    print(
        f"Need details for {len(new_ids)} games."
    )

    for start in range(
        0,
        len(new_ids),
        50,
    ):
        batch = new_ids[start:start + 50]

        print(
            f"Details "
            f"{start + 1}-"
            f"{min(start + 50, len(new_ids))}"
        )

        details = get_game_details(batch)

        for raw_game in details:
            game = normalize_game(raw_game)

            if game:
                existing[
                    game["universeId"]
                ] = game

        # Сохраняем промежуточный результат.
        # Если GitHub Actions оборвётся, уже собранные игры
        # останутся в games.json.
        save_games(
            list(existing.values())
        )

    final_games = list(existing.values())

    # Убираем дубликаты ещё раз.
    unique: Dict[int, Dict[str, Any]] = {}

    for game in final_games:
        universe_id = game.get("universeId")

        if universe_id:
            unique[int(universe_id)] = game

    save_games(
        list(unique.values())
    )

    print()
    print("================================")
    print(
        f"Finished. Games: "
        f"{min(len(unique), TARGET_GAMES)}"
    )
    print("================================")


if __name__ == "__main__":
    main()
