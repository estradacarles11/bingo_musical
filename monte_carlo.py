import random
from tqdm import tqdm
import json
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

JSON_PATH = Path("extract_chatgpt.json")

with open(JSON_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

song_list_filename = "Bingo_Musical_Boda_EstiCarles.xlsx"
song_list_file = pd.ExcelFile(song_list_filename)
song_list_df = pd.read_excel(song_list_filename, sheet_name="Playlist", header=0)

song_dict = song_list_df.T.to_dict()

song_list = [
    {"artist": song_dict[song]["Artista"], "title": song_dict[song]["Cancion"]}
    for song in song_dict.keys()
]

max_row_cnt = 4
max_bingo_cnt = 2

results = []

for i in tqdm(range(1000), desc="Monte Carlo"):

    shuffled_song_list = random.sample(song_list, len(song_list))
    sheets = [
        [
            [
                {"artist": song["artist"], "title": song["title"], "played": False}
                for song in row
            ]
            for row in sheet["songs"]
        ]
        for sheet in data["sheets"]
    ]

    song_cnt = 0
    row_stats = {"count": 0, "number_of_songs": []}
    bingo_stats = {"count": 0, "number_of_songs": []}

    for played in tqdm(shuffled_song_list, desc=f"Iteration {i}", leave=False):
        for sheet in tqdm(
            sheets, desc=f"{played['artist']} - {played['title']}", leave=False
        ):
            played_in_sheet = False
            for row in sheet:
                played_in_row = False
                for song in row:
                    if (
                        song["title"] == played["title"]
                        and song["artist"] == played["artist"]
                    ):
                        song["played"] = True
                        played_in_row = True
                        played_in_sheet = True
                        break
                if (
                    played_in_row
                    and row_stats["count"] < max_row_cnt
                    and all([song["played"] for song in row])
                ):
                    row_stats["count"] += 1
                    row_stats["number_of_songs"].append(song_cnt + 1)
            if played_in_sheet and all(
                [song["played"] for row in sheet for song in row]
            ):
                bingo_stats["count"] += 1
                bingo_stats["number_of_songs"].append(song_cnt + 1)
        song_cnt += 1
        if bingo_stats["count"] >= max_bingo_cnt:
            break

    results.append(
        {"song_cnt": song_cnt, "row_stats": row_stats, "bingo_stats": bingo_stats}
    )

with open("results.json", "w") as f:
    json.dump(results, f, indent=2)

fig, ((ax0, ax1)) = plt.subplots(nrows=1, ncols=2)

ax0.hist(
    [result["bingo_stats"]["number_of_songs"][0] for result in results],
    density=False,
    histtype="barstacked",
    rwidth=0.8,
    facecolor="b",
)
ax0.set_ylabel("# of rounds")
ax0.set_xlabel("# of songs for 1st Bingo")

ax1.hist(
    [result["bingo_stats"]["number_of_songs"][1] for result in results],
    density=False,
    histtype="barstacked",
    rwidth=0.8,
    facecolor="r",
)
ax1.set_ylabel("# of rounds")
ax1.set_xlabel("# of songs for 2nd Bingo")

plt.show()
