-- NOTE. Note: The queries were tested using pandasql. Please be aware that some structures, especially the Date type, might differ depending on the database used.

-- Query 1 How Many Users Were Active on a Given Day (They Made a Deposit or Withdrawal)

SELECT COUNT(DISTINCT t.user_id) AS ActiveUsers
FROM transactions_vf t
JOIN dates_df d ON t.DateID = d.DateID
WHERE d.Date = '2020-01-02 00:00:00.000000';

-- Query 2 Identify Users Who Haven't Made a Deposit

SELECT u.user_id
FROM users u
WHERE u.user_id NOT IN (
    SELECT t.user_id 
    FROM transactions_vf t 
    WHERE t.TransType = 'deposit'
);

-- Query 3 Identify on a given day which users have made more than 5 deposits historically

SELECT t.user_id
FROM transactions_vf t
JOIN dates_df d ON t.DateID = d.DateID
WHERE t.TransType = 'deposit'              
AND d.Date <= '2024-07-19 00:00:00.000000'                
GROUP BY t.user_id
HAVING COUNT(t.TransID) > 5;

-- Query 4 When Was the Last Time a User Made a Login

SELECT e.user_id, MAX(d.Date) AS LastLoginDate
FROM events_vf e
JOIN dates_df d ON e.DateID = d.DateID
WHERE e.event_name = 'login'
GROUP BY e.user_id;

-- Query 5 How Many Times a User Has Made a Login Between Two Dates

SELECT user_id, COUNT(event_name) AS LoginCount
FROM events_vf e
JOIN dates_df d ON e.DateID = d.DateID
WHERE event_name = 'login' AND Date BETWEEN '2021-11-24 00:00:00.000000' AND '2022-04-13 00:00:00.000000'
GROUP BY user_id;

-- Query 6 Number of Unique Currencies Deposited on a Given Day

SELECT COUNT(DISTINCT currency) AS UniqueCurrencies
FROM transactions_vf t
JOIN dates_df d ON t.DateID = d.DateID
WHERE Date = '2021-11-24 00:00:00.000000'
AND TransType = 'deposit';

-- Query 7 Number of Unique Currencies Withdrawn on a Given Day

SELECT COUNT(DISTINCT currency) AS UniqueCurrencies
FROM transactions_vf t
JOIN dates_df d ON t.DateID = d.DateID
WHERE Date = '2021-11-24 00:00:00.000000'
AND TransType = 'withdrawal';

-- Query 8 Total Amount Deposited of a Given Currency on a Given Day

SELECT currency, SUM(amount) AS TotalAmount
FROM transactions_vf t
JOIN dates_df d ON t.DateID = d.DateID
WHERE currency = 'usd' AND Date = '2021-11-24 00:00:00.000000'
GROUP BY currency;