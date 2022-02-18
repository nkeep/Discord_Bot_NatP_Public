CREATE TABLE IF NOT EXISTS guilds (
	GuildID bigint PRIMARY KEY,
	Prefix text DEFAULT '+',
	reminderchannel bigint
);

CREATE TABLE IF NOT EXISTS exp (
	UserID integer PRIMARY KEY,
	XP integer DEFAULT 0,
	Level integer DEFAULT 0,
	XPLock text DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS db (
	name text PRIMARY KEY,
	result text,
	isfile integer,
	author text,
	uses int DEFAULT 0
);

CREATE TABLE IF NOT EXISTS memes(
  meme_id text PRIMARY KEY,
  title text
);

CREATE TABLE IF NOT EXISTS templates(
	name text PRIMARY KEY,
	filelocation text,
	type text CHECK (type = 'foreground' or type = 'background'),
	startx integer,
	starty integer,
	width integer,
	height integer,
	size text
);

CREATE TABLE IF NOT EXISTS sb(
	id BIGSERIAL,
	quote text PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS csgo(
	id BIGSERIAL PRIMARY KEY,
	data text
);

CREATE TABLE IF NOT EXISTS reminders(
	id BIGSERIAL PRIMARY KEY,
	year int,
	month int,
	day int,
	hour int,
	minute int,
	reminder text,
	username bigint,
	channel bigint
);
