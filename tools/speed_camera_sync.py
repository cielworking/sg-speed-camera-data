"""Fetch the SPF speed-camera page and write the app's JSON feed."""

import json
import re
from datetime import date
from pathlib import Path

import requests
from bs4 import BeautifulSoup

SOURCE = "https://www.police.gov.sg/Knowledge-Hub/Traffic/Traffic-Matters/Speed-Enforcement-Camera-Locations"
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DATA_DIRECTORY = (
    REPOSITORY_ROOT / "data"
    if (REPOSITORY_ROOT / "data").exists()
    else REPOSITORY_ROOT / "assets" / "data"
)
OUTPUT = DATA_DIRECTORY / "speed_cameras.json"
COORDINATE = re.compile(r"(-?\d{1,3}\.\d+)\s*,\s*(-?\d{1,3}\.\d+)")


def main() -> None:
    response = requests.get(SOURCE, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    cameras = []
    seen = set()
    category = "Speed enforcement camera"

    for element in soup.find_all(["h2", "h3", "h4", "tr"]):
        if element.name != "tr":
            heading = element.get_text(" ", strip=True).lower()
            if "fixed speed" in heading:
                category = "Fixed speed camera"
            elif "mobile speed" in heading:
                category = "Mobile speed camera"
            elif "average speed" in heading:
                category = "Average speed camera"
            elif "laser camera" in heading:
                category = "Police speed laser camera"
            continue

        row = element.get_text(" ", strip=True)
        coordinates = COORDINATE.findall(row)
        if not coordinates:
            continue
        location = COORDINATE.sub("", row).strip(" |-")
        for index, (latitude, longitude) in enumerate(coordinates, start=1):
            key = (category, location, latitude, longitude)
            if key in seen:
                continue
            seen.add(key)
            cameras.append(
                {
                    "id": f"{category.lower().replace(' ', '-')}-{len(cameras) + 1}",
                    "category": category,
                    "location": location or "Published camera location",
                    "latitude": float(latitude),
                    "longitude": float(longitude),
                    "source": SOURCE,
                    "source_updated_at": date.today().isoformat(),
                }
            )

    if not cameras:
        raise RuntimeError("No camera coordinates were found; refusing to overwrite feed")

    OUTPUT.write_text(
        json.dumps(
            {
                "source": SOURCE,
                "source_updated_at": date.today().isoformat(),
                "cameras": cameras,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(cameras)} camera coordinates to {OUTPUT}")


if __name__ == "__main__":
    main()
