"""
Synthetic ANPR event simulator.

Generates fake (non-real) vehicle sightings and POSTs them to a running
HoloLink API instance, for demoing search/history/parking flows without
any real camera hardware or production plate data.

Usage:
    python simulator/anpr_simulator.py --count 20
    python simulator/anpr_simulator.py --count 50 --url http://127.0.0.1:8000 --plates 8
"""
import argparse
import random
import string
import sys
import time

import httpx

COUNTRIES = ["UAE", "SAU", "OMN", "QAT"]
CATEGORIES = ["Private", "Commercial", "Taxi", "Government"]
VEHICLE_TYPES = ["Sedan", "SUV", "Pickup", "Van", "Hatchback"]
MAKES_MODELS = [
    ("Toyota", "Land Cruiser"),
    ("Toyota", "Camry"),
    ("Nissan", "Patrol"),
    ("Honda", "Civic"),
    ("Ford", "F-150"),
    ("Chevrolet", "Tahoe"),
    ("Hyundai", "Elantra"),
    ("Kia", "Sportage"),
]
COLORS = ["White", "Black", "Silver", "Grey", "Blue", "Red"]
CAMERAS = [f"CAM-{i:03d}" for i in range(1, 6)]
SITES = [f"SITE-{i:03d}" for i in range(1, 4)]
DIRECTIONS = ["ENTRY", "EXIT", "PASSING"]


def random_plate() -> str:
    letters = "".join(random.choices(string.ascii_uppercase, k=1))
    digits = "".join(random.choices(string.digits, k=5))
    return f"{letters}{digits}"


def build_event(plate_pool: list[str]) -> dict:
    make, model = random.choice(MAKES_MODELS)
    return {
        "plate": random.choice(plate_pool),
        "country": random.choice(COUNTRIES),
        "category": random.choice(CATEGORIES),
        "vehicle_type": random.choice(VEHICLE_TYPES),
        "make": make,
        "model": model,
        "color": random.choice(COLORS),
        "camera_id": random.choice(CAMERAS),
        "site_id": random.choice(SITES),
        "direction": random.choice(DIRECTIONS),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate synthetic ANPR events for HoloLink.")
    parser.add_argument("--count", type=int, default=20, help="Number of events to send.")
    parser.add_argument("--url", default="http://127.0.0.1:8000", help="Base URL of the HoloLink API.")
    parser.add_argument("--plates", type=int, default=10, help="Number of distinct synthetic plates to cycle through.")
    parser.add_argument("--delay", type=float, default=0.0, help="Seconds to sleep between events.")
    args = parser.parse_args()

    plate_pool = [random_plate() for _ in range(args.plates)]
    endpoint = f"{args.url.rstrip('/')}/api/v1/anpr/events"

    sent, failed = 0, 0
    with httpx.Client(timeout=5.0) as client:
        for i in range(args.count):
            event = build_event(plate_pool)
            try:
                resp = client.post(endpoint, json=event)
                resp.raise_for_status()
                sent += 1
                print(f"[{i + 1}/{args.count}] OK  plate={event['plate']} direction={event['direction']}")
            except httpx.HTTPError as exc:
                failed += 1
                print(f"[{i + 1}/{args.count}] FAIL plate={event['plate']} error={exc}", file=sys.stderr)

            if args.delay:
                time.sleep(args.delay)

    print(f"\nDone. sent={sent} failed={failed} target={endpoint}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
