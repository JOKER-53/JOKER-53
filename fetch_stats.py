"""
Fetches real GitHub data for a user and renders two neo-brutalist SVG cards:
  - stats.svg      (repos, followers, following, total stars, status)
  - languages.svg  (top languages by bytes across all owned repos)

Requires: GITHUB_TOKEN (repo/user read scope) and GITHUB_USER env vars.
Run via GitHub Actions on a schedule (see workflow below).
"""

import os
import sys
import requests
from collections import defaultdict

TOKEN = os.environ["GH_TOKEN"]
USER = os.environ["GH_USER"]
API = "https://api.github.com"
HEADERS = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github+json"}

PALETTE = {
    "cream": "#F2EEE3",
    "black": "#0A0A0A",
    "yellow": "#FFDE59",
    "orange": "#FF5A36",
    "teal": "#4FD1C5",
    "muted": "#7A7568",
}
COLOR_CYCLE = ["#FFDE59", "#FF5A36", "#4FD1C5", "#0A0A0A", "#B8B2A0"]


def gh_get(path, params=None):
    r = requests.get(f"{API}{path}", headers=HEADERS, params=params or {})
    r.raise_for_status()
    return r.json()


def fetch_user():
    return gh_get(f"/users/{USER}")


def fetch_all_repos():
    repos, page = [], 1
    while True:
        batch = gh_get(f"/users/{USER}/repos", params={"per_page": 100, "page": page, "type": "owner"})
        if not batch:
            break
        repos.extend(batch)
        page += 1
    return repos


def fetch_total_stars(repos):
    return sum(r["stargazers_count"] for r in repos)


def fetch_language_bytes(repos):
    totals = defaultdict(int)
    for r in repos:
        if r.get("fork"):
            continue
        langs = gh_get(f"/repos/{USER}/{r['name']}/languages")
        for lang, byte_count in langs.items():
            totals[lang] += byte_count
    return totals


def top_languages(lang_bytes, n=4):
    total = sum(lang_bytes.values()) or 1
    ranked = sorted(lang_bytes.items(), key=lambda kv: kv[1], reverse=True)[:n]
    return [(name, round(100 * count / total, 1)) for name, count in ranked]


def rank_letter(stars, repos, followers):
    # simple heuristic scoring — swap for a real rank algorithm if desired
    score = stars * 3 + repos * 1 + followers * 2
    if score > 300:
        return "A+"
    if score > 150:
        return "A"
    if score > 80:
        return "B+"
    if score > 30:
        return "B"
    return "C+"


def render_stats_svg(user, total_stars, repo_count, rank):
    followers = user["followers"]
    following = user["following"]
    return f"""<svg width="480" height="280" viewBox="0 0 480 280" xmlns="http://www.w3.org/2000/svg" font-family="'Arial Black','Helvetica Neue',Arial,sans-serif">
  <rect x="0" y="0" width="480" height="280" fill="{PALETTE['cream']}"/>
  <rect x="18" y="18" width="440" height="244" fill="{PALETTE['black']}"/>
  <rect x="10" y="10" width="440" height="244" fill="#FFFFFF" stroke="{PALETTE['black']}" stroke-width="4"/>
  <rect x="10" y="10" width="290" height="38" fill="{PALETTE['teal']}" stroke="{PALETTE['black']}" stroke-width="4"/>
  <text x="30" y="35" font-size="12.5" fill="{PALETTE['black']}" letter-spacing="0.3" font-weight="900">{user['login'].upper()}'S GITHUB STATS</text>
  <g font-family="'JetBrains Mono',monospace" font-weight="700" font-size="14">
    <text x="32" y="82" fill="{PALETTE['black']}">TOTAL STARS EARNED</text>
    <text x="270" y="82" fill="{PALETTE['black']}" text-anchor="end" font-weight="900">{total_stars}</text>
    <text x="32" y="112" fill="{PALETTE['black']}">PUBLIC REPOS</text>
    <text x="270" y="112" fill="{PALETTE['black']}" text-anchor="end" font-weight="900">{repo_count}</text>
    <text x="32" y="142" fill="{PALETTE['black']}">FOLLOWERS</text>
    <text x="270" y="142" fill="{PALETTE['black']}" text-anchor="end" font-weight="900">{followers}</text>
    <text x="32" y="172" fill="{PALETTE['black']}">FOLLOWING</text>
    <text x="270" y="172" fill="{PALETTE['black']}" text-anchor="end" font-weight="900">{following}</text>
  </g>
  <line x1="32" y1="188" x2="270" y2="188" stroke="{PALETTE['black']}" stroke-width="3"/>
  <g transform="translate(310,70)">
    <rect x="0" y="0" width="130" height="130" fill="{PALETTE['yellow']}" stroke="{PALETTE['black']}" stroke-width="4" transform="rotate(-4 65 65)"/>
    <rect x="6" y="6" width="118" height="118" fill="#FFFFFF" stroke="{PALETTE['black']}" stroke-width="4"/>
    <text x="65" y="70" font-size="34" fill="{PALETTE['black']}" text-anchor="middle" font-weight="900">{rank}</text>
    <text x="65" y="96" font-size="11" fill="{PALETTE['muted']}" text-anchor="middle" letter-spacing="1" font-weight="900">RANK</text>
  </g>
</svg>"""


def render_languages_svg(top_langs):
    rows = []
    y_label, y_bar = 84, 90
    for i, (name, pct) in enumerate(top_langs):
        color = COLOR_CYCLE[i % len(COLOR_CYCLE)]
        bar_w = round(3.96 * pct)  # scale to 396px max width
        rows.append(f'''
    <text x="32" y="{y_label}" font-size="13" fill="{PALETTE['black']}" font-weight="900">{name.upper()}</text>
    <text x="428" y="{y_label}" font-size="13" fill="{PALETTE['black']}" text-anchor="end" font-weight="900">{pct}%</text>
    <rect x="32" y="{y_bar}" width="396" height="16" fill="{PALETTE['cream']}" stroke="{PALETTE['black']}" stroke-width="2.5"/>
    <rect x="32" y="{y_bar}" width="{bar_w}" height="16" fill="{color}" stroke="{PALETTE['black']}" stroke-width="2.5"/>''')
        y_label += 46
        y_bar += 46
    bars = "".join(rows)
    return f"""<svg width="480" height="280" viewBox="0 0 480 280" xmlns="http://www.w3.org/2000/svg" font-family="'Arial Black','Helvetica Neue',Arial,sans-serif">
  <rect x="0" y="0" width="480" height="280" fill="{PALETTE['cream']}"/>
  <rect x="18" y="18" width="440" height="244" fill="{PALETTE['black']}"/>
  <rect x="10" y="10" width="440" height="244" fill="#FFFFFF" stroke="{PALETTE['black']}" stroke-width="4"/>
  <rect x="10" y="10" width="180" height="38" fill="{PALETTE['yellow']}" stroke="{PALETTE['black']}" stroke-width="4"/>
  <text x="100" y="35" font-size="14" fill="{PALETTE['black']}" text-anchor="middle" letter-spacing="0.5" font-weight="900">TOP LANGUAGES</text>
  <g font-family="'JetBrains Mono',monospace" font-weight="700">{bars}
  </g>
</svg>"""


def main():
    user = fetch_user()
    repos = fetch_all_repos()
    total_stars = fetch_total_stars(repos)
    lang_bytes = fetch_language_bytes(repos)
    top_langs = top_languages(lang_bytes, n=4)
    rank = rank_letter(total_stars, user["public_repos"], user["followers"])

    os.makedirs("dist", exist_ok=True)
    with open("dist/stats.svg", "w") as f:
        f.write(render_stats_svg(user, total_stars, user["public_repos"], rank))
    with open("dist/languages.svg", "w") as f:
        f.write(render_languages_svg(top_langs))

    print(f"stars={total_stars} repos={user['public_repos']} rank={rank}")
    print(f"top_langs={top_langs}")


if __name__ == "__main__":
    main()
