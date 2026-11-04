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

objectives = []
seen = set()

for heading in soup.find_all(["h2", "h3", "h4"]):
    title = re.sub(r"\s+", " ", heading.get_text(" ", strip=True)).strip()

    if not title or title.lower() in {"fc 27 objectives", "group rewards"}:
        continue

    card = None

    for parent in heading.parents:
        if getattr(parent, "name", None) in {"body", "html"}:
            break

        block_text = re.sub(r"\s+", " ", parent.get_text(" ", strip=True))

        if (
            re.search(r"\b\d+\s+tasks?\b", block_text, re.I)
            and "Group rewards" in block_text
            and "View tasks and rewards" in block_text
        ):
            card = parent
            break

    if card is None:
        continue

    card_text = re.sub(r"\s+", " ", card.get_text(" ", strip=True))

    task_match = re.search(
        r"\b(\d+)\s+tasks?\s+(\d{1,2}\s+[A-Za-zÀ-ÿ]+\s+\d{4},\s*\d{2}:\d{2})",
        card_text,
        re.I
    )

    if not task_match or title in seen:
        continue

    status = "Actif"
    category = "Objectif"

    for previous in heading.find_all_previous(string=True):
        label = re.sub(r"\s+", " ", str(previous)).strip()

        if label.startswith("Active "):
            category = label[len("Active "):].strip()
            break

        if label.startswith("Expired "):
            status = "Expiré"
            category = label[len("Expired "):].strip()
            break

    if status != "Actif":
        continue

    rewards = []
    reward_match = re.search(
        r"Group rewards\s+(.*?)\s+View tasks and rewards",
        card_text,
        re.I
    )

    if reward_match:
        reward_text = reward_match.group(1).strip()
        if reward_text:
            rewards = [reward_text]

    objectives.append({
        "title": title,
        "category": category,
        "status": status,
        "tasks": int(task_match.group(1)),
        "expiry": task_match.group(2),
        "rewards": rewards
    })

    seen.add(title)

if not objectives:
    print("Titres détectés :", [
        h.get_text(" ", strip=True)
        for h in soup.find_all(["h2", "h3", "h4"])[:20]
    ])
    raise RuntimeError("Aucun objectif actif détecté sur FCData.")

data = {
    "updated": datetime.now(ZoneInfo("Europe/Paris")).isoformat(),
    "source": URL,
    "objectives": objectives
}

with open("data.json", "w", encoding="utf-8") as file:
    json.dump(data, file, ensure_ascii=False, indent=2)

print(f"{len(objectives)} objectifs actifs récupérés.")
