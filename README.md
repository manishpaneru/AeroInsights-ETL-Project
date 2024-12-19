# OpenSky Flight Data ETL Pipeline 🛩️

A Python-based ETL (Extract, Transform, Load) pipeline that fetches real-time flight data from the OpenSky Network API and stores it in a SQLite database.

## Overview

This project creates an automated pipeline to:
- Extract flight data from OpenSky Network's REST API
- Transform the data by cleaning and restructuring it
- Load the processed data into a SQLite database

## Features

- Real-time flight data collection
- Data cleaning and standardization
- Automated timestamp conversions
- SQLite database storage
- Task Scheduler compatible
- Detailed logging

## Prerequisites

- Python 3.x
- Required Python packages:
  ```
  pandas
  requests
  sqlite3
  ```

## Installation

1. Clone this repository:
   ```bash
   git clone [your-repository-url]
   ```

2. Install required packages:
   ```bash
   pip install pandas requests
   ```

## Project Structure

```
opensky_ETL/
│
├── fetch_flights.py    # Main ETL script
├── sky.db             # SQLite database (created on first run)
└── README.md          # This file
```

## How It Works

The ETL process is divided into three main functions:

1. **Extract (`extract()`):**
   - Fetches last 2 hours of flight data from OpenSky API
   - Converts raw JSON data to pandas DataFrame
   - Handles API connection errors

2. **Transform (`transform()`):**
   - Removes unnecessary columns
   - Handles missing values
   - Converts timestamps to datetime format
   - Renames columns for clarity
   - Standardizes data types

3. **Load (`load()`):**
   - Connects to SQLite database
   - Creates/updates 'flights' table
   - Stores processed data

## Data Structure

The processed data includes:
- Flight number
- Departure/Arrival airports
- Departure/Arrival times
- Other flight-specific information

## Automation Setup

### Using Windows Task Scheduler:

1. Open Task Scheduler
2. Create a new Basic Task
3. Set trigger to recur every 3 minutes
4. Action: Start a program
5. Program/script: `python`
6. Add arguments: `path_to_your_script/fetch_flights.py`
7. Start in: `path_to_your_script_directory`

## Error Handling

The script includes comprehensive error handling for:
- API connection issues
- Data transformation errors
- Database connection problems
- Each step logs its status and any errors

## Output

- Console logs showing ETL process status
- SQLite database (`sky.db`) containing flight data
- Timestamp-based execution logs

## Contributing

Feel free to fork this repository and submit pull requests. For major changes, please open an issue first to discuss what you would like to change.

## License

[Your chosen license]

## Acknowledgments

- [OpenSky Network](https://opensky-network.org/) for providing the flight data API
- Built with ❤️ for aviation data enthusiasts 