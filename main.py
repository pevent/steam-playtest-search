import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import os
import numpy as np

def get_game_details(api_url):
    response = requests.get(api_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        pattern = 'Join the .* Playtest'
        matches = re.findall(pattern, str(soup))
        title = soup.find_all(id='appHubAppName')
        if title:
            title_text = title[0].text.strip()
        else:
            title_text = ""

        print('Title: ',title_text)
        if matches:
            return True,True,title_text
        else:
            return False,True,''
    else:
        print(f"Error accessing the API. Status code: {response.status_code}")
        return False,False,''

def get_appid_list(api_url):
    response = requests.get(api_url)

    if response.status_code == 200:
        data = response.json()
        app_ids = [app["appid"] for app in data["applist"]["apps"]]

        # Create a DataFrame from the app_ids list
        df = pd.DataFrame({"app_id": app_ids})

        # Save the DataFrame to a CSV file
        df.to_csv("export/appids.csv", index=False)
        print("App IDs saved to app_ids.csv")
    else:
        print("Failed to retrieve app IDs. Error:", response.status_code)


if __name__ == '__main__':

    apilist_url = "https://api.steampowered.com/ISteamApps/GetAppList/v2/"
    get_appid_list(apilist_url)

    df_appid = pd.read_csv("export/appids.csv")

    # Check if the file exists before reading
    if os.path.isfile("export/successful_appid.csv"):
        df_successful = pd.read_csv("export/successful_appid.csv")
    else:
        df_successful = pd.DataFrame({"app_id": []})
        print("CSV file does not exist. Empty DataFrame created.")

    successful_appid = df_successful['app_id'].values.tolist()
    playtest_appid = []
    appid = df_appid['app_id'].values.tolist()

    # Find the values in `appid` that are not present in `successful_appid`
    appid = np.setdiff1d(appid, successful_appid)

    df_playtest = pd.DataFrame(columns=['app_id', 'app_name'])

    for id in appid:
        print(id)
        api_url = f"https://store.steampowered.com/app/{id}"
        match,response,title=get_game_details(api_url)
        if response:
            successful_appid.append(id)
            df_successful = pd.concat([df_successful, pd.DataFrame({"app_id": [id]})], ignore_index=True)
            df_successful.to_csv("export/successful_appid.csv", index=False)
        if match:
            playtest_appid.append(id)
            df_playtest = pd.concat([df_playtest, pd.DataFrame({"app_id": [id], "app_name": [title]})], ignore_index=True)
            df_playtest.to_csv("export/playtest_appid.csv", index=False)

    print('All games that have playtest available have been found!')

