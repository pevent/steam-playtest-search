import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import os
import numpy as np
import datetime

def get_game_details(api_url):
    dt = datetime.datetime.now()
    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            pattern = 'Join the .* Playtest'
            matches = re.findall(pattern, str(soup))
            title = soup.find_all(id='appHubAppName')
            bts=soup.find_all('a', onclick="javascript:RequestPlaytestAccess();return false;")
            if title:
                title_text = title[0].text.strip()
            else:
                title_text = ""
            print('Title: ', title_text)
            if matches and len(bts)>0:
                return True, True, title_text, dt
            else:
                return False, True, '', dt
        else:
            print(f"Error accessing the API. Status code: {response.status_code}")
            return False, False, '', dt
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return False, False, '', dt
def get_appid_list(api_url):
    response = requests.get(api_url)

    if response.status_code == 200:
        data = response.json()
        app_ids = [app["appid"] for app in data["applist"]["apps"]]

        # Create a DataFrame from the app_ids list
        df = pd.DataFrame({"app_id": app_ids})

        # Save the DataFrame to a CSV file
        df.to_csv("export/appid.csv", index=False)
        print("App IDs saved to appid.csv")
    else:
        print("Failed to retrieve app IDs. Error:", response.status_code)


if __name__ == '__main__':

    # PATHs & URLs
    appid_csv_path = "export/appid.csv"
    successful_appid_csv_path = "export/successful_appid.csv"
    defective_appid_csv_path = "export/defective_appid.csv"
    playtest_appid_csv_path = "export/playtest_appid.csv"
    apilist_url = "https://api.steampowered.com/ISteamApps/GetAppList/v2/"

    # APP ID LIST
    get_appid_list(apilist_url)
    df_appid = pd.read_csv(appid_csv_path)

    # CHECKING FILES
    # Check if successful_appid.csv exists before reading
    if os.path.isfile(successful_appid_csv_path):
        df_successful = pd.read_csv(successful_appid_csv_path)
    else:
        df_successful = pd.DataFrame({"app_id": [],"last_time_checked": []}, dtype=int)
        print("successful_appid.csv does not exist. Empty DataFrame created.")

    # Check if defective_appid.csv exists before reading
    if os.path.isfile(defective_appid_csv_path):
        df_defective = pd.read_csv(defective_appid_csv_path)
    else:
        df_defective = pd.DataFrame({"app_id": [],"last_time_checked": []}, dtype=int)
        print("defective_appid.csv does not exist. Empty DataFrame created.")

    # Check if playtest_appid.csv exists before reading
    if os.path.isfile(playtest_appid_csv_path):
        df_playtest = pd.read_csv(playtest_appid_csv_path)
    else:
        df_playtest = pd.DataFrame({"app_id": [], "app_name": [], "last_time_checked": []}, dtype=int)
        print("playtest_appid.csv does not exist. Empty DataFrame created.")

    # TURNING DATAFRAMES INTO LISTS
    successful_appid = df_successful[['app_id', 'last_time_checked']].values.tolist()
    defective_appid = df_defective[['app_id', 'last_time_checked']].values.tolist()
    playtest_appid = df_playtest[['app_id', 'app_name', 'last_time_checked']].values.tolist()
    appid = df_appid['app_id'].values.tolist()

    # CHECKING WHAT GAMES WERE ALREADY VERIFIED
    appid = [id for id in appid if id not in [row[0] for row in successful_appid]]
    appid = [id for id in appid if id not in [row[0] for row in defective_appid]]
    appid = [id for id in appid if id not in [row[0] for row in playtest_appid]]

    # LOOP FOR EACH APP ID
    for id in appid:
        print(id)
        api_url = f"https://store.steampowered.com/app/{id}"
        match,response,title,dt=get_game_details(api_url)
        if response:
            successful_appid.append(id)
            df_successful = pd.concat([df_successful, pd.DataFrame({"app_id": [id],"last_time_checked": [dt.strftime("%Y-%m-%d %H:%M:%S")]})], ignore_index=True)
            df_successful.to_csv(successful_appid_csv_path, index=False)
        if match:
            playtest_appid.append(id)
            df_playtest = pd.concat([df_playtest, pd.DataFrame({"app_id": [id], "app_name": [title],"last_time_checked": [dt.strftime("%Y-%m-%d %H:%M:%S")]})], ignore_index=True)
            df_playtest.to_csv(playtest_appid_csv_path, index=False)
        if response is False and match is False:
            defective_appid.append(id)
            df_defective = pd.concat([df_defective, pd.DataFrame({"app_id": [id],"last_time_checked": [dt.strftime("%Y-%m-%d %H:%M:%S")]})], ignore_index=True)
            df_defective.to_csv(defective_appid_csv_path, index=False)

    print('All games that have playtest available have been found!')
