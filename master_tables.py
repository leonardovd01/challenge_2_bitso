
import requests
import pandas as pd
from datetime import datetime
import io
import zipfile

# URLs for the CSV files
BASE_URL = "https://raw.githubusercontent.com/IMARVI/sr_de_challenge/main/"
DEPOSIT_URL = BASE_URL + "deposit_sample_data.csv.zip"
EVENT_URL = BASE_URL + "event_sample_data.csv"
USER_URL = BASE_URL + "user_id_sample_data.csv"
WITHDRAWAL_URL = BASE_URL + "withdrawals_sample_data.csv"

def download_and_unzip(url):
    """
    Download a zip file from a URL and read the CSV within it.
    
    Args:
        url (str): URL of the zip file containing the CSV.
        
    Returns:
        pd.DataFrame: DataFrame containing the CSV data.
    """
    response = requests.get(url)
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        for filename in z.namelist():
            with z.open(filename) as f:
                return pd.read_csv(f)

def normalize_datetime(dt_series):
    """
    Convert datetime series to UTC and make timezone-naive.
    
    Args:
        dt_series (pd.Series): Series of datetime values.
        
    Returns:
        pd.Series: Normalized datetime series.
    """
    return pd.to_datetime(dt_series, utc=True).dt.tz_convert(None)

def load_and_transform_data():
    """
    Load and transform data from URLs.
    
    Returns:
        dict: Transformed DataFrames.
    """
    # Download and read each CSV file
    deposit_df = download_and_unzip(DEPOSIT_URL)
    event_df = pd.read_csv(EVENT_URL)
    user_df = pd.read_csv(USER_URL)
    withdrawal_df = pd.read_csv(WITHDRAWAL_URL)
    
    # Transformation for user_df
    user_df.drop_duplicates(subset='user_id', inplace=True)
    user_df.dropna(inplace=True)

    # Transformation for deposit_df
    deposit_df.drop_duplicates(inplace=True)
    deposit_df.dropna(subset='amount', inplace=True)
    deposit_df['event_timestamp'] = pd.to_datetime(deposit_df['event_timestamp'], format='mixed')

    # Transformation for withdrawal_df
    withdrawal_df.drop_duplicates(inplace=True)
    withdrawal_df.dropna(subset='amount', inplace=True)
    withdrawal_df['event_timestamp'] = pd.to_datetime(withdrawal_df['event_timestamp'], format='mixed')

    # Transformation for event_df
    event_df.drop_duplicates(inplace=True)
    event_df.dropna(inplace=True)
    event_df['event_timestamp'] = pd.to_datetime(event_df['event_timestamp'])

    # Normalize timestamps and make them naive
    deposit_df['event_timestamp'] = normalize_datetime(deposit_df['event_timestamp'])
    withdrawal_df['event_timestamp'] = normalize_datetime(withdrawal_df['event_timestamp'])
    event_df['event_timestamp'] = normalize_datetime(event_df['event_timestamp'])

    return {
        'users': user_df,
        'deposits': deposit_df,
        'withdrawals': withdrawal_df,
        'events': event_df
    }

def create_dates_table(deposits, withdrawals, events):
    """
    Create a Dates table from event timestamps.
    
    Args:
        deposits (pd.DataFrame): Deposits DataFrame.
        withdrawals (pd.DataFrame): Withdrawals DataFrame.
        events (pd.DataFrame): Events DataFrame.
        
    Returns:
        pd.DataFrame: Dates DataFrame with DateID mapping.
    """
    dates_data = pd.concat([deposits['event_timestamp'], withdrawals['event_timestamp'], events['event_timestamp']]).unique()
    dates = pd.to_datetime(dates_data).normalize()
    dates_df = pd.DataFrame({
        'Date': dates,
        'DayOfWeek': dates.dayofweek,
        'Month': dates.month,
        'Year': dates.year
    })

    dates_df.drop_duplicates(inplace=True)
    dates_df.reset_index(drop=True, inplace=True)
    dates_df['DateID'] = dates_df.index + 1

    return dates_df

def map_date_ids(df, dates_df, date_column='event_timestamp'):
    """
    Map DateIDs back to the original tables.
    
    Args:
        df (pd.DataFrame): DataFrame containing the date_column.
        dates_df (pd.DataFrame): Dates DataFrame with DateID mapping.
        date_column (str): Column name of the datetime column to map.
        
    Returns:
        pd.DataFrame: DataFrame with DateID mapped.
    """
    df['DateID'] = df[date_column].map(lambda x: x.normalize()).map(dates_df.set_index('Date')['DateID'])
    return df

def create_transactions_table(deposits, withdrawals):
    """
    Create a consolidated Transactions table from deposits and withdrawals.
    
    Args:
        deposits (pd.DataFrame): Deposits DataFrame.
        withdrawals (pd.DataFrame): Withdrawals DataFrame.
        
    Returns:
        pd.DataFrame: Consolidated Transactions DataFrame.
    """
    deposits['TransID'] = 'D' + deposits['id'].astype(str)
    withdrawals['TransID'] = 'W' + withdrawals['id'].astype(str)

    transactions = pd.concat([
        deposits[['TransID', 'DateID', 'user_id', 'amount', 'currency', 'tx_status']].assign(TransType='deposit'),
        withdrawals[['TransID', 'DateID', 'user_id', 'amount', 'currency', 'tx_status']].assign(TransType='withdrawal')
    ])

    transactions = transactions[transactions['tx_status'] == 'complete']
    transactions.rename(columns={'id': 'TransID'}, inplace=True)
    return transactions

def main():
    # Load and transform data
    data = load_and_transform_data()

    # Create Dates table
    dates_df = create_dates_table(data['deposits'], data['withdrawals'], data['events'])

    # Map DateIDs
    data['deposits'] = map_date_ids(data['deposits'], dates_df)
    data['withdrawals'] = map_date_ids(data['withdrawals'], dates_df)
    data['events'] = map_date_ids(data['events'], dates_df)

    # Create Transactions table
    transactions = create_transactions_table(data['deposits'], data['withdrawals'])

    # Selecting the final columns of each table to export to csv
    transactions_vf = transactions[['TransID', 'DateID', 'user_id', 'amount', 'currency', 'TransType']]
    deposits_vf = data['deposits'][['TransID', 'user_id', 'event_timestamp', 'tx_status']]
    withdrawals_vf = data['withdrawals'][['TransID', 'user_id', 'event_timestamp', 'interface', 'tx_status']]
    events_vf = data['events'][['id', 'event_timestamp', 'user_id', 'event_name', 'DateID']]
    users_vf = data['users']

    # Save to CSV and print confirmation
    transactions_vf.to_csv('transactions_vf.csv', index=False)
    print("transactions_vf.csv has been saved.")
    
    deposits_vf.to_csv('deposits_vf.csv', index=False)
    print("deposits_vf.csv has been saved.")
    
    withdrawals_vf.to_csv('withdrawals_vf.csv', index=False)
    print("withdrawals_vf.csv has been saved.")
    
    events_vf.to_csv('events_vf.csv', index=False)
    print("events_vf.csv has been saved.")
    
    users_vf.to_csv('users_vf.csv', index=False)
    print("users_vf.csv has been saved.")
    
    dates_df.to_csv('dates_vf.csv', index=False)
    print("dates_df.csv has been saved.")

if __name__ == "__main__":
    main()
