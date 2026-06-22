import requests
import pandas as pd

def fetch_live_nav_data(scheme_codes):
    for code in scheme_codes:
        url = f"https://api.mfapi.in/mf/{code}"
        response = requests.get(url)
        data = response.json()
        nav_data = data["data"]
        df = pd.DataFrame(nav_data)
        file_path="C:/Users/JAY MISTRY/OneDrive/Desktop/Bluestock_mf_capstone/data/raw"
        df.to_csv(f"{file_path}/{data['meta']['scheme_name']}_nav_data.csv", index=False)
        
if __name__ == "__main__":
    scheme_codes= [125497,119551,120503,118632,119092,120841]        
    fetch_live_nav_data(scheme_codes)
