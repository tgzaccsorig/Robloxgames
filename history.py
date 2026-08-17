import json
import os
from datetime import datetime, timezone, timedelta

GAMES_FILE = "games.json"
HISTORY_DIR = "history"

os.makedirs(HISTORY_DIR, exist_ok=True)


def load_games():
    with open(GAMES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data.get("games", [])


def load_history(universe_id):
    path = os.path.join(
        HISTORY_DIR,
        f"{universe_id}.json"
    )

    if not os.path.exists(path):
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_history(universe_id, history):
    path = os.path.join(
        HISTORY_DIR,
        f"{universe_id}.json"
    )

    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            history,
            f,
            ensure_ascii=False,
            indent=2
        )


def main():

    games = load_games()

    now = datetime.now(
        timezone.utc
    )

    cutoff = now - timedelta(
        hours=24
    )

    saved = 0

    for game in games:

        universe_id = game.get(
            "universeId"
        )

        if not universe_id:
            continue

        playing = int(
            game.get(
                "playing",
                0
            ) or 0
        )

        history = load_history(
            universe_id
        )

        history.append({
            "time": now.isoformat(),
            "playing": playing
        })

        cleaned = []

        for point in history:

            try:
                point_time = datetime.fromisoformat(
                    point["time"]
                )

                if point_time >= cutoff:
                    cleaned.append(point)

            except Exception:
                pass

        # Не записываем несколько одинаковых
        # точек подряд с одинаковым временем.
        if len(cleaned) > 500:
            cleaned = cleaned[-500:]

        save_history(
            universe_id,
            cleaned
        )

        saved += 1

    print(
        f"Saved history for {saved} games"
    )


if __name__ == "__main__":
    main()
