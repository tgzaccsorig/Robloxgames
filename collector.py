import json
import os
import time
import random
import requests

OUTPUT = "games.json"
TARGET = 10000

TIMEOUT = 12
RETRIES = 2
DELAY = 0.25

SEARCH_URL = "https://apis.roblox.com/search-api/omni-search"
DETAIL_URL = "https://games.roblox.com/v1/games"
THUMB_URL = (
    "https://thumbnails.roblox.com/v1/games/icons"
    "?universeIds={}"
    "&returnPolicy=PlaceHolder"
    "&size=512x512"
    "&format=Png"
    "&isCircular=false"
)

SEARCHES = [
    "obby",
    "simulator",
    "roleplay",
    "horror",
    "survival",
    "adventure",
    "pvp",
    "rpg",
    "racing",
    "tycoon",
    "anime",
    "story",
    "parkour",
    "murder",
    "zombie",
    "fighting",
    "tower",
    "escape",
    "backrooms",
    "fishing",
    "farming",
    "cars",
    "driving",
    "city",
    "school",
    "space",
    "pirates",
    "pets",
    "sports",
    "football",
    "basketball",
    "boxing",
    "strategy",
    "building",
    "sandbox",
    "quest",
    "dungeon",
    "monster",
    "ninja",
    "samurai",
    "superhero",
    "prison",
    "police",
    "military",
    "fps",
    "shooter",
    "bedwars",
    "battlegrounds",
    "tower defense",
    "clicker",
    "idle",
    "restaurant",
    "hotel",
    "fashion",
    "music",
    "puzzle",
    "minigame",
    "challenge",
    "speedrun",
    "open world",
    "island",
    "ocean",
    "dragon",
]

session = requests.Session()

session.headers.update({
    "User-Agent": "RobloxHiddenGems/5.0",
    "Accept": "application/json",
})


def request_json(url, params=None):
    for attempt in range(RETRIES + 1):
        try:
            r = session.get(
                url,
                params=params,
                timeout=TIMEOUT
            )

            if r.status_code == 200:
                return r.json()

            if r.status_code == 429:
                wait = 2 + attempt * 2
                print(
                    f"Rate limit. Waiting {wait}s...",
                    flush=True
                )
                time.sleep(wait)
                continue

            if r.status_code >= 500:
                time.sleep(2)
                continue

            print(
                f"HTTP {r.status_code}",
                flush=True
            )
            return None

        except requests.RequestException as e:
            print(
                f"Request error: {e}",
                flush=True
            )
            time.sleep(1)

    return None


def load_games():
    if not os.path.exists(OUTPUT):
        return {}

    try:
        with open(
            OUTPUT,
            "r",
            encoding="utf-8"
        ) as f:
            data = json.load(f)

        result = {}

        for game in data.get("games", []):
            uid = game.get("universeId")

            if uid:
                result[str(uid)] = game

        return result

    except Exception as e:
        print(
            f"Could not load games.json: {e}",
            flush=True
        )
        return {}


def save_games(games):
    values = list(games.values())

    values.sort(
        key=lambda x: int(
            x.get("playing") or 0
        ),
        reverse=True
    )

    values = values[:TARGET]

    data = {
        "updatedAt": time.strftime(
            "%Y-%m-%dT%H:%M:%SZ",
            time.gmtime()
        ),
        "count": len(values),
        "games": values
    }

    with open(
        OUTPUT,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )

    print(
        f"Saved {len(values)} games",
        flush=True
    )


def find_ids(query, known):
    found = set()

    session_id = (
        str(random.randint(100000, 999999))
        + "-"
        + str(int(time.time()))
    )

    params = {
        "searchQuery": query,
        "sessionId": session_id,
        "pageType": "all"
    }

    data = request_json(
        SEARCH_URL,
        params
    )

    if not data:
        return found

    def scan(value):
        if isinstance(value, dict):

            for key in (
                "universeId",
                "universeID",
                "universe_id"
            ):
                value_id = value.get(key)

                if value_id:
                    try:
                        uid = int(value_id)

                        if uid not in known:
                            found.add(uid)

                    except Exception:
                        pass

            for child in value.values():
                scan(child)

        elif isinstance(value, list):
            for child in value:
                scan(child)

    scan(data)

    return found


def get_details(ids):
    if not ids:
        return []

    params = {
        "universeIds": ",".join(
            str(x) for x in ids
        )
    }

    data = request_json(
        DETAIL_URL,
        params
    )

    if not data:
        return []

    return data.get("data", [])


def make_game(raw):
    uid = raw.get("id")

    if not uid:
        return None

    uid = int(uid)

    place = raw.get("rootPlaceId")

    if place:
        place = int(place)

    creator = raw.get("creator")

    if not isinstance(creator, dict):
        creator = {}

    return {
        "universeId": uid,
        "placeId": place,
        "name": raw.get(
            "name",
            "Unknown game"
        ),
        "description": raw.get(
            "description",
            ""
        ),
        "playing": int(
            raw.get("playing") or 0
        ),
        "visits": int(
            raw.get("visits") or 0
        ),
        "favorites": int(
            raw.get("favoritedCount") or 0
        ),
        "maxPlayers": int(
            raw.get("maxPlayers") or 0
        ),
        "created": raw.get("created"),
        "updated": raw.get("updated"),
        "creator": creator,
        "genre": raw.get(
            "genre",
            "All"
        ),
        "thumbnail": THUMB_URL.format(uid),
        "url": (
            f"https://www.roblox.com/games/{place}"
            if place
            else f"https://www.roblox.com/games/{uid}"
        )
    }


def main():

    print(
        "================================",
        flush=True
    )
    print(
        " Roblox Hidden Gems Collector 5.0",
        flush=True
    )
    print(
        "================================",
        flush=True
    )

    games = load_games()

    print(
        f"Existing games: {len(games)}",
        flush=True
    )

    # ------------------------------------------------
    # SEARCH
    # ------------------------------------------------

    random.shuffle(SEARCHES)

    for index, query in enumerate(
        SEARCHES,
        1
    ):

        if len(games) >= TARGET:
            break

        print(
            f"[{index}/{len(SEARCHES)}] Searching: {query}",
            flush=True
        )

        ids = find_ids(
            query,
            {
                int(x)
                for x in games.keys()
            }
        )

        if not ids:
            print(
                "  No new games",
                flush=True
            )
            continue

        print(
            f"  Found {len(ids)} new IDs",
            flush=True
        )

        # Small batches = much less chance
        # of hitting Roblox limits.
        ids = list(ids)[:100]

        for start in range(
            0,
            len(ids),
            50
        ):

            batch = ids[
                start:start + 50
            ]

            details = get_details(
                batch
            )

            added = 0

            for raw in details:

                game = make_game(raw)

                if not game:
                    continue

                uid = str(
                    game["universeId"]
                )

                if uid not in games:
                    games[uid] = game
                    added += 1

            print(
                f"  Added {added}",
                flush=True
            )

            save_games(games)

            time.sleep(DELAY)

        time.sleep(DELAY)

    # ------------------------------------------------
    # REFRESH ONLY THE MOST ACTIVE 300
    # ------------------------------------------------

    print(
        "Refreshing live stats...",
        flush=True
    )

    active = sorted(
        games.values(),
        key=lambda x: int(
            x.get("playing") or 0
        ),
        reverse=True
    )

    refresh_ids = [
        int(x["universeId"])
        for x in active[:300]
        if x.get("universeId")
    ]

    for start in range(
        0,
        len(refresh_ids),
        50
    ):

        batch = refresh_ids[
            start:start + 50
        ]

        details = get_details(
            batch
        )

        for raw in details:

            game = make_game(raw)

            if not game:
                continue

            uid = str(
                game["universeId"]
            )

            if uid in games:
                old = games[uid]

                # Keep any old fields.
                old.update(game)

        save_games(games)

        time.sleep(DELAY)

    # ------------------------------------------------
    # FINAL CLEANUP
    # ------------------------------------------------

    clean = {}

    for game in games.values():

        uid = game.get(
            "universeId"
        )

        if not uid:
            continue

        uid = str(uid)

        game["thumbnail"] = THUMB_URL.format(
            int(uid)
        )

        clean[uid] = game

    save_games(clean)

    print(
        "================================",
        flush=True
    )

    print(
        f"FINAL: {len(clean)} unique games",
        flush=True
    )

    print(
        "Collector finished successfully!",
        flush=True
    )

    print(
        "================================",
        flush=True
    )


if __name__ == "__main__":
    main()
