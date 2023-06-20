import csv
import requests
import networkx as nx
from flask import Flask, render_template, jsonify
from datetime import datetime
from functools import lru_cache

app = Flask(__name__)

# csv_file = "/home/Iamsuperman/web3bridge/data.csv"  # Production

# Cache the results of the get_user_repos function
@lru_cache(maxsize=128)
def get_user_repos(username):
    url = f"https://api.github.com/users/{username}/repos"
    headers = {
        'Authorization': 'Bearer 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',
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        repos = response.json()
        return repos
    else:
        print("Error:", response.text)
        return []

def create_github_graph():
    csv_file = "./data.csv"
    repos_data = []

    with open(csv_file, 'r') as file:
        csv_reader = csv.reader(file)
        header = next(csv_reader)

        for row in csv_reader:
            if len(row) >= 3:
                email = row[1]
                username = row[0]
                github_repos = get_user_repos(username)

                for repo in github_repos:
                    if "message" not in repo:
                        created_date = repo["created_at"]
                        created_date = datetime.strptime(created_date, "%Y-%m-%dT%H:%M:%SZ")
                        if created_date >= datetime(2021, 6, 1):
                            repo["email"] = email
                            repo["username"] = username
                            repos_data.append(repo.copy())
                    else:
                        print(f"Error: {repo['message']}")

    G = nx.Graph()
    for repo in repos_data:
        G.add_node(repo["name"], email=repo["email"], size=3)
        G.add_edge(repo["username"], repo["name"])

    for username in set(repo["username"] for repo in repos_data):
        G.add_node(username, email="", size=5, color="red")
        user_repos = [repo["name"] for repo in repos_data if repo["username"] == username]
        for repo in user_repos:
            G.add_edge(username, repo, color="red")

    return G

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data')
def data():
    G = create_github_graph()

    graph_data = {
        'nodes': [],
        'links': []
    }

    for node in G.nodes():
        if 'email' in G.nodes[node]:
            graph_data['nodes'].append({
                'id': node,
                'group': 'repo',
                'email': G.nodes[node]['email']
            })
        else:
            graph_data['nodes'].append({
                'id': node,
                'group': 'user'
            })

    for edge in G.edges():
        graph_data['links'].append({
            'source': edge[0],
            'target': edge[1]
        })

    return jsonify(graph_data)

if __name__ == "__main__":
    app.run()
