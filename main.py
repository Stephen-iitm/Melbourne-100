import requests
import pandas as pd
import os

from tqdm import tqdm

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
HEADERS = {'Authorization': f'token {GITHUB_TOKEN}'}

def fetch_users():
    users = []
    url = "https://api.github.com/search/users?q=location:Melbourne+followers:>100"
    while url:
        response = requests.get(url, headers=HEADERS)
        data = response.json()
        users.extend(data.get('items', []))

        # Check for pagination in the 'Link' header
        links = response.headers.get('Link', None)
        if links:
            for link in links.split(','):
                if 'rel="next"' in link:
                    url = link[link.find('<') + 1:link.find('>')]
                    break
            else:
                url = None  # No 'next' link found
        else:
            url = None  # No 'Link' header, thus no pagination
    print("fetch_users")
    return users

def clean_company(company):
    if company:
        return company.strip().lstrip('@').upper()
    return ''

def process_user_data(users):
    user_data = []
    for user in users:
        user_detail = requests.get(user['url'], headers=HEADERS).json()
        user_data.append({
            'login': user_detail.get('login', ''),
            'name': user_detail.get('name', ''),
            'company': clean_company(user_detail.get('company', '')),
            'location': user_detail.get('location', ''),
            'email': user_detail.get('email', ''),
            'hireable': user_detail.get('hireable', ''),
            'bio': user_detail.get('bio', ''),
            'public_repos': user_detail.get('public_repos', 0),
            'followers': user_detail.get('followers', 0),
            'following': user_detail.get('following', 0),
            'created_at': user_detail.get('created_at', '')
        })
    print("process_user_data")
    return pd.DataFrame(user_data)



def fetch_repositories(user):
    repos = []
    url = f"https://api.github.com/users/{user}/repos?per_page=100"
    with tqdm(total=500, desc=f"Fetching repos for {user}", leave=False) as pbar:
        while url and len(repos) < 500:
            response = requests.get(url, headers=HEADERS)
            if response.status_code != 200:
                print(f"Failed to fetch repos for {user}: {response.status_code}")
                break
            repo_page = response.json()
            repos.extend(repo_page)
            pbar.update(len(repo_page))

            # Handle pagination via the 'Link' header
            links = response.headers.get('Link', None)
            if links:
                for link in links.split(','):
                    if 'rel="next"' in link:
                        url = link[link.find('<') + 1:link.find('>')]
                        break
                else:
                    url = None  # No 'next' link found
            else:
                url = None  # No 'Link' header, thus no pagination
    return repos

def process_repo_data(users_df):
    repo_data = []
    for login in tqdm(users_df['login'], desc="Processing users"):
        repos = fetch_repositories(login)
        for repo in repos:
            license_name = repo.get('license', {}).get('key', '') if repo.get('license') else ''
            repo_data.append({
                'login': login,
                'full_name': repo.get('full_name', ''),
                'created_at': repo.get('created_at', ''),
                'stargazers_count': repo.get('stargazers_count', 0),
                'watchers_count': repo.get('watchers_count', 0),
                'language': repo.get('language', ''),
                'has_projects': repo.get('has_projects', False),
                'has_wiki': repo.get('has_wiki', False),
                'license_name': license_name
            })
    return pd.DataFrame(repo_data)


if __name__ == '__main__':
    # Fetch and process users data
    print("started")
    users = fetch_users()
    users_df = process_user_data(users)
    users_df.to_csv('users.csv', index=False)
    print("Users data saved to users.csv")


    # repositories data
    repos_df = process_repo_data(users_df)
    repos_df.to_csv('repositories.csv', index=False)
    print("Repositories data saved to repositories.csv")

