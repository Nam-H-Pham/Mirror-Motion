import requests
import time
import os

BASE_URL = "http://127.0.0.1:8000"
INTERVAL = 0.1  # seconds between polls

endpoints = {
    "lap_count": "/lap_count",
    "current_lap_progress": "/current_lap_progress",
    "hallway_progress": "/hallway_progress",
    "lap_state": "/lap_state",
}


def clear_console():
    os.system("cls" if os.name == "nt" else "clear")


def get_all():
    results = {}

    for name, path in endpoints.items():
        try:
            r = requests.get(BASE_URL + path, timeout=3)
            r.raise_for_status()
            results[name] = r.json()
        except Exception as e:
            results[name] = {"error": str(e)}

    return results


if __name__ == "__main__":
    while True:
        data = get_all()

        clear_console()
        print("Lap Tracker Live Data\n" + "-" * 25)

        for key, value in data.items():
            print(f"{key}: {value}")

        time.sleep(INTERVAL)
