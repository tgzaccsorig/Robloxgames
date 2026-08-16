```python
import json
import os
import re
import time
import uuid
from datetime import datetime, timezone
from urllib.parse import urlencode

import requests


SESSION_ID = str(uuid.uuid4())

OUTPUT = "games.json"

TARGET_GAMES = 10000

DISCOVER_URL = (
    "https://apis.roblox.com/explore-api/v1/get-sorts"
)

SORT_CONTENT_URL = (
    "https://apis.roblox.com/explore-api/v1/get-sort-content"
)

GAME_DETAILS_URL = (
    "https://games.roblox.com/v1/games"
)

THUMBNAIL_URL = (
    "https://thumbnails.roblox.com/v1/games/multiget/thumbnails"
)


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "Chrome/130 Safari/537.36"
    )
}


session = requests.Session()
session.headers.update(HEADERS)


def get_json(url, params=None):

    try:

        response = session.get(
            url,
            params=params,
            timeout=30
        )

        response.raise_for_status()

        return response.json()

    except Exception as exc:

        print(
            "REQUEST ERROR:",
            url,
            exc
        )

        return None


def recursive_find_ids(obj):

    """
    Roblox может менять форму Discover JSON.

    Поэтому вместо жёсткой привязки
    к одному полю мы рекурсивно ищем
    universeId / placeId.
    """

    found = []

    if isinstance(obj, dict):

        universe_id = (
            obj.get("universeId")
            or obj.get("universeID")
            or obj.get("UniverseId")
            or obj.get("UniverseID")
        )

        place_id = (
            obj.get("placeId")
            or obj.get("placeID")
            or obj.get("PlaceId")
            or obj.get("PlaceID")
        )

        if universe_id:

            try:

                found.append({
                    "universeId": int(universe_id),
                    "placeId": int(place_id or 0)
                })

            except Exception:
                pass


        for value in obj.values():

            found.extend(
                recursive_find_ids(value)
            )


    elif isinstance(obj, list):

        for value in obj:

            found.extend(
                recursive_find_ids(value)
            )


    return found


def discover_sorts():

    print("Получаем Roblox Discover sorts...")

    data = get_json(
        DISCOVER_URL,
        {
            "sessionId": SESSION_ID,
            "device": "computer",
            "country": "all"
        }
    )

    if not data:

        return []


    sorts = []


    def walk(obj):

        if isinstance(obj, dict):

            sort_id = (
                obj.get("sortId")
                or obj.get("id")
            )

            if sort_id is not None:

                text = str(sort_id)

                if text not in sorts:

                    sorts.append(text)


            for value in obj.values():
                walk(value)


        elif isinstance(obj, list):

            for value in obj:
                walk(value)


    walk(data)

    print(
        "Найдено Discover sorts:",
        len(sorts)
    )

    return sorts


def collect_from_sort(sort_id):

    data = get_json(
        SORT_CONTENT_URL,
        {
            "sessionId": SESSION_ID,
            "sortId": sort_id
        }
    )

    if not data:

        return []


    return recursive_find_ids(data)


def collect_universe_ids():

    sorts = discover_sorts()

    unique = {}

    for index, sort_id in enumerate(sorts):

        print(
            f"[{index + 1}/{len(sorts)}] "
            f"Собираем sort {sort_id}"
        )

        items = collect_from_sort(sort_id)

        for item in items:

            universe_id = item["universeId"]

            if universe_id not in unique:

                unique[universe_id] = {
                    "universeId": universe_id,
                    "placeId": item["placeId"]
                }

        print(
            "Уникальных игр:",
            len(unique)
        )

        if len(unique) >= TARGET_GAMES:

            break

        time.sleep(0.4)


    return list(unique.values())


def chunks(items, size):

    for i in range(0, len(items), size):

        yield items[i:i + size]


def get_game_details(ids):

    all_games = []

    for batch in chunks(ids, 50):

        params = {
            "universeIds": ",".join(
                str(x)
                for x in batch
            )
        }

        data = get_json(
            GAME_DETAILS_URL,
            params
        )

        if not data:
            continue

        rows = data.get(
            "data",
            []
        )

        all_games.extend(rows)

        print(
            "Получено данных:",
            len(all_games),
            "/",
            len(ids)
        )

        time.sleep(0.15)


    return all_games


def get_thumbnails(universe_ids):

    result = {}

    for batch in chunks(universe_ids, 50):

        params = {
            "universeIds": ",".join(
                str(x)
                for x in batch
            ),
            "countPerUniverse": 1,
            "defaults": "true",
            "size": "768x432",
            "format": "Png",
            "isCircular": "false"
        }

        data = get_json(
            THUMBNAIL_URL,
            params
        )

        if not data:
            continue

        for item in data.get("data", []):

            uid = item.get("universeId")

            if uid:

                result[int(uid)] = (
                    item.get("imageUrl")
                    or item.get("thumbnailUrl")
                    or ""
                )

        time.sleep(0.15)


    return result


def rating_percent(game):

    up = game.get("upVotes")

    down = game.get("downVotes")

    if up is None or down is None:

        return 0

    total = up + down

    if total <= 0:

        return 0

    return round(
        (up / total) * 100
    )


def clean_game(game, thumbnails):

    universe_id = game.get(
        "id"
    )

    place_id = game.get(
        "rootPlaceId"
    )


    if not universe_id or not place_id:

        return None


    description = (
        game.get("description")
        or ""
    )

    description = re.sub(
        r"\s+",
        " ",
        description
    ).strip()


    return {

        "universeId": int(universe_id),

        "placeId": int(place_id),

        "name": (
            game.get("name")
            or "Unknown Roblox Game"
        ),

        "description": description,

        "playing": int(
            game.get("playing")
            or 0
        ),

        "maxPlayers": int(
            game.get("maxPlayers")
            or 0
        ),

        "visits": int(
            game.get("visits")
            or 0
        ),

        "rating": rating_percent(
            game
        ),

        "created": (
            game.get("created")
            or ""
        ),

        "updated": (
            game.get("updated")
            or ""
        ),

        "thumbnail": thumbnails.get(
            int(universe_id),
            ""
        ),

        "tags": []

    }


def main():

    print("")
    print("===================================")
    print(" ROBLOX HIDDEN GEMS COLLECTOR")
    print("===================================")
    print("")


    identifiers = collect_universe_ids()

    print(
        "Всего найдено уникальных universe:",
        len(identifiers)
    )


    if not identifiers:

        print(
            "Не удалось получить игры."
        )

        return


    identifiers = identifiers[
        :TARGET_GAMES
    ]


    ids = [
        item["universeId"]
        for item in identifiers
    ]


    details = get_game_details(ids)

    print(
        "Деталей игр получено:",
        len(details)
    )


    thumbnail_map = get_thumbnails(ids)


    final_games = []

    seen = set()


    for game in details:

        cleaned = clean_game(
            game,
            thumbnail_map
        )

        if not cleaned:
            continue


        uid = cleaned["universeId"]


        if uid in seen:
            continue


        seen.add(uid)

        final_games.append(
            cleaned
        )


    final_games.sort(
        key=lambda x: (
            x.get("playing", 0)
        ),
        reverse=True
    )


    output = {

        "version": 1,

        "updatedAt":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "count":
            len(final_games),

        "games":
            final_games

    }


    with open(
        OUTPUT,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            output,
            file,
            ensure_ascii=False,
            separators=(",", ":")
        )


    print("")
    print("===================================")
    print(
        "ГОТОВО:",
        len(final_games),
        "уникальных игр"
    )
    print("===================================")


if __name__ == "__main__":
    main()
```
