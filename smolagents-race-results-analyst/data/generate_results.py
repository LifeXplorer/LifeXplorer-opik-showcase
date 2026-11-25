"""Regenerate data/saltmarsh_2025.csv (fictional race, fixed seed).

Not needed to run the example: the CSV is committed. Planted findings:
- Dune Pacers: most finishers run the second half faster (negative split).
- Age group 60+: unusually high DNF rate.
- Women 40-44: one clear winner.
"""

import csv
import random
from pathlib import Path

rng = random.Random(2025)
CLUBS = ["Harbour Striders", "Gull Road Runners", "Tidewater TC", "Lighthouse Joggers", "Dune Pacers", "Unattached"]
GROUPS = ["18-34", "35-39", "40-44", "45-49", "50-59", "60+"]
FIRST_F = ["Maren", "Ines", "Tove", "Lucia", "Odile", "Priya", "Hana", "Greta", "Noor", "Sela", "Britta", "Ayla"]
FIRST_M = ["Tobias", "Emil", "Rafael", "Joren", "Kasper", "Dario", "Anders", "Mateo", "Idris", "Lukas", "Soren", "Pavel"]
LAST = ["Alder", "Brandt", "Corvell", "Dunmore", "Eskild", "Fenwick", "Garrow", "Holm", "Ivers", "Jessop", "Kerrigan", "Lindqvist", "Marlow", "Nyberg", "Oakes", "Pryce"]


def fmt(sec: int) -> str:
    return f"{sec // 3600}:{sec % 3600 // 60:02d}:{sec % 60:02d}"


rows = []
used = set()
for bib in range(101, 341):
    gender = rng.choice("FM")
    group = rng.choices(GROUPS, weights=[30, 18, 16, 14, 14, 8])[0]
    club = rng.choice(CLUBS)
    while True:
        name = f"{rng.choice(FIRST_F if gender == 'F' else FIRST_M)} {rng.choice(LAST)}"
        if name not in used:
            used.add(name)
            break
    base = rng.gauss(14400 if gender == "M" else 15600, 1500) + GROUPS.index(group) * 240
    base = max(int(base), 10200)
    neg_p = 0.8 if club == "Dune Pacers" else 0.12
    first_half_share = 0.515 if rng.random() < neg_p else 0.485
    dnf_p = 0.3 if group == "60+" else 0.04
    dnf = rng.random() < dnf_p
    rows.append(dict(bib=bib, runner=name, gender=gender, age_group=group, club=club,
                     half_split=fmt(int(base * first_half_share)),
                     chip_time="" if dnf else fmt(base), status="DNF" if dnf else "FIN"))

# Make the women's 40-44 winner unambiguous and fast.
cands = [r for r in rows if r["gender"] == "F" and r["age_group"] == "40-44" and r["status"] == "FIN"]
best = min(cands, key=lambda r: r["chip_time"])
best["chip_time"], best["half_split"] = "3:04:18", "1:33:10"

out = Path(__file__).parent / "saltmarsh_2025.csv"
with out.open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
print(f"wrote {len(rows)} rows to {out}")
