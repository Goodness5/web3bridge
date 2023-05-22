# import csv
# import requests
# import json
# import matplotlib.pyplot as plt

# # Function to fetch GitHub repositories for a given username
# def get_user_repos(username):
#     url = f"https://api.github.com/users/{username}/repos"
#     response = requests.get(url)
# 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

#     if response.status_code == 200:
#         repos = response.json()
#         return repos  # Return the repository data instead of printing
#     else:
#         print("Error:", response.status_code)
#         return []  # Return an empty list in case of an error

# csv_file = "./data.csv"
# solidity_repos = []  # List to store Solidity repositories

# with open(csv_file, 'r') as file:
#     csv_reader = csv.reader(file)
#     header = next(csv_reader)  # Skip header row
#     print('Starting')

#     for row in csv_reader:
#         if len(row) >= 2:  # Check if row has at least 2 elements
#             email = row[1]
#             username = row[0]
#             github_repos = get_user_repos(username)  # Fetch repository data
            
#             # Filter and append repositories with Solidity as the language
#             for repo in github_repos:
#                 if repo["language"] == "Solidity":
#                     solidity_repos.append(repo)
                    
#     # Write the Solidity repositories data to a JSON file
#     json_file = "solidity_repos.json"
#     with open(json_file, 'w') as f:
#         json.dump(solidity_repos, f, indent=4)

#     print(f"Solidity repositories data has been written to {json_file}")


# json_file = "solidity_repos.json"
# with open(json_file, 'r') as f:
#     solidity_repos = json.load(f)

# # Count the number of Solidity repositories for each user
# repo_counts = {}
# for repo in solidity_repos:
#     user = repo["owner"]["login"]
#     if user in repo_counts:
#         repo_counts[user] += 1
#     else:
#         repo_counts[user] = 1

# # Extract users and corresponding repository counts
# users = list(repo_counts.keys())
# counts = list(repo_counts.values())

# # Plot the bar chart
# plt.bar(users, counts)
# plt.xlabel("User")
# plt.ylabel("Number of Solidity Repositories")
# plt.title("Solidity Repositories by User")
# plt.xticks(rotation=45)
# plt.show()