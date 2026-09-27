"""
Downloads place names (settlements, rivers, peaks, lakes, forests, ...) of one country from
OpenStreetMap (Overpass API) as word lists: `./cartosynth.sh words AT austria`.
One category is queried at a time with pauses, so a full download takes ~10 minutes.
"""
import os
import time
from math import floor
from random import shuffle

import requests



def get_places_template_dict():
    """Template to be later filled with toponyms"""
    return {
        "cities": [],
        "rivers": [],
        "mountains": [],
        "lakes": [],
        "regions": [],
        "valleys": [],
        "forests": [],
        "islands": [],
        "glaciers": [],
        "other": []
    }



def get_query_template_dict(country_code):
    """Returns a dictionary of queries per category as a template"""
    return {
        "cities": f"""
            [out:json][timeout:120];
            area["ISO3166-1"={country_code}][admin_level=2];
            (
              node["place"~"city|town|village|hamlet|suburb|neighbourhood"](area);
              way["place"~"city|town|village|hamlet|suburb|neighbourhood"](area);
              relation["place"~"city|town|village|hamlet|suburb|neighbourhood"](area);
            );
            out tags;
        """,

        "rivers": f"""
            [out:json][timeout:120];
            area["ISO3166-1"={country_code}][admin_level=2];
            (
              way["waterway"~"river|stream|canal"]["name"](area);
              relation["waterway"~"river|stream|canal"]["name"](area);
            );
            out tags;
        """,

        "mountains": f"""
            [out:json][timeout:120];
            area["ISO3166-1"={country_code}][admin_level=2];
            (
              node["natural"="peak"]["name"](area);
              node["natural"="hill"]["name"](area);
            );
            out tags;
        """,

        "mountain_ranges": f"""
            [out:json][timeout:120];
            area["ISO3166-1"={country_code}][admin_level=2];
            (
              way["natural"="mountain_range"]["name"](area);
              relation["natural"="mountain_range"]["name"](area);
            );
            out tags;
        """,

        "lakes": f"""
            [out:json][timeout:120];
            area["ISO3166-1"={country_code}][admin_level=2];
            (
              way["natural"="water"]["name"](area);
              relation["natural"="water"]["name"](area);
              way["water"~"lake|reservoir"]["name"](area);
              relation["water"~"lake|reservoir"]["name"](area);
            );
            out tags;
        """,

        "regions": f"""
            [out:json][timeout:120];
            area["ISO3166-1"={country_code}][admin_level=2];
            (
              relation["boundary"="administrative"]["admin_level"~"4|6|8"]["name"](area);
            );
            out tags;
        """,

        "valleys": f"""
            [out:json][timeout:120];
            area["ISO3166-1"={country_code}][admin_level=2];
            (
              way["natural"="valley"]["name"](area);
              relation["natural"="valley"]["name"](area);
            );
            out tags;
        """,

        "forests": f"""
            [out:json][timeout:120];
            area["ISO3166-1"={country_code}][admin_level=2];
            (
              way["natural"="wood"]["name"](area);
              relation["natural"="wood"]["name"](area);
              way["landuse"="forest"]["name"](area);
              relation["landuse"="forest"]["name"](area);
            );
            out tags;
        """,

        "islands": f"""
            [out:json][timeout:120];
            area["ISO3166-1"={country_code}][admin_level=2];
            (
              node["place"="island"]["name"](area);
              way["place"="island"]["name"](area);
            );
            out tags;
        """,

        "glaciers": f"""
            [out:json][timeout:120];
            area["ISO3166-1"={country_code}][admin_level=2];
            (
              way["natural"="glacier"]["name"](area);
              relation["natural"="glacier"]["name"](area);
            );
            out tags;
        """
    }



def query_with_retry(query, max_retries=3):
    """Try to query with retries on failure"""

    overpass_url = "https://overpass-api.de/api/interpreter"

    for attempt in range(max_retries):
        try:
            print(f"  Attempt {attempt + 1}/{max_retries}...", end=" ")
            response = requests.post(overpass_url, data={"data": query}, timeout=180)

            if response.status_code == 200:
                print("Success!")
                return response.json()
            elif response.status_code == 504:
                print("Timeout (504)")
                if attempt < max_retries - 1:
                    wait_time = 10 * (attempt + 1)
                    print(f"  Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
            elif response.status_code == 429:
                print("Rate limited (429)")
                wait_time = 60 * (attempt + 1)
                print(f"  Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                print(f"Error: HTTP {response.status_code}")
                return None

        except requests.exceptions.Timeout:
            print("Request timeout")
            if attempt < max_retries - 1:
                wait_time = 10 * (attempt + 1)
                print(f"  Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
        
        except Exception as e:
            print(f"Error: {e}")
            return None

    print("  All retries failed")
    return None
    


def download_place_names(country_code):
    """
    Download all geographic names from OpenStreetMap using Overpass API using a given country shorthand.
    Queries each category separately to avoid timeouts.
    """

    places = get_places_template_dict()


    # Define queries for each category
    queries = get_query_template_dict(country_code)

    # Query each category
    for category, query in queries.items():
        print(f"\nQuerying {category}... ")

        data = query_with_retry(query)

        if data:
            # Extract names
            names = []
            for element in data.get("elements", []):
                if "tags" in element and "name" in element["tags"]:
                    name = element["tags"]["name"]
                    names.append(name)

            # Remove duplicates and sort
            names = sorted(list(set(names)))
            names = [elem.replace('"', '').replace("'", "") for elem in names]

            # Merge mountain_ranges into mountains
            if category == "mountain_ranges":
                places["mountains"].extend(names)
                places["mountains"] = sorted(list(set(places["mountains"])))
            else:
                places[category] = names

            print(f"found {len(names)} unique names")
            
            print("Sleep for 30 seconds to avoid Rate Limiting...")
            time.sleep(30)
        else:
            print(f"skipping {category} due to errors")

    return places



def create_full_training_file(places, save_file):
    """All names, deduplicated and shuffled."""
    all_names = sorted({name for names in places.values() for name in names})
    shuffle(all_names)
    with open(save_file, "w", encoding="utf-8") as f:
        f.write("\n".join(all_names) + "\n")
    print(f"Full word list ({len(all_names)} names): {save_file}")


def create_small_training_file(places, save_file, per_category=500):
    """At most ~per_category names per category, so large categories (villages) do not dominate."""
    all_names = []
    for names in places.values():
        step = floor(len(names) / per_category) if len(names) > per_category else 1
        all_names.extend(names[::step])
    shuffle(all_names)
    with open(save_file, "w", encoding="utf-8") as f:
        f.write("\n".join(all_names) + "\n")
    print(f"Small word list ({len(all_names)} names): {save_file}")


def download_word_lists(country_code, out_dir, name):
    places = download_place_names(country_code)
    if not any(places.values()):
        raise RuntimeError("No names downloaded (Overpass API unreachable or rate limited?)")
    os.makedirs(out_dir, exist_ok=True)
    create_full_training_file(places, os.path.join(out_dir, f"{name}_full.txt"))
    create_small_training_file(places, os.path.join(out_dir, f"{name}_small.txt"))
