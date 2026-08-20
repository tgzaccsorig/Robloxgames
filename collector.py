import json
import os
import time
import urllib.request
import urllib.error

# ============================================================
# Hide Game Find RBX
# Collector
# ============================================================

OUTPUT_FILE = "games.json"

# Сколько игр собирать
LIMIT = 3500

# Пауза между запросами
REQUEST_DELAY = 0.15

ROBLOX_GAMES_URL = (
    "https://games.roblox.com/v1/games/list"
    "?sortToken={token}"
    "&limit=100"
)

ROBLOX_SORT_URL = (
    "https://games.roblox.com/v1/games/list"
    "?sortOrder=Desc"
    "&sortType=Playing"
    "&limit=100"
)


# ============================================================
# HTTP
# ============================================================

def request_json(url):
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "HideGameFindRBX/1.0"
            }
        )

        with urllib.request.urlopen(req, timeout=20) as response:
            data = response.read()

        return json.loads(data.decode("utf-8"))

    except urllib.error.HTTPError as error:
        print("HTTP ошибка:", error.code)
        return None

    except urllib.error.URLError as error:
        print("Ошибка соединения:", error.reason)
        return None

    except Exception as error:
        print("Ошибка запроса:", error)
        return None


# ============================================================
# СОХРАНЕНИЕ
# ============================================================

def load_old_games():
    if not os.path.exists(OUTPUT_FILE):
        return {}

    try:
        with open(
            OUTPUT_FILE,
            "r",
            encoding="utf-8"
        ) as file:
            data = json.load(file)

        if isinstance(data, list):
            return {
                str(game.get("universeId")): game
                for game in data
                if game.get("universeId")
            }

        if isinstance(data, dict):
            return data

    except Exception as error:
        print("Не удалось прочитать старый games.json:")
        print(error)

    return {}


def save_games(games):
    temporary_file = OUTPUT_FILE + ".tmp"

    with open(
        temporary_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            list(games.values()),
            file,
            ensure_ascii=False,
            indent=2
        )

    # Безопасная замена файла
    os.replace(
        temporary_file,
        OUTPUT_FILE
    )


# ============================================================
# ЖАНР
# ============================================================

def get_genre(game):
    genre = game.get("genre")

    if genre:
        return genre

    return "Unknown"


# ============================================================
# ОБРАБОТКА ИГРЫ
# ============================================================

def normalize_game(game):

    universe_id = game.get("universeId")

    if not universe_id:
        return None

    result = {
        "universeId": universe_id,

        "placeId": game.get(
            "rootPlaceId"
        ),

        "name": game.get(
            "name",
            "Unknown"
        ),

        "description": game.get(
            "description",
            ""
        ),

        "genre": get_genre(game),

        "playing": game.get(
            "playing",
            0
        ),

        "visits": game.get(
            "visits",
            0
        ),

        "favoritedCount": game.get(
            "favoritedCount",
            0
        ),

        "created": game.get(
            "created"
        ),

        "updated": game.get(
            "updated"
        ),

        # Пока Roblox не отдаёт нам
        # надёжную возрастную категорию
        # через этот сборщик.
        "ageRecommendation": game.get(
            "ageRecommendation",
            "unknown"
        )
    }

    return result


# ============================================================
# ПОЛУЧЕНИЕ ИГР
# ============================================================

def collect_games():

    games = load_old_games()

    print()
    print("======================================")
    print(" Hide Game Find RBX - Collector")
    print("======================================")
    print()

    print(
        "Уже сохранено:",
        len(games)
    )

    print()

    cursor = None
    collected = 0

    while collected < LIMIT:

        if cursor:
            url = (
                "https://games.roblox.com/v1/games/list"
                "?sortOrder=Desc"
                "&sortType=Playing"
                "&limit=100"
                "&cursor=" + cursor
            )
        else:
            url = ROBLOX_SORT_URL

        print(
            "Получение страницы...",
            collected,
            "/",
            LIMIT
        )

        data = request_json(url)

        if not data:
            print(
                "Не удалось получить данные."
            )
            break

        page_games = data.get(
            "games",
            []
        )

        if not page_games:
            print(
                "Roblox не вернул игры."
            )
            break

        for raw_game in page_games:

            game = normalize_game(
                raw_game
            )

            if not game:
                continue

            key = str(
                game["universeId"]
            )

            games[key] = game

            collected += 1

            print(
                f"[{collected}/{LIMIT}] "
                f"{game['name']}"
            )

            if collected >= LIMIT:
                break

        cursor = data.get(
            "nextPageCursor"
        )

        if not cursor:
            print(
                "Следующей страницы нет."
            )
            break

        time.sleep(
            REQUEST_DELAY
        )

    return games


# ============================================================
# MAIN
# ============================================================

def main():

    try:

        games = collect_games()

        print()
        print(
            "Сохранение games.json..."
        )

        save_games(games)

        print()
        print("======================================")
        print(" ГОТОВО!")
        print("======================================")
        print(
            "Всего игр:",
            len(games)
        )
        print(
            "Файл:",
            os.path.abspath(OUTPUT_FILE)
        )
        print()

    except KeyboardInterrupt:

        print()
        print(
            "Сбор остановлен пользователем."
        )

    except MemoryError:

        print()
        print(
            "Python действительно закончил"
            " доступную оперативную память."
        )
        print(
            "Это не связано с 159 ГБ свободного"
            " места на диске."
        )

    except OSError as error:

        print()
        print(
            "Ошибка файловой системы:"
        )
        print(error)

    except Exception as error:

        print()
        print(
            "Неожиданная ошибка:"
        )
        print(error)


if __name__ == "__main__":
    main()
