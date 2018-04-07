DROP TABLE IF EXISTS messageReceipient;
DROP TABLE IF EXISTS messages;
DROP TABLE IF EXISTS pendingGroupMembers;
DROP TABLE IF EXISTS groupMembership;
DROP TABLE IF EXISTS groups;
DROP TABLE IF EXISTS pendingFriends;
DROP TABLE IF EXISTS friends;
DROP TABLE IF EXISTS profile;

CREATE TABLE profile (
	userID varchar(20),
	fname varchar(20) NOT NULL,
	lname varchar(20) NOT NULL,
	email varchar(30) NOT NULL,
	password varchar(15) NOT NULL,
	DOB date NOT NULL,
	lastlogin timestamp NOT NULL,
	PRIMARY KEY (userID),
	CHECK (email LIKE '%_@__%.__%'),
	CHECK (DOB <= CURRENT_DATE)
);

CREATE TABLE friends (
	userID1 varchar(20),
	userID2 varchar(20),
	friendshipDate date NOT NULL,
	message char(200) DEFAULT 'I accepted your friend request!',
	PRIMARY KEY (userID1, userID2),
	FOREIGN KEY (userID1) REFERENCES profile ON DELETE CASCADE,
	FOREIGN KEY (userID2) REFERENCES profile ON DELETE CASCADE
);

CREATE TABLE pendingFriends (
	userID1 varchar(20),
	userID2 varchar(20),
	message char(200) DEFAULT 'Hi! Let''s be friends!',
	PRIMARY KEY (userID1, userID2),
	FOREIGN KEY (userID1) REFERENCES profile ON DELETE CASCADE,
	FOREIGN KEY (userID2) REFERENCES profile ON DELETE CASCADE
);

CREATE TABLE groups(
	gID varchar(20),
	name varchar(40) NOT NULL,
	lmt integer DEFAULT 10,
	description varchar(200),
	PRIMARY KEY (gID)
);

/* Handle message deletion when user is deleted in profile*/
CREATE TABLE messages (
	msgID varchar(20),
	fromUserID varchar(20) NOT NULL,
	toUserID varchar(20) DEFAULT NULL,
	toGroupID varchar(20) DEFAULT NULL,
	message varchar(20) NOT NULL,
	dateSent timestamp DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY (msgID),
	FOREIGN KEY (fromUserID) REFERENCES profile,
	FOREIGN KEY (toUserID) REFERENCES profile,
	FOREIGN KEY (toGroupID) REFERENCES groups,
	CHECK ((toUserID IS NOT NULL AND toGroupID IS NULL) OR (toUserID IS NULL AND toGroupID IS NOT NULL)),
	CHECK (dateSent <= CURRENT_TIMESTAMP)
);

CREATE TABLE messageReceipient (
	msgID varchar(20),
	toUserID varchar(20) DEFAULT NULL,
	FOREIGN KEY (msgID) REFERENCES messages,
	FOREIGN KEY (toUserID) REFERENCES profile ON DELETE CASCADE
);

CREATE TABLE groupMembership(
	gID varchar(20),
	userID varchar(20),
	role varchar(20),
	PRIMARY KEY (gID, userID),
	FOREIGN KEY(gID) REFERENCES groups,
	FOREIGN KEY (userID) REFERENCES profile ON DELETE CASCADE
	/*CHECK ((SELECT count(userID) FROM groupMembership WHERE groupMembership.gID = gID) < (SELECT lmt FROM groups WHERE groups.gID = gID))
		"cannot use subquery in check constraint"*/
);


/* ASK DELIS ABOUT PENDING USERS, GROUP LIMIT*/
CREATE TABLE pendingGroupMembers(
	gID varchar(20),
	userID varchar(20),
	message varchar(200),
	PRIMARY KEY (gID, userID),
	FOREIGN KEY (gID) REFERENCES groups ON DELETE CASCADE,
	FOREIGN KEY (userID) REFERENCES profile ON DELETE CASCADE
	/*CHECK ((SELECT count(userID) FROM groupMembership WHERE groupMembership.gID = gID) < (SELECT lmt FROM groups WHERE groups.gID = gID))
		"cannot use subquery in check constraint"*/
);
