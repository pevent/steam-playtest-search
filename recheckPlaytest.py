import sys

import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import os
import datetime
import concurrent.futures
import time

def get_game_details(api_url,appid):
    dt = datetime.datetime.now()
    try:
        response = requests.get(api_url+appid)
        if response.status_code == 200:
            # Gets HTML of Steam page
            soup = BeautifulSoup(response.content, "html.parser")
            # Regular Expression that every playtest will have
            pattern = 'Join the .* Playtest'
            matches = re.findall(pattern, str(soup))
            # Get element a from page with the atribute onclick, every playtest seems to have this
            bts = soup.find_all('a', onclick="javascript:RequestPlaytestAccess();return false;")

            # Find the specific div
            description = soup.find('div', class_="game_description_snippet")

            if matches and len(bts)>0:
                return True, True,description, dt
            else:
                return False, True, '', dt
        else:
            print(f"Error accessing the API. Status code: {response.status_code}")
            return False, False,'',  dt
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return False, False, '',  dt

def process_app(app):
    app_id = app[0]
    app_name = app[1]

    # Call get_game_details
    match, response, description, dt = get_game_details(api_url, str(app_id))

    # match == True if regex and element a were found
    # response == True if response == 200
    # if both False, means response != 200 or there was an error accessing the page
    if match==True:
        df_rechecked_appid = pd.DataFrame({"ID": [app_id], "Title": [app_name], "Description": [description], "Last_time_checked": [dt.strftime("%Y-%m-%d %H:%M:%S")]})
        return df_rechecked_appid, "rechecked"
    elif response==False and match==False:
        df_defective = pd.DataFrame({"app_id": [app_id],  "last_time_checked": [dt.strftime("%Y-%m-%d %H:%M:%S")]})
        return df_defective, "defective"
    return pd.DataFrame,"nothing"

if __name__ == '__main__':

    # PATHs & URLs
    rechecked_appid_csv_path = "export/playtest_appid_rechecked.csv"
    successful_appid_csv_path = "export/successful_appid.csv"
    defective_appid_csv_path = "export/defective_appid.csv"
    playtest_appid_csv_path = "export/playtest_appid.csv"
    apilist_url = "https://api.steampowered.com/ISteamApps/GetAppList/v2/"
    api_url = "https://store.steampowered.com/app/"

    # CHECKING FILES
    # Check if playtest_appid.csv exists before reading
    if os.path.isfile(playtest_appid_csv_path):
        df_playtest = pd.read_csv(playtest_appid_csv_path)
    else:
        print("playtest_appid.csv does not exist.\nYou need playtest_appid.csv for this script to work!")
        sys.exit()

    # Check if rechecked_appid.csv exists before reading
    if os.path.isfile(rechecked_appid_csv_path):
        df_rechecked_appid = pd.read_csv(rechecked_appid_csv_path)
    else:
        df_rechecked_appid = pd.DataFrame({"ID": [], "Title": [], "Description": [], "Last_time_checked":[]}, dtype=int)
        print("playtest_appid_rechecked.csv does not exist. Empty DataFrame created.")

    # Check if defective_appid.csv exists before reading
    if os.path.isfile(defective_appid_csv_path):
        df_defective = pd.read_csv(defective_appid_csv_path)
    else:
        df_defective = pd.DataFrame({"app_id": [],"last_time_checked": []}, dtype=int)
        print("defective_appid.csv does not exist. Empty DataFrame created.")


    # TURNING DATAFRAMES INTO LISTS
    playtest_appid = df_playtest[['app_id', 'app_name', 'last_time_checked']].values.tolist()
    rechecked_appid = df_rechecked_appid[['ID', 'Title', 'Description', 'Last_time_checked']].values.tolist()

    batch_size = 2  # Initial concurrency level
    response_times = []  # List to store the response times for each batch

    # Execute asynchronous call function process_app
    with concurrent.futures.ThreadPoolExecutor(max_workers=batch_size) as executor:
        # Get 10 apps
        for batch_index in range(0, len(playtest_appid), batch_size):
            # batch is the position batch_index to batch_index + batch_size (10) from appid
            batch = playtest_appid[batch_index:batch_index + batch_size]

            # Record the start time before making the requests
            start_time = time.time()

            # Call process_app for each app in batch
            results = executor.map(process_app, batch)

            # Store the response time for this batch
            response_time = time.time() - start_time
            response_times.append(response_time)

            print(response_times)

            # To know which is activated to know which DF needs to be stored
            re = False
            defe = False

            # For each result from each function call
            for result, indicator in results:
                # Concatenate result to the pre-existing DF
                if indicator == "rechecked":
                    print("Rechecked")
                    df_rechecked_appid = pd.concat([df_rechecked_appid, result], ignore_index=True)
                    re = True
                elif indicator == "defective":
                    print("Defective")
                    df_defective = pd.concat([df_defective, result], ignore_index=True)
                    defe = True

            # Save the DataFrames to CSV files)
            if re:
                df_rechecked_appid.to_csv(rechecked_appid_csv_path, index=False)
            if defe:
                df_defective.to_csv(defective_appid_csv_path, index=False)

            # Clear the response times list
            response_times = []

print('All games that have playtest available have been found!')
