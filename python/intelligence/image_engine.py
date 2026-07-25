#!/usr/bin/env python3

from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
DATABASE = ROOT / "coupons.json"


class ImageEngine:

    def __init__(self):
        self.products = []

    def load_database(self):

        print("Loading database...")

        if not DATABASE.exists():
            print("ERROR : coupons.json not found")
            return

        with DATABASE.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if isinstance(data, list):
            self.products = data
        elif isinstance(data, dict):
            self.products = (
                data.get("products")
                or data.get("coupons")
                or data.get("items")
                or []
            )

        print(f"Products Loaded : {len(self.products)}")

    def analyze_images(self):

        print("\nChecking Images...\n")

        available = 0
        missing = 0

        for product in self.products:

            image = product.get("image")

            if image:
                available += 1
            else:
                missing += 1

        print(f"Images Available : {available}")
        print(f"Images Missing   : {missing}")


def main():

    engine = ImageEngine()

    engine.load_database()
    engine.analyze_images()


if __name__ == "__main__":
    main()