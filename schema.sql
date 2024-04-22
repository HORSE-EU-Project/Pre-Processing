-- Create the user table
CREATE TABLE IF NOT EXISTS user(
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT NOT NULL,
  token TEXT NOT NULL,
  organization TEXT,
  domain_name TEXT
);

-- Create the apps table
CREATE TABLE IF NOT EXISTS apps(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  user_id TEXT NOT NULL
);

-- Create the history table
CREATE TABLE IF NOT EXISTS history(
  history_id TEXT PRIMARY KEY,
  usr_id TEXT NOT NULL,
  timestamp TIMESTAMP NOT NULL,
  filename TEXT NOT NULL,
  description TEXT
);

-- Create the subscriptions table
CREATE TABLE IF NOT EXISTS subscriptions(
  subscription_id INTEGER PRIMARY KEY,
  user_id TEXT NOT NULL,
  subscription_type TEXT,
  endpoint_url TEXT NOT NULL,
  DB_url TEXT NOT NULL,
  query TEXT,
  interval TEXT,
  active BOOLEAN NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


CREATE TRIGGER update_subscription_timestamp
AFTER UPDATE ON subscriptions
BEGIN
    UPDATE subscriptions SET updated_at = CURRENT_TIMESTAMP WHERE rowid = NEW.rowid;
END;


