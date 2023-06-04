import sys
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import os
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


if __name__ == '__main__':

    # PATHs & URLs
    rechecked_appid_csv_path = "export/rechecked_appid.csv"
    defective_appid_csv_path = "export/defective_appid.csv"
    playtest_appid_csv_path = "export/playtest_appid.csv"

    # CHECKING FILES
    # Check if playtest_appid.csv exists before reading
    if os.path.isfile(playtest_appid_csv_path):
        df_playtest = pd.read_csv(playtest_appid_csv_path)
    else:
        print("playtest_appid.csv does not exist.\nYou need playtest_appid.csv for this script to work!")
        sys.exit()

    # Check if rechecked_appid.csv exists before reading
    if os.path.isfile(rechecked_appid_csv_path):
        df_playtest = pd.read_csv(rechecked_appid_csv_path)
        df_rechecked_appid = pd.DataFrame({"app_id": [], "app_name": [], "last_time_checked": []}, dtype=int)
    else:
        df_rechecked_appid = pd.DataFrame({"app_id": [], "app_name": [],"last_time_checked": []}, dtype=int)
        print("successful_appid.csv does not exist. Empty DataFrame created.")

    # Check if defective_appid.csv exists before reading
    if os.path.isfile(defective_appid_csv_path):
        df_defective = pd.read_csv(defective_appid_csv_path)
    else:
        df_defective = pd.DataFrame({"app_id": [],"last_time_checked": []}, dtype=int)
        print("defective_appid.csv does not exist. Empty DataFrame created.")



    # TURNING DATAFRAMES INTO LISTS
    playtest_appid = df_playtest[['app_id', 'app_name', 'last_time_checked']].values.tolist()


    # LOOP FOR EACH APP ID
    for id in playtest_appid:
        print(id)
        api_url = f"https://store.steampowered.com/app/{id}"
        match,response,title,dt=get_game_details(api_url)
        if response:
            df_playtest = pd.concat([df_playtest, pd.DataFrame({"app_id": [id],"app_name": [title],"last_time_checked": [dt.strftime("%Y-%m-%d %H:%M:%S")]})], ignore_index=True)
            df_playtest.to_csv(playtest_appid_csv_path, index=False)
        if match:
            df_rechecked_appid = pd.concat([df_rechecked_appid, pd.DataFrame({"app_id": [id], "app_name": [title],"last_time_checked": [dt.strftime("%Y-%m-%d %H:%M:%S")]})], ignore_index=True)
            df_rechecked_appid.to_csv(rechecked_appid_csv_path, index=False)
        if response is False and match is False:
            df_defective = pd.concat([df_defective, pd.DataFrame({"app_id": [id],"last_time_checked": [dt.strftime("%Y-%m-%d %H:%M:%S")]})], ignore_index=True)
            df_defective.to_csv(defective_appid_csv_path, index=False)

    print('All games that have playtest available have been found!')
