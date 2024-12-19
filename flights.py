import requests
import pandas as pd
import time
import sqlite3
from datetime import datetime, timedelta

# Found this cool OpenSky API that gives real-time flight data!
API_URL = "https://opensky-network.org/api/flights/all"

def extract():
    """
    Getting live flight data from OpenSky - this API is amazing for tracking flights worldwide!
    I'm pulling the last 2 hours of data because that gives us a good snapshot without overwhelming the system.
    """
    try:
        # Setting up a 2-hour window - found that this gives us enough data to work with
        end_time = int(time.time())
        begin_time = end_time - 7200  # 2 hours of flight data should be plenty!
        
        params = {
            "begin": begin_time,
            "end": end_time
        }
        
        # Fingers crossed the API is responsive today...
        response = requests.get(API_URL, params=params)
        
        if response.status_code == 200:
            flights = pd.DataFrame(response.json())
            
            print(f"Successfully fetched {len(flights)} flight records")
            print("\nDataFrame Columns:")
            print(flights.columns)
            print("\nDataFrame Head:")
            print(flights.head())
            print("\nDataFrame Info:")
            print(flights.info())
            
            return flights
            
        else:
            print(f"Error fetching data: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None

def transform(flights):
    """
    Time to clean up this messy flight data! 
    The raw data has some unnecessary columns and weird formatting - let's make it analysis-ready.
    """
    try:
        if flights is None:
            return None
            
        # Always work with a copy - learned this the hard way after messing up my original data once!
        df = flights.copy()
        
        # These columns were giving me a headache - they're just noise for our analysis
        columns_to_drop = [
            'estDepartureAirportHorizDistance',
            'estDepartureAirportVertDistance',
            'estArrivalAirportHorizDistance',
            'estArrivalAirportVertDistance',
            'departureAirportCandidatesCount',
            'arrivalAirportCandidatesCount'
        ]
        df = df.drop(columns=columns_to_drop, errors='ignore')
        
        # No point keeping flights with unknown airports - can't analyze routes without this!
        df = df.dropna(subset=['estDepartureAirport', 'estArrivalAirport'])
        
        # Converting Unix timestamps to something humans can actually read
        df['firstSeen'] = pd.to_datetime(df['firstSeen'], unit='s')
        df['lastSeen'] = pd.to_datetime(df['lastSeen'], unit='s')
        
        # Making column names more intuitive - my future self will thank me
        column_mapping = {
            'callsign': 'flightnumber',
            'estDepartureAirport': 'DepartureAirport',
            'estArrivalAirport': 'ArrivalAirport',
            'firstSeen': 'approxDepartureTime',
            'lastSeen': 'approxArrivalTime'
        }
        df = df.rename(columns=column_mapping)
        
        # Making sure our datetime columns are in the right format for time-series analysis later
        df['approxDepartureTime'] = df['approxDepartureTime'].astype('datetime64[ns]')
        df['approxArrivalTime'] = df['approxArrivalTime'].astype('datetime64[ns]')
        
        print("\nTransformation completed successfully")
        print(f"Records after processing: {len(df)}")
        print("\nTransformed DataFrame Columns:")
        print(df.columns)
        print("\nTransformed DataFrame Head:")
        print(df.head())
        print("\nDateTime columns info:")
        print(df[['approxDepartureTime', 'approxArrivalTime']].dtypes)
        
        return df
        
    except Exception as e:
        print(f"Error during transformation: {str(e)}")
        return None

def load(df):
    """
    Final step - getting this clean data into our SQLite database!
    I'm using SQLite because it's perfect for this size of data and super easy to work with.
    """
    try:
        if df is None:
            return False
            
        # Connecting to our trusty SQLite database
        conn = sqlite3.connect('sky.db')
        
        # Out with the old, in with the new - replacing existing data to avoid duplicates
        df.to_sql('flights', conn, if_exists='replace', index=False)
        
        conn.close()
        
        print("\nData successfully loaded into sky.db in table 'flights'")
        return True
        
    except Exception as e:
        print(f"Error during database loading: {str(e)}")
        return False

if __name__ == "__main__":
    # Get current timestamp for logging
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n[{current_time}] Starting ETL process...")
    
    # Extract the data
    raw_flights = extract()
    
    # Transform the data
    if raw_flights is not None:
        processed_flights = transform(raw_flights)
        
        # Load the data
        if processed_flights is not None:
            if load(processed_flights):
                print(f"[{current_time}] ETL process completed successfully")
            else:
                print(f"[{current_time}] ETL process failed during loading")