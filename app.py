import csv
import requests
import networkx as nx
import plotly.graph_objects as go
from flask import Flask, render_template
from datetime import datetime
import time
import math
import random


app = Flask(__name__)

# Function to fetch GitHub repositories for a given username
def get_user_repos(username):
    url = f"https://api.github.com/users/{username}/repos"
    headers = {
        'Authorization': 'Bearer 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',
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        repos = response.json()
        return repos  # Return the repository data instead of printing
    else:
        print("Error:", response.text)  # Print the response message instead of the response code
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
                    if "message" not in repo:  # Check if the repository exists
                        created_date = repo["created_at"]
                        created_date = datetime.strptime(created_date, "%Y-%m-%dT%H:%M:%SZ")
                        if created_date >= datetime(2021, 6, 1):
                            repo["email"] = email
                            repo["username"] = username
                            repos_data.append(repo)
                            # time.sleep(1)  # Pause execution for 1 second between API requests
                    else:
                        print(f"Error: {repo['message']}")  # Print the error message for 404 errors

    G = nx.Graph()
    for repo in repos_data:
        G.add_node(repo["username"], email=repo["email"], size=20)
        G.add_node(repo["name"], email=repo["email"], size=10)
        G.add_edge(repo["username"], repo["name"], color=repo["username"])

    # Create a list of repositories grouped under each user
    grouped_repos = {}
    for repo in repos_data:
        username = repo["username"]
        if username not in grouped_repos:
            grouped_repos[username] = []
        grouped_repos[username].append(repo["name"])

    num_nodes = len(G.nodes())
    user_lat_gap = 180 / (num_nodes // 2 + 1)
    repo_lat_gap = 5
    random.seed(42)  # Set the random seed for reproducibility

    for i, node in enumerate(G.nodes()):
        if node in repos_data:
            username = G.nodes[node]["email"]
            repo_index = grouped_repos[username].index(node)
            lat = 90 - (i // 2) * user_lat_gap + random.uniform(-1, 1) * repo_lat_gap
            lng = random.random() * 360  # Generate a random longitude between 0 and 360
        else:
            lat = 90 - (i // 2) * user_lat_gap
            lng = random.random() * 360  # Generate a random longitude between 0 and 360

        G.nodes[node]["lat"] = lat
        G.nodes[node]["lng"] = lng



    # Rest of the code...


    # Define a function to convert latitude and longitude to spherical coordinates
    def lat_lng_to_sphere_coords(lat, lng, radius):
        # Convert latitude and longitude to radians
        lat_rad = lat * math.pi / 180
        lng_rad = lng * math.pi / 180

        # Calculate the Cartesian coordinates on the sphere
        x = radius * math.cos(lat_rad) * math.cos(lng_rad)
        y = radius * math.sin(lat_rad)
        z = radius * math.cos(lat_rad) * math.sin(lng_rad)

        return x, y, z

    # Convert the latitude and longitude coordinates to Cartesian coordinates on the sphere
    radius = 1.0  # Adjust this value to control the size of the sphere
    for node in G.nodes():
        lat = G.nodes[node]["lat"]
        lng = G.nodes[node]["lng"]
        x, y, z = lat_lng_to_sphere_coords(lat, lng, radius)
        G.nodes[node]["x"] = x
        G.nodes[node]["y"] = y
        G.nodes[node]["z"] = z

    edge_x = []
    edge_y = []
    edge_z = []
    edge_colors = []
    for edge in G.edges():
        x0 = G.nodes[edge[0]]["x"]
        y0 = G.nodes[edge[0]]["y"]
        z0 = G.nodes[edge[0]]["z"]
        x1 = G.nodes[edge[1]]["x"]
        y1 = G.nodes[edge[1]]["y"]
        z1 = G.nodes[edge[1]]["z"]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        edge_z.extend([z0, z1, None])
        edge_colors.append(G.nodes[edge[0]]["color"])  # Set edge color based on the user, not the repository

    edge_trace = go.Scatter3d(
        x=edge_x, y=edge_y, z=edge_z,
        line=dict(color='#888'),
        hoverinfo='none',
        mode='lines')

    node_x = []
    node_y = []
    node_z = []
    node_sizes = []
    node_colors = []
    for node in G.nodes():
        x = G.nodes[node]["x"]
        y = G.nodes[node]["y"]
        z = G.nodes[node]["z"]
        node_x.append(x)
        node_y.append(y)
        node_z.append(z)
        node_sizes.append(G.nodes[node]["size"])  # Get the node size from the attribute
        if node in repos_data:
            num_repos = len([edge[1] for edge in G.edges() if edge[0] == node])
            if num_repos > 50:
                node_colors.append("green")  # Set green color for users with more than 50 repositories
            elif num_repos > 30:
                node_colors.append("blue")  # Set blue color for users with more than 30 repositories
            else:
                node_colors.append("red")  # Set orange or red color for users with less than 30 repositories

    node_trace = go.Scatter3d(
        x=node_x, y=node_y, z=node_z,
        mode='markers',
        hoverinfo='text',
        marker=dict(
            showscale=False,
            color=node_colors,
            size=node_sizes,
            colorbar=dict(
                thickness=15,
                title='Node Connections',
                xanchor='left',
                titleside='right'
            ),
            line_width=2))

    node_adjacencies = []
    node_text = []
    for node, adjacencies in G.adjacency():
        node_adjacencies.append(len(adjacencies))
        text = f"{node}<br>Connections: {len(adjacencies)}"
        if node in repos_data:
            text += f"<br>Email: {G.nodes[node]['email']}"
        node_text.append(text)

    node_trace.marker.color = node_adjacencies
    node_trace.text = node_text

    fig = go.Figure(data=[edge_trace, node_trace],
                    layout=go.Layout(
                        title='<br>GitHub Repository Network',
                        titlefont_size=16,
                        plot_bgcolor='rgb(17, 17, 17)',
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20, l=5, r=5, t=40),
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        hoverdistance=10,
                        hoverlabel=dict(
                            bgcolor="white",
                            font_size=14,
                            font_family="Arial"
                        )))

    fig.update_layout(scene=dict(aspectmode='data'))  # Set the aspect mode to 'data' for a spherical plot

    fig.update_scenes(
        xaxis_visible=False,
        yaxis_visible=False,
        zaxis_visible=False
    )

    plot_html = fig.to_html(full_html=False, config={'displayModeBar': True})

    return render_template('index.html', plot_html=plot_html)

if __name__ == '__main__':
    app.run(debug=True)
