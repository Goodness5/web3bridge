import csv
import requests
import networkx as nx
import plotly.graph_objects as go
from flask import Flask, render_template
from datetime import datetime

app = Flask(__name__)

# Function to fetch GitHub repositories for a given username
def get_user_repos(username):
    url = f"https://api.github.com/users/{username}/repos"
    response = requests.get(url)

    if response.status_code == 200:
        repos = response.json()
        return repos  # Return the repository data instead of printing
    else:
        print("Error:", response.status_code)
        # Return an empty list in case of an error
        return []

@app.route('/')
def index():
    csv_file = "./data.csv"
    repos_data = []  # List to store repository data

    with open(csv_file, 'r') as file:
        csv_reader = csv.reader(file)
        header = next(csv_reader)  # Skip header row

        for row in csv_reader:
            if len(row) >= 3:  # Check if row has at least 2 elements
                email = row[1]
                username = row[0]
                github_repos = get_user_repos(username)  # Fetch repository data

                for repo in github_repos:
                    created_date = repo["created_at"]
                    created_date = datetime.strptime(created_date, "%Y-%m-%dT%H:%M:%SZ")
                    if created_date >= datetime(2021, 6, 1):
                        repo["email"] = email
                        repo["username"] = username
                        repos_data.append(repo)

    # Create a network graph using NetworkX
    G = nx.Graph()

    for repo in repos_data:
        user = repo["owner"]["login"]
        repo_name = repo["name"]
        repo_url = repo["html_url"]
        G.add_node(repo_name, user=user, email=repo["email"], url=repo_url)
        G.add_edge(user, repo_name)

    # Create a layout for the network graph using fruchterman_reingold_layout
    pos = nx.fruchterman_reingold_layout(G)

    # Extract node and edge data for visualization
    node_x = []
    node_y = []
    node_text = []
    node_hovertext = []
    edge_x = []
    edge_y = []

    for node, (x, y) in pos.items():
        node_x.append(x)
        node_y.append(y)
        node_text.append(node)
        node_hovertext.append(f"User: {G.nodes[node]['user']}<br>Repository: {node}")

    for edge in G.edges:
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.append(x0)
        edge_x.append(x1)
        edge_x.append(None)
        edge_y.append(y0)
        edge_y.append(y1)
        edge_y.append(None)

    # Create a scatter plot using Plotly.js
    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers",
        marker=dict(size=10, color="red"),
        text=node_hovertext,
        hoverinfo="text"
    )

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        mode="lines",
        line=dict(width=1, color="black"),
        hoverinfo="none"
    )

    data = [edge_trace, node_trace]

    layout = go.Layout(
        title="GitHub Repository Network",
        showlegend=False,
        hovermode="closest",
        margin=dict(b=20, l=5, r=5, t=40),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor="black",
        paper_bgcolor="black"
    )

    fig = go.Figure(data=data, layout=layout)

    # Convert the plot to HTML
    plot_html = fig.to_html(full_html=False)

    return render_template('index.html', plot_html=plot_html)

if __name__ == '__main__':
    app.run(debug=True)
