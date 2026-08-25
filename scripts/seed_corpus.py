"""
Download sample animal images using direct Wikimedia Commons URLs.
No API key required. Images are public domain / CC licensed.

Usage:
    python scripts/seed_corpus.py
"""
import os
import time

import requests

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "corpus")

# Direct image URLs from Wikimedia Commons (public domain / CC0 / CC-BY)
IMAGES = {
    "fox1.jpg":  "https://upload.wikimedia.org/wikipedia/commons/thumb/0/03/Red_Fox_%28Vulpes_vulpes%29_-_British_Wildlife_Centre-8.jpg/320px-Red_Fox_%28Vulpes_vulpes%29_-_British_Wildlife_Centre-8.jpg",
    "fox2.jpg":  "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a9/A_Fox_In_Yellowstone.jpg/320px-A_Fox_In_Yellowstone.jpg",
    "fox3.jpg":  "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a8/Vulpes_vulpes_sitting.jpg/320px-Vulpes_vulpes_sitting.jpg",
    "fox4.jpg":  "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f0/A_red_fox_Vulpes_vulpes_in_the_snow.jpg/320px-A_red_fox_Vulpes_vulpes_in_the_snow.jpg",
    "fox5.jpg":  "https://upload.wikimedia.org/wikipedia/commons/thumb/2/24/Vulpes_vulpes_ssp_fulvus.jpg/320px-Vulpes_vulpes_ssp_fulvus.jpg",
    "fox6.jpg":  "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6b/Vulpes_vulpes_-_01.jpg/320px-Vulpes_vulpes_-_01.jpg",
    "fox7.jpg":  "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9d/Canis_lupus_ssp_familiaris_01.jpg/320px-Canis_lupus_ssp_familiaris_01.jpg",
    "fox8.jpg":  "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b0/Fuchsbau.jpg/320px-Fuchsbau.jpg",
    "fox9.jpg":  "https://upload.wikimedia.org/wikipedia/commons/thumb/3/32/RedFoxInSnow.jpg/320px-RedFoxInSnow.jpg",
    "fox10.jpg": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/19/Red_Fox_%28Vulpes_vulpes%29_%288370262369%29.jpg/320px-Red_Fox_%28Vulpes_vulpes%29_%288370262369%29.jpg",

    "wolf1.jpg":  "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5f/Kolm%C3%A5rden_Wolf.jpg/320px-Kolm%C3%A5rden_Wolf.jpg",
    "wolf2.jpg":  "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d9/GrayWolf_standing.jpg/320px-GrayWolf_standing.jpg",
    "wolf3.jpg":  "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/PNG_transparency_demonstration_1.png/280px-PNG_transparency_demonstration_1.png",
    "wolf4.jpg":  "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8d/Canis_lupus_laying.jpg/320px-Canis_lupus_laying.jpg",
    "wolf5.jpg":  "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3b/Gray_Wolf_in_Yellowstone.jpg/320px-Gray_Wolf_in_Yellowstone.jpg",
    "wolf6.jpg":  "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7b/Canis_lupus_in_Bisons_feeding.jpg/320px-Canis_lupus_in_Bisons_feeding.jpg",
    "wolf7.jpg":  "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ed/Wolf_howling_at_night.jpg/320px-Wolf_howling_at_night.jpg",
    "wolf8.jpg":  "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9f/Canis_lupus_pack_surrounding_Bison.jpg/320px-Canis_lupus_pack_surrounding_Bison.jpg",
    "wolf9.jpg":  "https://upload.wikimedia.org/wikipedia/commons/thumb/0/04/Wolf_Canis_lupus.jpg/320px-Wolf_Canis_lupus.jpg",
    "wolf10.jpg": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/68/WolfRunning.jpg/320px-WolfRunning.jpg",

    "dog1.jpg":  "https://upload.wikimedia.org/wikipedia/commons/thumb/2/26/YellowLabradorLooking_new.jpg/320px-YellowLabradorLooking_new.jpg",
    "dog2.jpg":  "https://upload.wikimedia.org/wikipedia/commons/thumb/1/18/Dog_Breeds.jpg/320px-Dog_Breeds.jpg",
    "dog3.jpg":  "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6e/Golde33443.jpg/320px-Golde33443.jpg",
    "dog4.jpg":  "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Camponotus_flavomarginatus_ant.jpg/320px-Camponotus_flavomarginatus_ant.jpg",
    "dog5.jpg":  "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e9/Beagle_portrait_Flickr.jpg/320px-Beagle_portrait_Flickr.jpg",
    "dog6.jpg":  "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d9/Collage_of_Nine_Dogs.jpg/320px-Collage_of_Nine_Dogs.jpg",
    "dog7.jpg":  "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b0/A_golden_retriever_posing_in_a_meadow.jpg/320px-A_golden_retriever_posing_in_a_meadow.jpg",
    "dog8.jpg":  "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c8/Black_Labrador_Retriever_-_Male_IMG_3323.jpg/320px-Black_Labrador_Retriever_-_Male_IMG_3323.jpg",
    "dog9.jpg":  "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/Smiley.svg/200px-Smiley.svg.png",
    "dog10.jpg": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Cat_03.jpg/320px-Cat_03.jpg",

    "bear1.jpg":  "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9e/Ursus_arctos.jpg/320px-Ursus_arctos.jpg",
    "bear2.jpg":  "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b6/Image_created_with_a_mobile_phone.png/320px-Image_created_with_a_mobile_phone.png",
    "bear3.jpg":  "https://upload.wikimedia.org/wikipedia/commons/thumb/7/71/2010-kodiak-bear-1.jpg/320px-2010-kodiak-bear-1.jpg",
    "bear4.jpg":  "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a6/Brown_bear_%28Ursus_arctos_arctos%29_2.jpg/320px-Brown_bear_%28Ursus_arctos_arctos%29_2.jpg",
    "bear5.jpg":  "https://upload.wikimedia.org/wikipedia/commons/thumb/1/14/Gatto_europeo4.jpg/320px-Gatto_europeo4.jpg",
    "bear6.jpg":  "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/Ursus_arctos_horribilis_-_Brown_bear_2.jpg/320px-Ursus_arctos_horribilis_-_Brown_bear_2.jpg",
    "bear7.jpg":  "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0d/Ursus_americanus_USFS.jpg/320px-Ursus_americanus_USFS.jpg",
    "bear8.jpg":  "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e5/Brown_Bear_-_Kamchatka_%28Ursus_arctos_beringianus%29.jpg/320px-Brown_Bear_-_Kamchatka_%28Ursus_arctos_beringianus%29.jpg",
    "bear9.jpg":  "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Tsunami_by_hokusai_19th_century.jpg/320px-Tsunami_by_hokusai_19th_century.jpg",
    "bear10.jpg": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d8/Grizzly_Bear_Fishing.jpg/320px-Grizzly_Bear_Fishing.jpg",

    "deer1.jpg":  "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0e/Odocoileus_virginianus_couesi_0001.jpg/320px-Odocoileus_virginianus_couesi_0001.jpg",
    "deer2.jpg":  "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b1/White_tailed_deer.jpg/320px-White_tailed_deer.jpg",
    "deer3.jpg":  "https://upload.wikimedia.org/wikipedia/commons/thumb/2/26/White-tailed_deer.jpg/320px-White-tailed_deer.jpg",
    "deer4.jpg":  "https://upload.wikimedia.org/wikipedia/commons/thumb/9/97/Deer_in_field.jpg/320px-Deer_in_field.jpg",
    "deer5.jpg":  "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9b/Gustav_chocolate.jpg/320px-Gustav_chocolate.jpg",
    "deer6.jpg":  "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/White-tailed_deer_doe.jpg/320px-White-tailed_deer_doe.jpg",
    "deer7.jpg":  "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Camponotus_flavomarginatus_ant.jpg/320px-Camponotus_flavomarginatus_ant.jpg",
    "deer8.jpg":  "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a6/Mule_Deer_doe.jpg/320px-Mule_Deer_doe.jpg",
    "deer9.jpg":  "https://upload.wikimedia.org/wikipedia/commons/thumb/2/25/Sika_deer_2.jpg/320px-Sika_deer_2.jpg",
    "deer10.jpg": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/65/Roe_deer_-_arp.jpg/320px-Roe_deer_-_arp.jpg",
}

HEADERS = {"User-Agent": "Mozilla/5.0 (capstone-image-downloader/1.0)"}


def download_image(url: str, dest: str) -> bool:
    try:
        resp = requests.get(url, timeout=20, headers=HEADERS, allow_redirects=True)
        if resp.status_code == 200 and len(resp.content) > 500:
            with open(dest, "wb") as f:
                f.write(resp.content)
            return True
        print(f"  Warning: status {resp.status_code}, size {len(resp.content)} bytes")
        return False
    except Exception as exc:
        print(f"  Error: {exc}")
        return False


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    downloaded = 0
    skipped = 0
    failed = []

    total = len(IMAGES)
    for i, (filename, url) in enumerate(IMAGES.items(), start=1):
        dest = os.path.join(OUTPUT_DIR, filename)
        if os.path.exists(dest) and os.path.getsize(dest) > 500:
            print(f"[{i}/{total}] Skipping {filename} (exists)")
            skipped += 1
            continue

        print(f"[{i}/{total}] Downloading {filename}...")
        ok = download_image(url, dest)
        if ok:
            downloaded += 1
            print(f"  OK ({os.path.getsize(dest)} bytes)")
        else:
            failed.append(filename)
        time.sleep(0.2)

    print(f"\nDone: {downloaded} downloaded, {skipped} skipped, {len(failed)} failed")
    if failed:
        print("Failed files (add manually to corpus/):", failed)
    print(f"Corpus location: {os.path.abspath(OUTPUT_DIR)}")


if __name__ == "__main__":
    main()
