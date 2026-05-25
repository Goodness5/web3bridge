import csv
import requests
import networkx as nx
from flask import Flask, render_template, jsonify
from datetime import datetime
from functools import lru_cache
from urllib.parse import urlparse
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
CSV_FILE = os.getenv("CSV_FILE", "data.csv")


@lru_cache(maxsize=128)
def get_user_repos(username):
    url = f"https://api.github.com/users/{username}/repos"
    headers = {}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    response = requests.get(url, headers=headers)
    print(f"  [{username}] response: {response.status_code}")

    if response.status_code == 200:
        repos = response.json()
        return tuple(repos)  # lru_cache requires hashable type
    else:
        print(f"  [{username}] Error: {response.text}")
        return ()


def extract_github_username(raw: str) -> str:
    """
    Extract just the username from any of these formats:
      https://github.com/Qreamville
      https://github.com/devtosxn/       <- trailing slash
      http://github.com/emmaglorypraise
      https://www.github.com/rasheey97-alt
      github.com/ginakev                  <- no scheme
      github.com/osazeejedi/my-project    <- sub-path, ignore it
      Qreamville                          <- already plain username
    Returns empty string if nothing usable found.
    """
    raw = raw.strip().rstrip("/")
    if not raw:
        return ""

    # Add scheme so urlparse works on scheme-less URLs like "github.com/user"
    if not raw.startswith("http"):
        raw = "https://" + raw

    parsed = urlparse(raw)

    if "github.com" not in parsed.netloc:
        return ""

    # Path is /username or /username/ or /username/repo — first segment is the username
    parts = [p for p in parsed.path.split("/") if p]
    return parts[0] if parts else ""


def load_users_from_csv():
    """
    Load users from the messy CSV which has:
    - Cohort header rows  (e.g. 'Cohort V,,')
    - Two column layouts: (email, github) or (empty, email, github)
    - Full GitHub URLs instead of plain usernames
    - Trailing slashes / sub-paths in URLs
    - Empty rows and duplicates
    """
    SKIP_KEYWORDS = {"cohort", "email", "github", "name"}
    users = []
    seen = set()   # deduplicate by (email, username)

    try:
        with open(CSV_FILE, newline="", encoding="utf-8-sig") as f:
            rows = list(csv.reader(f))
    except FileNotFoundError:
        print(f"Error: CSV file '{CSV_FILE}' not found.")
        return users

    for row in rows:
        row = [cell.strip() for cell in row]

        # Skip completely empty rows
        if not any(row):
            continue

        # Detect column layout:
        # Layout A: email=col[0], github=col[1]
        # Layout B: blank=col[0], email=col[1], github=col[2]
        email_col = github_col = None
        if len(row) >= 2 and "@" in row[0]:
            email_col, github_col = 0, 1
        elif len(row) >= 3 and "@" in row[1]:
            email_col, github_col = 1, 2
        else:
            continue  # cohort label or unusable row

        email = row[email_col].lower()
        raw_github = row[github_col]

        # Skip header-like rows
        if any(kw in email for kw in SKIP_KEYWORDS):
            continue

        username = extract_github_username(raw_github)
        if not username:
            print(f"Skipping — no username found in: '{raw_github}'")
            continue

        key = (email, username.lower())
        if key in seen:
            continue
        seen.add(key)

        users.append({"email": email, "username": username})

    print(f"Total unique users loaded: {len(users)}")
    return users


def create_github_graph():
    users = load_users_from_csv()
    repos_data = []

    for user in users:
        email = user["email"]
        username = user["username"]
        print(f"Fetching repos for: {username}")

        github_repos = get_user_repos(username)
        for repo in github_repos:
            if "message" not in repo:
                created_date = datetime.strptime(repo["created_at"], "%Y-%m-%dT%H:%M:%SZ")
                if created_date >= datetime(2021, 6, 1):
                    repos_data.append({
                        **repo,
                        "email": email,
                        "username": username,
                    })
            else:
                print(f"  Repo error for {username}: {repo['message']}")

    G = nx.Graph()

    for repo in repos_data:
        G.add_node(repo["name"], email=repo["email"], size=3)

    for username in set(repo["username"] for repo in repos_data):
        G.add_node(username, email="", size=5, color="red")
        for repo in repos_data:
            if repo["username"] == username:
                G.add_edge(username, repo["name"], color="red")

    return G


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/data")
def data():
    G = create_github_graph()
    graph_data = {"nodes": [], "links": []}

    for node in G.nodes():
        node_attrs = G.nodes[node]
        if node_attrs.get("email") is not None:
            graph_data["nodes"].append({
                "id": node,
                "group": "repo",
                "email": node_attrs.get("email", ""),
            })
        else:
            graph_data["nodes"].append({
                "id": node,
                "group": "user",
            })

    for edge in G.edges():
        graph_data["links"].append({
            "source": edge[0],
            "target": edge[1],
        })

    return jsonify(graph_data)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
