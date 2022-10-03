CREATE TABLE IF NOT EXISTS user(
  id TEXT PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  email TEXT UNIQUE NOT NULL,
  token TEXT UNIQUE NOT NULL,
  organization TEXT,
  domain_name TEXT
);

CREATE TABLE IF NOT EXISTS apps(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  user TEXT NOT NULL,
  foreign KEY (user) references user (id)
);

CREATE TABLE IF NOT EXISTS history(
	history_id TEXT PRIMARY KEY,
  usr_id TEXT NOT NULL,
  timestamp TIMESTAMP NOT NULL,
  filename TEXT NOT NULL,
  description TEXT NOT NULL,
  foreign KEY (usr_id) references user (id)
);
