import json
import re
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

URL = "https://fcdata.io/objectives"

response = requests.get(
    URL,
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=30
)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

lines = [
    re.sub(r"\s+", " ", line).strip()
    for line in soup.get_text("\n").splitlines()
    if line.strip()
]

objectives = []
category = "Objectif"
status = "Actif"

for i, line in enumerate(lines):
    if line.startswith("Active "):
        status = "Actif"
        category = line.replace("Active ", "").strip()

    elif line.startswith("Expired "):
        status = "Expiré"

    match = re.search(r"(\d+)\s+tasks?\s+(.+)", line, re.I)

    if match and status == "Actif":
        title = lines[i - 2] if i >= 2 else "Objectif"

        rewards = []

        if i + 1 < len(lines) and lines[i + 1] == "Group rewards":
            for reward in lines[i + 2:i + 8]:
                if reward == "View tasks and rewards":
                    break
                rewards.append(reward)

        objectives.append({
            "title": title,
            "category": category,
            "status": status,
            "tasks": int(match.group(1)),
            "expiry": match.group(2),
            "rewards": rewards
        })

if not objectives:
    raise RuntimeError("Aucun objectif détecté sur FCData.")

data = {
    "updated": datetime.now(ZoneInfo("Europe/Paris")).isoformat(),
    "source": URL,
    "objectives": objectives
}

with open("data.json", "w", encoding="utf-8") as file:
    json.dump(data, file, ensure_ascii=False, indent=2)

print(f"{len(objectives)} objectifs récupérés.")
