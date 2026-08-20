import json
import os
import time
import random
import urllib.parse
import urllib.request
import urllib.error

OUTPUT = "games.json"
STATE_FILE = "collector_state.json"

TARGET_GAMES = 10000

REQUEST_TIMEOUT = 15
MAX_RETRIES = 2
SAVE_EVERY = 25

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
    "war",
    "battle",
    "magic",
    "fantasy",
    "horror story",
    "survival horror",
    "roleplay city",
    "roleplay school",
    "car",
    "motorcycle",
    "train",
    "airport",
    "boat",
    "helicopter",
    "simulator games",
    "fun",
    "popular",
    "new",
    "hidden gems"
]


def get_json(url, params=None):
    """
    Выполняет GET-запрос без requests.
    Используется стандартный urllib из Python.
    """

    if params:
        query = urllib.parse.urlencode(params)
        separator = "&" if "?" in url else "?"
        url = url + separator + query

    headers = {
        "User-Agent": "Mozilla/5.0 RobloxHiddenGemsCollector/6.0",
        "Accept": "application/json",
    }

    request = urllib.request.Request(
        url,
        headers=headers,
        method="GET"
    )

    for attempt in range(MAX_RETRIES + 1):

        try:

            with urllib.request.urlopen(
                request,
                timeout=REQUEST_TIMEOUT
            ) as response:

                status = response.status

                if status != 200:
                    print(
                        f"HTTP {status}",
                        flush=True
                    )

                    if attempt < MAX_RETRIES:
                        time.sleep(2)
                        continue

                    return None

                raw = response.read()

                return json.loads(
                    raw.decode("utf-8")
                )

        except urllib.error.HTTPError as error:

            print(
                f"HTTP Error {error.code}",
                flush=True
            )

            if error.code == 429:

                wait = 3 + attempt * 3

                print(
                    f"Rate limit. Waiting {wait}s...",
                    flush=True
                )

                time.sleep(wait)

                continue

            if error.code >= 500:

                time.sleep(2)

                continue

            return None

        except urllib.error.URLError as error:

            print(
                f"Network error: {error}",
                flush=True
            )

            if attempt < MAX_RETRIES:
                time.sleep(2)
                continue

            return None

        except TimeoutError:

            print(
                "Request timeout",
                flush=True
            )

            if attempt < MAX_RETRIES:
                time.sleep(2)
                continue

            return None

        except Exception as error:

            print(
                f"Request failed: {error}",
                flush=True
            )

            if attempt < MAX_RETRIES:
                time.sleep(2)
                continue

            return None

    return None


def load_games():

    if not os.path.exists(OUTPUT):
        return {}

    try:

        with open(
            OUTPUT,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        result = {}

        for game in data.get(
            "games",
            []
        ):

            universe_id = game.get(
                "universeId"
            )

            if universe_id:

                result[
                    str(universe_id)
                ] = game

        return result

    except Exception as error:

        print(
            f"Could not read games.json: {error}",
            flush=True
        )

        return {}


def save_games(games):

    values = list(
        games.values()
    )

    values.sort(
        key=lambda game:
        int(
            game.get(
                "playing",
                0
            ) or 0
        ),
        reverse=True
    )

    values = values[
        :TARGET_GAMES
    ]

    data = {
        "updatedAt":
            time.strftime(
                "%Y-%m-%dT%H:%M:%SZ",
                time.gmtime()
            ),

        "count":
            len(values),

        "games":
            values
    }

    temporary = OUTPUT + ".tmp"

    with open(
        temporary,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2
        )

    os.replace(
        temporary,
        OUTPUT
    )

    print(
        f"Saved {len(values)} games",
        flush=True
    )


def extract_universe_ids(data):

    result = set()

    def scan(value):

        if isinstance(
            value,
            dict
        ):

            for key in (
                "universeId",
                "universeID",
                "universe_id"
            ):

                possible = value.get(
                    key
                )

                if possible:

                    try:

                        result.add(
                            int(possible)
                        )

                    except Exception:
                        pass

            for child in value.values():

                scan(child)

        elif isinstance(
            value,
            list
        ):

            for child in value:
                scan(child)

    scan(data)

    return result


def load_state():

    if not os.path.exists(STATE_FILE):
        return {"pageTokens": {}, "queryIndex": 0}

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
        if not isinstance(data, dict):
            return {"pageTokens": {}, "queryIndex": 0}
        data.setdefault("pageTokens", {})
        data.setdefault("queryIndex", 0)
        return data
    except Exception:
        return {"pageTokens": {}, "queryIndex": 0}


def save_state(state):

    temporary = STATE_FILE + ".tmp"

    with open(temporary, "w", encoding="utf-8") as file:
        json.dump(state, file, ensure_ascii=False, indent=2)

    os.replace(temporary, STATE_FILE)


def search_games(
    query,
    known_ids,
    page_token=None
):

    # Roblox's current search endpoint is undocumented and paginated.
    # The old collector only read the first page, so after ~3500 games
    # most queries contained only games we already had.
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

    if page_token:
        params["pageToken"] = page_token

    data = get_json(SEARCH_URL, params)

    if not data:
        return set(), None

    ids = extract_universe_ids(data)

    # Explicitly inspect the current searchResults structure too.
    for result in data.get("searchResults", []):
        if not isinstance(result, dict):
            continue
        for content in result.get("contents", []):
            if not isinstance(content, dict):
                continue
            for key in ("universeId", "universeID", "universe_id"):
                value = content.get(key)
                if value:
                    try:
                        ids.add(int(value))
                    except (TypeError, ValueError):
                        pass

    next_token = data.get("nextPageToken")

    return (
        {uid for uid in ids if uid not in known_ids},
        next_token
    )


def get_game_details(
    universe_ids
):

    if not universe_ids:
        return []

    universe_ids = [
        int(x)
        for x in universe_ids
    ]

    params = {
        "universeIds":
            ",".join(
                str(x)
                for x in universe_ids
            )
    }

    data = get_json(
        DETAIL_URL,
        params
    )

    if not data:
        return []

    return data.get(
        "data",
        []
    )


def make_game(raw):

    universe_id = raw.get(
        "id"
    )

    if not universe_id:
        return None

    place_id = raw.get(
        "rootPlaceId"
    )

    creator = raw.get(
        "creator"
    )

    if not isinstance(
        creator,
        dict
    ):
        creator = {}

    try:
        playing = int(
            raw.get(
                "playing",
                0
            ) or 0
        )
    except Exception:
        playing = 0

    try:
        visits = int(
            raw.get(
                "visits",
                0
            ) or 0
        )
    except Exception:
        visits = 0

    try:
        favorites = int(
            raw.get(
                "favoritedCount",
                0
            ) or 0
        )
    except Exception:
        favorites = 0

    try:
        max_players = int(
            raw.get(
                "maxPlayers",
                0
            ) or 0
        )
    except Exception:
        max_players = 0

    universe_id = int(
        universe_id
    )

    if place_id:
        try:
            place_id = int(
                place_id
            )
        except Exception:
            place_id = None

    if place_id:

        game_url = (
            "https://www.roblox.com/games/"
            + str(place_id)
        )

    else:

        game_url = (
            "https://www.roblox.com/games/"
            + str(universe_id)
        )

    return {

        "universeId":
            universe_id,

        "placeId":
            place_id,

        "name":
            raw.get(
                "name",
                "Unknown game"
            ),

        "description":
            raw.get(
                "description",
                ""
            ),

        "playing":
            playing,

        "visits":
            visits,

        "favorites":
            favorites,

        "maxPlayers":
            max_players,

        "created":
            raw.get(
                "created"
            ),

        "updated":
            raw.get(
                "updated"
            ),

        "creator":
            creator,

        "genre":
            raw.get(
                "genre",
                "All"
            ),

        "isAllGenre":
            bool(raw.get("isAllGenre", False)),

        "thumbnail":
            THUMB_URL.format(
                universe_id
            ),

        "url":
            game_url
    }


def main():

    print(
        "======================================",
        flush=True
    )

    print(
        " Roblox Hidden Gems Collector 6.0",
        flush=True
    )

    print(
        " No requests dependency",
        flush=True
    )

    print(
        "======================================",
        flush=True
    )

    games = load_games()

    print(
        f"Existing games: {len(games)}",
        flush=True
    )

    if len(games) >= TARGET_GAMES:

        print(
            "Target already reached.",
            flush=True
        )

    state = load_state()
    page_tokens = state.get("pageTokens", {})
    query_index = int(state.get("queryIndex", 0) or 0) % len(SEARCHES)

    # Process a rotating subset on every run. This prevents one run from
    # hammering Roblox and, more importantly, lets us walk through pages
    # instead of repeatedly collecting the same first 40 results.
    run_queries = 40
    queries = [
        SEARCHES[(query_index + i) % len(SEARCHES)]
        for i in range(min(run_queries, len(SEARCHES)))
    ]

    total_added = 0

    for index, query in enumerate(queries, 1):

        if len(games) >= TARGET_GAMES:
            break

        print("", flush=True)
        print(
            f"[{index}/{len(queries)}] Searching: {query}",
            flush=True
        )

        known_ids = {
            int(x)
            for x in games.keys()
            if str(x).isdigit()
        }

        page_token = page_tokens.get(query) or None

        new_ids, next_token = search_games(
            query,
            known_ids,
            page_token
        )

        print(
            f"Found {len(new_ids)} new IDs",
            flush=True
        )

        # Save the cursor even when this page has no new games.
        # When Roblox reaches the end, restart this query from page 1
        # on a future rotation so newly-created games can be discovered.
        if next_token:
            page_tokens[query] = next_token
        else:
            page_tokens.pop(query, None)

        state["pageTokens"] = page_tokens
        state["queryIndex"] = (query_index + index) % len(SEARCHES)
        save_state(state)

        if not new_ids:
            time.sleep(0.7)
            continue

        new_ids = list(new_ids)[:100]

        for batch_start in range(0, len(new_ids), 50):

            batch = new_ids[batch_start:batch_start + 50]
            details = get_game_details(batch)
            added_now = 0

            for raw in details:
                game = make_game(raw)
                if not game:
                    continue

                uid = str(game["universeId"])
                if uid not in games:
                    games[uid] = game
                    added_now += 1
                    total_added += 1

            print(f"Added this batch: {added_now}", flush=True)
            print(f"Total catalog: {len(games)}", flush=True)

            save_games(games)
            time.sleep(0.5)

        time.sleep(0.8)

    state["pageTokens"] = page_tokens
    state["queryIndex"] = (query_index + len(queries)) % len(SEARCHES)
    save_state(state)

    print(
        "Refreshing active games...",
        flush=True
    )

    active_games = sorted(
        games.values(),
        key=lambda game:
        int(
            game.get(
                "playing",
                0
            ) or 0
        ),
        reverse=True
    )

    refresh_ids = []

    for game in active_games[
        :300
    ]:

        uid = game.get(
            "universeId"
        )

        if uid:
            refresh_ids.append(
                int(uid)
            )

    for start in range(
        0,
        len(refresh_ids),
        50
    ):

        batch = refresh_ids[
            start:start + 50
        ]

        details = get_game_details(
            batch
        )

        for raw in details:

            updated_game = make_game(
                raw
            )

            if not updated_game:
                continue

            uid = str(
                updated_game[
                    "universeId"
                ]
            )

            if uid in games:

                games[
                    uid
                ].update(
                    updated_game
                )

        save_games(
            games
        )

        time.sleep(
            0.4
        )

    print(
        "",
        flush=True
    )

    print(
        "Cleaning duplicates...",
        flush=True
    )

    clean = {}

    for game in games.values():

        uid = game.get(
            "universeId"
        )

        if not uid:
            continue

        uid = str(
            uid
        )

        game[
            "thumbnail"
        ] = THUMB_URL.format(
            int(uid)
        )

        clean[
            uid
        ] = game

    save_games(
        clean
    )

    print(
        "",
        flush=True
    )

    print(
        "======================================",
        flush=True
    )

    print(
        f"FINAL GAMES: {len(clean)}",
        flush=True
    )

    print(
        f"ADDED THIS RUN: {total_added}",
        flush=True
    )

    print(
        "Collector finished successfully!",
        flush=True
    )

    print(
        "======================================",
        flush=True
    )


if __name__ == "__main__":
    main()
