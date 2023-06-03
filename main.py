import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import os
import datetime
import concurrent.futures

# Function to get Web details from Steam page
def get_game_details(api_url,appid):
    dt = datetime.datetime.now()
    # try for cases of error
    try:
        response = requests.get(api_url+appid)
        if response.status_code == 200:
            # Gets HTML of Steam page
            soup = BeautifulSoup(response.content, "html.parser")
            # Regular Expression that every playtest will have
            pattern = 'Join the .* Playtest'
            matches = re.findall(pattern, str(soup))
            # Get element a from page with the atribute onclick, every playtest seems to have this
            bts=soup.find_all('a', onclick="javascript:RequestPlaytestAccess();return false;")

            if matches and len(bts)>0:
                return True, True, dt
            else:
                return False, True, dt
        else:
            print(f"Error accessing the API. Status code: {response.status_code}")
            return False, False, dt
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return False, False, dt

# Function to get all app ids in Steam
def get_appid_list(api_url):
    response = requests.get(api_url)

    if response.status_code == 200:
        data = response.json()
        app_ids = [(app["appid"], app["name"]) for app in data["applist"]["apps"]]
        # Create a DataFrame from the app_ids list
        df = pd.DataFrame(app_ids, columns=["app_id", "app_name"])

        # Save the DataFrame to a CSV file
        df.to_csv("export/appid.csv", index=False)
        print("App IDs saved to appid.csv")
    else:
        print("Failed to retrieve app IDs. Error:", response.status_code)

# Function to process app ID and return the results
def process_app(app):
    app_id = app[0]
    app_name = app[1]

    # Call get_game_details
    match, response, dt = get_game_details(api_url, str(app_id))

    # match == True if regex and element a were found
    # response == True if response == 200
    # if both False, means response != 200 or there was an error accessing the page
    if match==True:
        df_playtest = pd.DataFrame({"app_id": [app_id], "app_name": [app_name],"last_time_checked": [dt.strftime("%Y-%m-%d %H:%M:%S")]})
        return df_playtest, "playtest"
    elif response==True:
        df_successful = pd.DataFrame({"app_id": [app_id], "last_time_checked": [dt.strftime("%Y-%m-%d %H:%M:%S")]})
        return df_successful, "successful"
    else:
        df_defective = pd.DataFrame({"app_id": [app_id], "last_time_checked": [dt.strftime("%Y-%m-%d %H:%M:%S")]})
        return df_defective, "defective"

if __name__ == '__main__':

    # PATHs & URLs
    appid_csv_path = "export/appid.csv"
    successful_appid_csv_path = "export/successful_appid.csv"
    defective_appid_csv_path = "export/defective_appid.csv"
    playtest_appid_csv_path = "export/playtest_appid.csv"
    apilist_url = "https://api.steampowered.com/ISteamApps/GetAppList/v2/"
    api_url = "https://store.steampowered.com/app/"

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
    appid = df_appid[['app_id', 'app_name']].values.tolist()

     # Convert inner lists to tuples in successful_appid, defective_appid, and playtest_appid
    successful_appid = [row[0] for row in successful_appid]
    defective_appid = [row[0] for row in defective_appid]
    playtest_appid = [row[0] for row in playtest_appid]

    # Combine all lists into a single list
    combined = successful_appid + defective_appid + playtest_appid
    filtered_set = set(combined)

    # Filter appid list to exclude already succesful, defective, and playtest games
    appid = [id for id in appid if id[0] not in filtered_set]

    batch_size = 10 # Concurrency Limit

    # Execute asynchronous call function process_app
    with concurrent.futures.ThreadPoolExecutor(max_workers=batch_size) as executor:
        # Get 10 apps
        for batch_index in range(0, len(appid), batch_size):
            # batch is the position batch_index to batch_index + batch_size (10) from appid
            batch = appid[batch_index:batch_index + batch_size]
            # Call process_app for each app in batch
            results = executor.map(process_app, batch)
            # To know which is activated to know which DF needs to be stored
            succ = False
            pt = False
            defe = False
            # For each result from each function call
            for result, indicator in results:
                # Concatenate result to the pre-existing DF
                if indicator == "successful":
                    print("Successful")
                    df_successful = pd.concat([df_successful, result], ignore_index=True)
                    succ = True
                elif indicator == "playtest":
                    print("Playtest")
                    df_playtest = pd.concat([df_playtest, result], ignore_index=True)
                    pt = True
                elif indicator == "defective":
                    print("Defective")
                    df_defective = pd.concat([df_defective, result],ignore_index=True)
                    defe = True

            # Save the DataFrames to CSV files
            if succ:
                df_successful.to_csv(successful_appid_csv_path, index=False)
            if pt:
                df_playtest.to_csv(playtest_appid_csv_path, index=False)
            if defe:
                df_defective.to_csv(defective_appid_csv_path, index=False)


    print('All games that have playtest available have been found!')
