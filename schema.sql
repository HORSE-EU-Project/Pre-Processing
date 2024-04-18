-- Create the user table
CREATE TABLE IF NOT EXISTS user(
  id TEXT PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  email TEXT UNIQUE NOT NULL,
  token TEXT UNIQUE NOT NULL,
  organization TEXT,
  domain_name TEXT
);

-- Create the apps table
CREATE TABLE IF NOT EXISTS apps(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  user_id TEXT NOT NULL,
  FOREIGN KEY (user_id) REFERENCES user (id)
);

-- Create the history table
CREATE TABLE IF NOT EXISTS history(
  history_id TEXT PRIMARY KEY,
  usr_id TEXT NOT NULL,
  timestamp TIMESTAMP NOT NULL,
  filename TEXT NOT NULL,
  description TEXT NOT NULL,
  FOREIGN KEY (usr_id) REFERENCES user (id)
);

-- Create the subscriptions table
CREATE TABLE IF NOT EXISTS subscriptions(
  subscription_id SERIAL PRIMARY KEY,
  user_id TEXT NOT NULL,
  subscription_type TEXT NOT NULL,
  endpoint_url TEXT NOT NULL,
  DB_url TEXT NOT NULL,
  query TEXT,
  interval TEXT,
  active BOOLEAN NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES user (id)
);

-- Trigger for updating the 'updated_at' timestamp
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = CURRENT_TIMESTAMP;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply the trigger to the subscriptions table
CREATE TRIGGER update_subscriptions_updated_at
BEFORE UPDATE ON subscriptions
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();
