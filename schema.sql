CREATE TABLE user (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  token TEXT UNIQUE NOT NULL,
  application TEXT 
);

CREATE TABLE history (
	history_id TEXT PRIMARY KEY,
  usr_id TEXT NOT NULL,
  timestamp TIMESTAMP NOT NULL,
  filename TEXT NOT NULL,
  description TEXT NOT NULL,
  foreign KEY (usr_id) references user (id)
  
	
);
