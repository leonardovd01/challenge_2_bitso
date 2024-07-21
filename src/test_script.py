import unittest
from unittest.mock import patch, mock_open
import pandas as pd
import io
import zipfile

# We import all the functions from master_tables
from src.master_tables import (
    download_and_unzip,
    normalize_datetime,
    load_and_transform_data,
    create_dates_table,
    map_date_ids,
    create_transactions_table
)



class TestMasterTables(unittest.TestCase):
    
    @patch('requests.get')
    def test_download_and_unzip(self, mock_get):
        # Create a mock response object with a zip file containing a CSV
        mock_csv_content = 'id,amount,event_timestamp\n1,100.0,2023-01-01T00:00:00Z\n'
        mock_zip_content = io.BytesIO()
        with zipfile.ZipFile(mock_zip_content, 'w') as zf:
            zf.writestr('test.csv', mock_csv_content)
        mock_zip_content.seek(0)
        
        # Mock the requests.get to return the mock response
        mock_get.return_value.content = mock_zip_content.getvalue()
        
        # Call the function
        df = download_and_unzip('mock_url')
        
        # Check the DataFrame content
        expected_df = pd.read_csv(io.StringIO(mock_csv_content))
        pd.testing.assert_frame_equal(df, expected_df)
        print("test_download_and_unzip passed")


    def test_normalize_datetime(self):
        dt_series = pd.Series(['2023-01-01T00:00:00Z', '2023-01-02T12:00:00Z'])
        expected_series = pd.Series([pd.Timestamp('2023-01-01 00:00:00'), pd.Timestamp('2023-01-02 12:00:00')])
        normalized_series = normalize_datetime(dt_series)
        pd.testing.assert_series_equal(normalized_series, expected_series)
        print("test_normalize_datetime passed")

    @patch('master_tables.download_and_unzip')
    @patch('master_tables.pd.read_csv')
    def test_load_and_transform_data(self, mock_read_csv, mock_download_and_unzip):
        # Mock the DataFrames returned by download_and_unzip and read_csv
        mock_deposit_df = pd.DataFrame({'id': [1], 'amount': [100.0], 'event_timestamp': ['2023-01-01T00:00:00Z']})
        mock_event_df = pd.DataFrame({'id': [1], 'event_timestamp': ['2023-01-01T00:00:00Z']})
        mock_user_df = pd.DataFrame({'user_id': [1]})
        mock_withdrawal_df = pd.DataFrame({'id': [1], 'amount': [50.0], 'event_timestamp': ['2023-01-01T00:00:00Z']})

        mock_download_and_unzip.side_effect = [mock_deposit_df]
        mock_read_csv.side_effect = [mock_event_df, mock_user_df, mock_withdrawal_df]
        
        data = load_and_transform_data()
        
        # Check the keys in the returned dictionary
        self.assertIn('users', data)
        self.assertIn('deposits', data)
        self.assertIn('withdrawals', data)
        self.assertIn('events', data)
        print("test_load_and_transform_data passed")

    def test_create_dates_table(self):
        deposits = pd.DataFrame({'event_timestamp': pd.to_datetime(['2023-01-01', '2023-01-02'])})
        withdrawals = pd.DataFrame({'event_timestamp': pd.to_datetime(['2023-01-03'])})
        events = pd.DataFrame({'event_timestamp': pd.to_datetime(['2023-01-01', '2023-01-04'])})
        
        dates_df = create_dates_table(deposits, withdrawals, events)
        
        expected_dates = pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04']).normalize()
        self.assertTrue(all(dates_df['Date'].isin(expected_dates)))
        self.assertEqual(len(dates_df), 4)
        print("test_create_dates_table passed")

    def test_map_date_ids(self):
        df = pd.DataFrame({'event_timestamp': pd.to_datetime(['2023-01-01', '2023-01-02'])})
        dates_df = pd.DataFrame({
            'Date': pd.to_datetime(['2023-01-01', '2023-01-02']).normalize(),
            'DateID': [1, 2]
        })
        df_mapped = map_date_ids(df, dates_df)
        
        self.assertIn('DateID', df_mapped.columns)
        self.assertEqual(df_mapped['DateID'].tolist(), [1, 2])
        print("test_map_date_ids passed")

    def test_create_transactions_table(self):
        deposits = pd.DataFrame({
            'id': [1],
            'user_id': [1],
            'amount': [100.0],
            'currency': ['USD'],
            'tx_status': ['complete'],
            'DateID': [1],
            'event_timestamp': pd.to_datetime(['2023-01-01T00:00:00Z'])
        })
        withdrawals = pd.DataFrame({
            'id': [2],
            'user_id': [1],
            'amount': [50.0],
            'currency': ['USD'],
            'tx_status': ['complete'],
            'DateID': [2],
            'event_timestamp': pd.to_datetime(['2023-01-02T00:00:00Z'])
        })

        transactions = create_transactions_table(deposits, withdrawals)
        
        self.assertEqual(len(transactions), 2)
        self.assertIn('TransID', transactions.columns)
        self.assertIn('TransType', transactions.columns)
        self.assertEqual(transactions['TransType'].tolist(), ['deposit', 'withdrawal'])
        print("test_create_transactions_table passed")

if __name__ == '__main__':
    unittest.main()
