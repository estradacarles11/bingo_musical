import random
from tqdm import tqdm
import json
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import logging
import sys

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

number_of_sheets = 120

results = []
shorter_song_list = song_list
winning_sheets = [{"sheet_number": 0, "songs": []}]
shorter_stats = {
    "song_cnt": len(song_list),
    "row_stats": {"count": 0, "number_of_songs": []},
    "bingo_stats": {"count": 0, "number_of_songs": []},
}

for i in tqdm(range(10000), desc="Monte Carlo"):

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
    shuffled_sheets = random.sample(sheets, number_of_sheets)
    shuffled_song_list = random.sample(song_list, len(song_list))

    song_cnt = 0
    row_stats = {"count": 0, "number_of_songs": [], "extra_winning_sheet_numbers": []}
    bingo_stats = {"count": 0, "number_of_songs": [], "extra_winning_sheet_numbers": []}
    bingo_sheets = []

    # for played in tqdm(shuffled_song_list, desc=f"Iteration {i}", leave=False):
    #     for i in tqdm(
    #         range(len(sheets)),
    #         desc=f"{played['artist']} - {played['title']}",
    #         leave=False,
    #     ):    # for played in tqdm(shuffled_song_list, desc=f"Iteration {i}", leave=False):
    for played in shuffled_song_list:
        for i in range(
            len(sheets)
        ):  # for played in tqdm(shuffled_song_list, desc=f"Iteration {i}", leave=False):
            sheet_in_shuffled = sheets[i] in shuffled_sheets
            played_in_sheet = False
            for row in sheets[i]:
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
                    row_stats["number_of_songs"].append(song_cnt + 1)
                    if sheet_in_shuffled:
                        row_stats["count"] += 1
                    else:
                        row_stats["extra_winning_sheet_numbers"].append(i)
            if played_in_sheet and all(
                [song["played"] for row in sheets[i] for song in row]
            ):
                bingo_stats["number_of_songs"].append(song_cnt + 1)
                if sheet_in_shuffled:
                    bingo_stats["count"] += 1
                    bingo_sheets.append(i)
                else:
                    bingo_stats["extra_winning_sheet_numbers"].append(i)
        song_cnt += 1
        if bingo_stats["count"] >= max_bingo_cnt:
            break

    results.append(
        {"song_cnt": song_cnt, "row_stats": row_stats, "bingo_stats": bingo_stats}
    )
    if (
        song_cnt < shorter_stats["song_cnt"]
        and len(row_stats["number_of_songs"]) == len(set(row_stats["number_of_songs"]))
        and len(bingo_stats["number_of_songs"])
        == len(set(bingo_stats["number_of_songs"]))
        and len(row_stats["extra_winning_sheet_numbers"]) == 0
        and len(bingo_stats["extra_winning_sheet_numbers"]) == 0
    ):
        shorter_stats = {
            "song_cnt": song_cnt,
            "row_stats": row_stats,
            "bingo_stats": bingo_stats,
        }
        shorter_song_list = shuffled_song_list
        winning_sheets = [
            {"sheet_number": i + 1, "songs": sheets[i]} for i in bingo_sheets
        ]

if len(winning_sheets) == max_bingo_cnt:
    targets = logging.StreamHandler(sys.stdout), logging.FileHandler("results.log")
    logging.basicConfig(format="%(message)s", level=logging.INFO, handlers=targets)

    logging.info(f"Shortest Song list: {shorter_stats['song_cnt']} songs")
    logging.info(f"Rows at songs: {shorter_stats['row_stats']['number_of_songs']}")
    logging.info(f"Bingos at songs: {shorter_stats['bingo_stats']['number_of_songs']}")
    for i, sheet in enumerate(winning_sheets):
        logging.info("")
        logging.info(f"Winning Sheet {i + 1}: {sheet['sheet_number']}")
        logging.info(
            "+--------------------+--------------------+--------------------+--------------------+--------------------+"
        )
        for row in sheet["songs"]:
            logging.info(
                f"| {row[0]['artist'].ljust(18)[:18]} | {row[1]['artist'].ljust(18)[:18]} | {row[2]['artist'].ljust(18)[:18]} | {row[3]['artist'].ljust(18)[:18]} | {row[4]['artist'].ljust(18)[:18]} |"
            )
            logging.info(
                f"| {row[0]['title'].ljust(18)[:18]} | {row[1]['title'].ljust(18)[:18]} | {row[2]['title'].ljust(18)[:18]} | {row[3]['title'].ljust(18)[:18]} | {row[4]['title'].ljust(18)[:18]} |"
            )
            logging.info(
                "+--------------------+--------------------+--------------------+--------------------+--------------------+"
            )

with open("results.json", "w") as f:
    json.dump(results, f, indent=2)

with open("shorter_song_list.json", "w") as f:
    json.dump(shorter_song_list, f, indent=2)

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
