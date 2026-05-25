import csv
import requests
import networkx as nx
from flask import Flask, render_template, jsonify
from datetime import datetime
from functools import lru_cache
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
    print("response:", response)

    if response.status_code == 200:
        repos = response.json()
        print("repos:", repos)
        return tuple(repos)  # lru_cache requires hashable return types
    else:
        print("Error:", response.text)
        return ()


def load_users_from_csv():
    """Load user rows from a local CSV file instead of Google Sheets."""
    users = []
    try:
        with open(CSV_FILE, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)

        if not rows:
            print("CSV file is empty.")
            return users

        # Skip header row
        for row in rows[1:]:
            if len(row) >= 3:
                users.append({"email": row[1], "username": row[2]})
    except FileNotFoundError:
        print(f"Error: CSV file '{CSV_FILE}' not found.")
    return users


def create_github_graph():
    users = load_users_from_csv()
    repos_data = []

    for user in users:
        email = user["email"]
        username = user["username"]
        print("username:", username)

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
                print(f"Error for {username}: {repo['message']}")

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
    app.run(debug=True)
