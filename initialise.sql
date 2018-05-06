DROP TABLE IF EXISTS messageRecipient cascade;
DROP TABLE IF EXISTS messages cascade;
DROP TABLE IF EXISTS pendingGroupMembers cascade;
DROP TABLE IF EXISTS groupMembership cascade;
DROP TABLE IF EXISTS groups cascade;
DROP TABLE IF EXISTS pendingFriends cascade;
DROP TABLE IF EXISTS friends cascade;
DROP TABLE IF EXISTS profile cascade;

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
	message char(200) DEFAULT 'Hi! We should be friends!',
	PRIMARY KEY (userID1, userID2),
	FOREIGN KEY (userID1) REFERENCES profile ON DELETE CASCADE,
	FOREIGN KEY (userID2) REFERENCES profile ON DELETE CASCADE
);

CREATE TABLE groups(
	gID varchar(20),
	name varchar(40) NOT NULL,
	lmt integer DEFAULT 10 	NOT NULL,
	description varchar(200) NOT NULL,
	PRIMARY KEY (gID)
);

/* Handle message deletion when user is deleted in profile*/
CREATE TABLE messages (
	msgID SERIAL NOT NULL,
	fromUserID varchar(20),
	toUserID varchar(20) DEFAULT NULL,
	toGroupID varchar(20) DEFAULT NULL,
	message varchar(200) NOT NULL,
	dateSent timestamp DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY (msgID),
	FOREIGN KEY (fromUserID) REFERENCES profile ON DELETE SET NULL,
	FOREIGN KEY (toUserID) REFERENCES profile ON DELETE SET NULL,
	FOREIGN KEY (toGroupID) REFERENCES groups ON DELETE SET NULL,
	CHECK (dateSent <= CURRENT_TIMESTAMP)
);

CREATE TABLE messageRecipient (
	msgID integer,
	toUserID varchar(20) NOT NULL,
	PRIMARY KEY (msgID, toUserID),
	FOREIGN KEY (msgID) REFERENCES messages ON DELETE CASCADE,
	FOREIGN KEY (toUserID) REFERENCES profile ON DELETE CASCADE
);

CREATE TABLE groupMembership(
	gID varchar(20),
	userID varchar(20),
	role varchar(20),
	PRIMARY KEY (gID, userID),
	FOREIGN KEY(gID) REFERENCES groups ON DELETE CASCADE,
	FOREIGN KEY (userID) REFERENCES profile ON DELETE CASCADE,
	CHECK (role IN ('manager', 'member'))
);

/* ASK DELIS ABOUT PENDING USERS, GROUP LIMIT*/
CREATE TABLE pendingGroupMembers(
	gID varchar(20),
	userID varchar(20),
	message varchar(200),
	PRIMARY KEY (gID, userID),
	FOREIGN KEY (gID) REFERENCES groups ON DELETE CASCADE,
	FOREIGN KEY (userID) REFERENCES profile ON DELETE CASCADE
);

DROP FUNCTION IF EXISTS group_lmt();
DROP TRIGGER IF EXISTS group_lmt ON groupMembership;
DROP FUNCTION IF EXISTS pending_group_lmt();
DROP TRIGGER IF EXISTS pending_group_lmt ON pendingGroupMembers;
DROP FUNCTION IF EXISTS add_msg_recipients();
DROP TRIGGER IF EXISTS add_msg_recipients ON messages;
DROP FUNCTION IF EXISTS pending_friend();
DROP TRIGGER IF EXISTS pending_friend ON pendingFriends;
DROP FUNCTION IF EXISTS reverse_friend();
DROP TRIGGER IF EXISTS reverse_friend ON friends;
DROP FUNCTION IF EXISTS delete_groups();
DROP TRIGGER IF EXISTS delete_groups ON groupMembership;
DROP FUNCTION IF EXISTS delete_messages();
DROP TRIGGER IF EXISTS delete_messages ON profile;
DROP TRIGGER IF EXISTS delete_messages ON groups;

/*number of members in a group should be less than or equal to limit*/
CREATE FUNCTION group_lmt() RETURNS trigger AS $group_lmt$
	BEGIN
		IF (SELECT count(userID) FROM groupMembership WHERE groupMembership.gID = NEW.gID) >= (SELECT lmt FROM groups WHERE groups.gID = NEW.gID) THEN
			RAISE EXCEPTION 'group limit reached';
		END IF;
		RETURN NEW;
	END;
$group_lmt$ LANGUAGE plpgsql;

CREATE TRIGGER group_lmt BEFORE INSERT OR UPDATE ON groupMembership
	FOR EACH ROW EXECUTE PROCEDURE group_lmt();

/*number of members in a group should be less than or equal to limit and member should not already be in group*/
CREATE FUNCTION pending_group_lmt() RETURNS trigger AS $pending_group_lmt$
	BEGIN
		IF (SELECT count(userID) FROM groupMembership WHERE groupMembership.gID = NEW.gID) >= (SELECT lmt FROM groups WHERE groups.gID = NEW.gID) THEN
			RAISE EXCEPTION 'group limit reached';
		END IF;
		IF (SELECT count(userID) FROM groupMembership WHERE gID = NEW.gID AND userID = NEW.userID) != 0 THEN
			RAISE EXCEPTION 'member already in group';
		END IF;
		RETURN NEW;
	END;
$pending_group_lmt$ LANGUAGE plpgsql;

CREATE TRIGGER pending_group_lmt BEFORE INSERT OR UPDATE ON pendingGroupMembers
	FOR EACH ROW EXECUTE PROCEDURE pending_group_lmt();

/*add message recipient when message is added, also check constraints are satisfied*/
/* CHECK ((toUserID IS NOT NULL AND toGroupID IS NULL) OR (toUserID IS NULL AND toGroupID IS NOT NULL)) */
/* CHECK (fromUserID IS NOT NULL) */
CREATE FUNCTION add_msg_recipients() RETURNS trigger AS $add_msg_recipients$
	BEGIN
		IF NEW.fromUserID IS NULL THEN
			RAISE EXCEPTION 'fromUserID cannot be NULL';
		END IF;
		IF NEW.toUserID IS NULL AND NEW.toGroupID IS NULL THEN
			RAISE EXCEPTION 'toUserID and toGroupID cannot both be NULL, recipient is needed for a message';
		END IF;
		IF (NEW.toUserID IS NOT NULL) AND (NEW.toGroupID IS NOT NULL) THEN
			RAISE EXCEPTION 'either toUserID or toGroupID must be NULL, cannot have multiple recipient types';
		END IF;

		IF NEW.toUserID IS NOT NULL THEN
			INSERT INTO messageRecipient VALUES (NEW.msgID, NEW.toUserID);
		END IF;
		IF NEW.toGroupID IS NOT NULL THEN
			INSERT INTO messageRecipient(msgID, toUserID) SELECT NEW.msgID, groupMembership.userID FROM groupMembership WHERE groupMembership.gID = NEW.toGroupID;
		END IF;
		RETURN NEW;
	END;
$add_msg_recipients$ LANGUAGE plpgsql;

CREATE TRIGGER add_msg_recipients AFTER INSERT ON messages
	FOR EACH ROW EXECUTE PROCEDURE add_msg_recipients();

/*pending friend should not be added if already friends*/
CREATE FUNCTION pending_friend() RETURNS trigger AS $pending_friend$
	BEGIN
		IF (SELECT count(userID1) FROM friends WHERE userID1 = NEW.userID1 AND userID2 = NEW.userID2) != 0 THEN
			RAISE EXCEPTION 'already friends';
		END IF;
		IF (SELECT count(userID1) FROM friends WHERE userID1 = NEW.userID2 AND userID2 = NEW.userID1) != 0 THEN
			RAISE EXCEPTION 'reverse are already friends';
		END IF;
		IF (SELECT count(userID1) FROM pendingFriends WHERE userID2 = NEW.userID1 AND userID1 = NEW.userID2) != 0 THEN
			RAISE EXCEPTION 'reverse are already pending';
		END IF;
		RETURN NEW;
	END;
$pending_friend$ LANGUAGE plpgsql;

CREATE TRIGGER pending_friend BEFORE INSERT ON pendingFriends
	FOR EACH ROW EXECUTE PROCEDURE pending_friend();

/*friends should not be added if reverse are already friends*/
CREATE FUNCTION reverse_friend() RETURNS trigger AS $reverse_friend$
	BEGIN
		IF (SELECT count(userID1) FROM friends WHERE userID2 = NEW.userID1 AND userID1 = NEW.userID2) != 0 THEN
			RAISE EXCEPTION 'reverse already friends';
		END IF;
		RETURN NEW;
	END;
$reverse_friend$ LANGUAGE plpgsql;

CREATE TRIGGER reverse_friend BEFORE INSERT ON friends
	FOR EACH ROW EXECUTE PROCEDURE reverse_friend();

/*delete groups if no manager left*/
CREATE FUNCTION delete_groups() RETURNS trigger AS $delete_groups$
	BEGIN
		IF (SELECT count(userID) FROM groupMembership WHERE gID = OLD.gID AND role='manager') = 0 THEN
			DELETE FROM groups WHERE gID = OLD.gID;
		END IF;
		RETURN OLD;
	END;
$delete_groups$ LANGUAGE plpgsql;

CREATE TRIGGER delete_groups AFTER DELETE ON groupMembership
	FOR EACH ROW EXECUTE PROCEDURE delete_groups();

/*delete messages if no owning resources left*/
CREATE FUNCTION delete_messages() RETURNS trigger AS $delete_messages$
	BEGIN
		DELETE FROM messages WHERE messages.toUserID is NULL AND messages.fromUserID is NULL AND messages.toGroupID is NULL;
		RETURN NULL;
	END;
$delete_messages$ LANGUAGE plpgsql;

CREATE TRIGGER delete_messages AFTER DELETE ON profile
	FOR EACH ROW EXECUTE PROCEDURE delete_messages();

CREATE TRIGGER delete_messages_groups AFTER DELETE ON groups
	FOR EACH ROW EXECUTE PROCEDURE delete_messages();
