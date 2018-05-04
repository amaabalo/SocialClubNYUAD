import psycopg2
import time
import datetime
import sys

class Status:
    CONN_FAIL = 0
    CONN_SUCCESS = 1
    USERNAME_PASS_DNE = 2 #  does not exist
    LOGIN_SUCCESS = 3
    DATABASE_ERROR = 4
    USERNAME_ALREADY_EXISTS = 5
    EMAIL_ALREADY_EXISTS = 6
    USERNAME_PASS_DNM = 7 # Email and password do not match
    CREATE_SUCCESS = 8
    CREATE_LOG_IN_SUCCESS = 9
    INSERT_SUCCESS = 10
    DELETE_SUCCESS = 11
    DELETE_ERROR = 12
    REQUEST_NONEXISTENT = 13
    GROUP_LIMIT_REACHED = 14


    @staticmethod
    def error_string(status):
        if status == Status.CONN_FAIL:
            return "Connection faied."
        if status == Status.CONN_SUCCESS:
            return "Connection successful."
        if status == Status.USERNAME_PASS_DNE:
            return "Username does not exist."
        if status == Status.LOGIN_SUCCESS:
            return "Log in successful."
        if status == Status.DATABASE_ERROR:
            return "DATABASE_ERROR"
        if status == Status.USERNAME_ALREADY_EXISTS:
            return "Username already exists."
        if status == Status.EMAIL_ALREADY_EXISTS:
            return "Email already exists."
        if status == Status.USERNAME_PASS_DNM:
            return "Username and password do not match."
        if status == Status.CREATE_SUCCESS:
            return "User successfully created."
        if status == Status.CREATE_LOG_IN_SUCCESS:
            return "User successfully created and logged in."
        if status == Status.INSERT_SUCCESS:
            return "Record successfully inserted."
        if status == Status.DELETE_SUCCESS:
            return "Record successfully deleted."
        if status == Status.DELETE_ERROR:
            return "Record could not be deleted."
        if status == Status.REQUEST_NONEXISTENT:
            return "Request does not exist."
        if status == Status.GROUP_LIMIT_REACHED:
            return "The group's limit has been reached."

class DatabaseHelper:
    __instance = None

    def __init__(self):
        if DatabaseHelper.__instance != None:
            raise Exception("An instance of DatabaseHelper already exists. Use get_instance() instead.")
        else:
            DatabaseHelper.__instance = self
            self.conn = psycopg2.connect("dbname=" + sys.argv[1] + " user=" + sys.argv[2] + " password=" + sys.argv[3] + " host=127.0.0.1")
            self.conn.set_client_encoding('UTF8')
            self.cur = self.conn.cursor()

    @staticmethod
    def get_instance():
        if DatabaseHelper.__instance == None:
            DatabaseHelper()
        return DatabaseHelper.__instance

    # Returns a dictionary whose keys are the attributes in the relation
    # table_name, and whose values are True or False depending on whether the
    # attribute can be null or not.
    def get_attributes_nullabities(self, table_name):
        SQL =  "SELECT column_name, is_nullable FROM information_schema.columns WHERE table_name = %s"
        data = (table_name,)
        self.cur.execute(SQL, data)
        results = self.cur.fetchall()
        dict = {}
        for result in results:
            dict[result[0]] = True if result[1] == 'YES' else False
        return dict

    # Returns a dictionary whose keys are the attributes in the relation
    # table_name, and whose values are the maximum lengths of the attributes.
    # Will only return attributes that have a maximum length specified.
    def get_attributes_lengths(self, table_name):
        SQL =  "SELECT column_name, character_maximum_length FROM information_schema.columns WHERE table_name = %s"
        data = (table_name,)
        self.cur.execute(SQL, data)
        results = self.cur.fetchall()
        dict = {}
        for result in results:
            if result[1]:
                dict[result[0]] = result[1]
        return dict

    # Returns a list of any attributes in the relation table_name that have
    # a data type of date
    def get_date_attributes(self, table_name):
        SQL =  "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = %s"
        data = (table_name,)
        self.cur.execute(SQL, data)
        results = self.cur.fetchall()
        lst = []
        for result in results:
            if result[1] == 'date':
                lst.append(result[0])
        return lst

    # Returns True if a username already exists in the database, False otherwise.
    def check_username_exists(self, username):
        SQL = "SELECT * FROM profile WHERE userID = %s"
        data = (username,)
        self.cur.execute(SQL, data)
        results = self.cur.fetchall()
        if not results:
            return False
        return True

    # Returns True if a group_id already exists in the database, False otherwise.
    def check_group_id_exists(self, group_id):
        SQL = "SELECT * FROM groups WHERE gid = %s"
        data = (group_id,)
        self.cur.execute(SQL, data)
        results = self.cur.fetchall()
        if not results:
            return False
        return True

    # Returns True if an email already exists in the database, False otherwise.
    def check_email_exists(self, email):
        SQL = "SELECT * FROM profile WHERE email = %s"
        self.cur.execute(SQL, (email,))
        results = self.cur.fetchall()
        if not results:
            return False
        return True

    # Turns a list of tuples from the profile relation into a list of
    # dictionaries whose keys are the attributes of the profile relation and whose
    # values are the contents of the tuples.
    def profile_records_to_dictionaries(self, results):
        rval = []
        for result in results:
            dict = {}
            dict["userID"] = result[0]
            dict["fname"] = result[1]
            dict["lname"] = result[2]
            dict["email"] = result[3]
            dict["password"] = result[4]
            dict["DOB"] = result[5]
            dict["lastlogin"] = result[6]
            rval.append(dict)
        return rval

    # Turns a list of tuples of the form (userid2, userid1, fname, lname, message) into a list of
    # dictionaries whose keys are the attributes (userid2, userid1, fname, lname, message) and whose
    # values are the contents of the tuples. userid2 is the recipient of the request.
    def pendingfriends_records_to_dictionaries(self, results):
        rval = []
        for result in results:
            dict = {}
            dict["userID2"] = result[0]
            dict["userID1"] = result[1]
            dict["fname"] = result[2]
            dict["lname"] = result[3]
            dict["message"] = result[4].strip()
            rval.append(dict)
        return rval

    # Turns a list of tuples of the form (userid2, userid1, fname, lname, message) into a list of
    # dictionaries whose keys are the attributes (userid2, userid1, fname, lname, message) and whose
    # values are the contents of the tuples. userid2 is the manager of the group.
    def pendinggroupmembers_records_to_dictionaries(self, results):
        rval = []
        for result in results:
            dict = {}
            dict["userID2"] = result[0]
            dict["userID1"] = result[1]
            dict["fname"] = result[2]
            dict["lname"] = result[3]
            dict["message"] = result[4].strip()
            dict["gID"] = result[5]
            dict["name"] = result[6]
            dict["lmt"] = result[7]
            dict["description"] = '' if not result[8] else result[8].strip()
            rval.append(dict)
        return rval

    # Check if the password in the database for the user given_username
    # matches given_password. Returns True if so, false otherwise.
    def check_passwords_match(self, given_username, given_password):
        SQL = "SELECT * FROM profile WHERE userID = %s"
        self.cur.execute(SQL, (given_username,))
        results = self.cur.fetchall()
        if not results:
            return False
        result = self.profile_records_to_dictionaries(results)[0]
        if (result["password"] != given_password):
            return False
        return result

    # Inserts a new user into the database.
    def create_new_user(self, username, f_name, l_name, email, password, DOB):
        # check if username or email already exist
        if self.check_username_exists(username):
            return Status.USERNAME_ALREADY_EXISTS
        if self.check_email_exists(email):
            return Status.USERNAME_ALREADY_EXISTS
        ts = time.time()
        lastlogin = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        sql = 'INSERT INTO profile(userID, fname, lname, email, password, DOB, lastlogin)\
                VALUES (%s, %s, %s, %s, %s, %s, %s);'
        data = (username, f_name, l_name, email, password, DOB, lastlogin)
        try:
			self.cur.execute(sql,data)
			self.conn.commit()
        except psycopg2.IntegrityError:
            self.conn.rollback()
            return Status.DATABASE_ERROR
        return Status.CREATE_SUCCESS

    # Check if a friendship exists between user_id1 and user_id2. Returns True
    # if they are friends, False otherwise.
    def check_friendship_exists(self, user_id1, user_id2):
        SQL = "SELECT * FROM friends WHERE (userID1 = %s AND userID2 = %s) OR (userID1 = %s AND userID2 = %s);"
        data = ((user_id1, user_id2, user_id2, user_id1))
        self.cur.execute(SQL, data)
        results = self.cur.fetchall()
        if not results:
            return False
        return True

    # Returns all friends of the user_id
    def get_all_friends(self, user_id):
        SQL = "WITH a AS (SELECT userid1 as friendid FROM friends WHERE userid2 = %s),\
                    b AS (SELECT userid2 as friendid FROM friends WHERE userid1 = %s),\
                    c AS (SELECT * FROM a UNION SELECT * FROM b)\
               SELECT userid, fname, lname, email, '', dob, '' FROM c JOIN profile ON c.friendid = profile.userid;"
        data = (user_id, user_id)
        self.cur.execute(SQL, data)
        results = self.cur.fetchall()
        if not results:
            return None
        return self.profile_records_to_dictionaries(results)

    # returns None if there is no corresponding name
    def get_names_from_user_id(self, user_id):
        SQL = "SELECT fname, lname FROM profile WHERE userID = %s"
        self.cur.execute(SQL, (user_id,))
        results = self.cur.fetchall()
        if not results:
            return None
        return(results[0])

    # returns None if there is no corresponding name
    def get_group_name_from_group_id(self, group_id):
        SQL = "SELECT name FROM groups WHERE gid = %s"
        data = (group_id,)
        self.cur.execute(SQL, data)
        results = self.cur.fetchall()
        if not results:
            return None
        name, = results[0]
        return(name)

    # returns true if user_id1 has a friend request from user_id2.
    # In database, userID2 is recipient.
    def check_has_pending_friend_request_from(self, user_id1, user_id2):
        SQL = "SELECT * FROM pendingfriends WHERE userID2 = %s AND userID1 = %s;"
        data = (user_id1, user_id2)
        self.cur.execute(SQL, data)
        results = self.cur.fetchall()
        if not results:
            return False
        return True

    # returns true if user_id has a pending request to join group_id.
    def check_has_pending_join_request_from(self, group_id, user_id):
        SQL = "SELECT * FROM pendinggroupmembers WHERE gid = %s AND userid = %s;"
        data = (group_id, user_id)
        self.cur.execute(SQL, data)
        results = self.cur.fetchall()
        if not results:
            return False
        return True

    # Returns true if user_id is the manager of the group
    def check_is_group_manager(self, user_id, group_id):
        SQL = "SELECT * FROM groupmembership WHERE userID = %s AND gID = %s AND role = 'manager';"
        data = (user_id, group_id)
        self.cur.execute(SQL, data)
        results = self.cur.fetchall()
        if not results:
            return False
        return True

    # Returns true if user_id is (strictly) a member of the group
    def check_is_group_member(self, user_id, group_id):
        SQL = "SELECT * FROM groupmembership WHERE userID = %s AND gID = %s AND role = 'member';"
        data = (user_id, group_id)
        self.cur.execute(SQL, data)
        results = self.cur.fetchall()
        if not results:
            return False
        return True

    #checks if user_id is a member or manager of the group. Returns role if so, False if neither
    def check_is_group_member_or_manager(self, user_id, group_id):
        SQL = "SELECT role FROM groupmembership WHERE userID = %s AND gID = %s;"
        data = (user_id, group_id)
        self.cur.execute(SQL, data)
        results = self.cur.fetchall()
        if not results:
            return False
        role, = results[0]
        return role

    # Inserts a friend request from user_id1 to user_id2 into pendingfriends
    def insert_friend_request(self, user_id1, user_id2, message):
        if message == None:
            SQL = "INSERT INTO pendingfriends (userid1, userid2) VALUES (%s, %s);"
            data = (user_id1, user_id2)
        else:
            SQL = "INSERT INTO pendingfriends VALUES (%s, %s, %s);"
            data = (user_id1, user_id2, message)
        try:
			self.cur.execute(SQL,data)
			self.conn.commit()
        except psycopg2.IntegrityError:
            self.conn.rollback()
            return Status.DATABASE_ERROR
        return Status.INSERT_SUCCESS

    # Inserts a group join request from user_id to group_id
    def insert_group_join_request(self, user_id, group_id, message):
        SQL = "INSERT INTO pendinggroupmembers VALUES (%s, %s, %s);"
        data = (group_id, user_id, message)
        try:
			self.cur.execute(SQL,data)
			self.conn.commit()
        except psycopg2.IntegrityError:
            self.conn.rollback()
            return Status.DATABASE_ERROR
        return Status.INSERT_SUCCESS

    # Returns the default value for attribute in the relation with
    # name table_name, or None if there is no default value for attribute.
    def get_default_value(self, table_name, attribute):
        SQL =  "SELECT column_name, column_default FROM information_schema.columns WHERE table_name = %s AND column_name = %s;"
        data = (table_name, attribute)
        self.cur.execute(SQL, data)
        results = self.cur.fetchall()
        if not results:
            return None
        return results[0][1]

    # Returns a list of dictionaries of users found by a search with keywoard
    def search_for_user(self, keyword):
        SQL =  "SELECT * FROM profile WHERE LOWER(userid) LIKE %s OR LOWER(fname) LIKE %s OR LOWER(lname) LIKE %s OR LOWER(email) LIKE %s;"
        keyword = '%' + keyword.lower() + '%'
        data = (keyword, keyword, keyword, keyword)
        self.cur.execute(SQL, data)
        results = self.cur.fetchall()
        if not results:
            return None
        return self.profile_records_to_dictionaries(results)

    # Returns a list of dictionaries of unconfirmed friend requests for a given user
    # In database, userID2 is recipient.
    def get_unconfirmed_friend_requests(self, user_id):
        SQL =  "WITH a AS (SELECT * FROM pendingfriends WHERE userid2 = %s)\
               SELECT userid2, userid1, fname, lname, message FROM a JOIN profile ON a.userid1 = profile.userid;"
        data = (user_id,)
        self.cur.execute(SQL, data)
        results = self.cur.fetchall()
        if not results:
            return None
        return self.pendingfriends_records_to_dictionaries(results)

    # Deletes a pending friend request from user_id1 to user_id2
    def delete_friend_request(self, user_id1, user_id2):
        SQL = "DELETE FROM pendingfriends WHERE userID1 = %s and userID2 = %s;"
        data = (user_id1, user_id2)
        try:
			self.cur.execute(SQL,data)
			self.conn.commit()
        except psycopg2.IntegrityError:
            self.conn.rollback()
            return Status.DATABASE_ERROR
        return Status.DELETE_SUCCESS

    # Deletes a pending group join request from user_id1 to group_id
    def delete_group_join_request(self, user_id, group_id):
        SQL = "DELETE FROM pendinggroupmembers WHERE userID = %s and gid = %s;"
        data = (user_id, group_id)
        try:
			self.cur.execute(SQL,data)
			self.conn.commit()
        except psycopg2.IntegrityError:
            self.conn.rollback()
            return Status.DATABASE_ERROR
        return Status.DELETE_SUCCESS

    # Inserts a friendship between user_id1 and user_id2, provided there is a
    # request from user_id1 to user_id2
    def create_friendship(self, user_id1, user_id2, message = None):
        SQL = "SELECT * FROM pendingfriends WHERE userID1 = %s and userID2 = %s"
        data = (user_id1, user_id2)
        self.cur.execute(SQL,data)
        res = self.cur.fetchall()
        if not res:
            return Status.REQUEST_NONEXISTENT
        # delete the old friend request
        SQL = "DELETE FROM pendingfriends WHERE userID1 = %s and userID2 = %s;"
        data = (user_id1, user_id2)
        try:
			self.cur.execute(SQL,data)
        except psycopg2.IntegrityError:
            return Status.DELETE_ERROR
        # insert the new friendship
        SQL = "INSERT INTO friends (userID1, userID2, friendshipdate) VALUES(%s, %s, %s);"
        accept_date = datetime.date.today()
        data = (user_id1, user_id2, accept_date)
        try:
			self.cur.execute(SQL,data)
			self.conn.commit()
        except psycopg2.IntegrityError:
            self.conn.rollback()
            return Status.DATABASE_ERROR
        return Status.INSERT_SUCCESS

    # Returns the group limit of a group
    def get_group_limit(self, group_id):
        SQL = "SELECT lmt FROM groups WHERE gID = %s"
        data = (group_id,)
        self.cur.execute(SQL, data)
        limit = self.cur.fetchall()
        if not limit:
            return 0
        return limit

    # Returns the number of members in a group
    def get_group_member_count(self, group_id):
        SQL = "SELECT COUNT(userID) FROM groupmembership WHERE gID = %s"
        data = (group_id,)
        self.cur.execute(SQL, data)
        member_count = self.cur.fetchall()
        return member_count

    # Returns true if the group has reached its limit, false otherwise
    def check_group_limit_reached(self, group_id):
        limit = self.get_group_limit(group_id)
        member_count = self.get_group_member_count(group_id)
        return limit == member_count

    # Adds a user_id to a group group_id, provided there is a request to join
    # the group
    def add_group_member(self, user_id, group_id):
        if self.check_group_limit_reached(group_id):
            return Status.GROUP_LIMIT_REACHED

        SQL = "DELETE FROM pendinggroupmembers WHERE userID = %s and gID = %s RETURNING gID;"
        data = (user_id, group_id)
        try:
			self.cur.execute(SQL,data)
        except psycopg2.IntegrityError:
            return Status.DATABASE_ERROR

        results = self.cur.fetchall()
        if not results:
            return Status.REQUEST_NONEXISTENT

        SQL = "INSERT INTO groupmembership VALUES(%s, %s, 'member');"
        data = (group_id, user_id)
        try:
			self.cur.execute(SQL,data)
			self.conn.commit()
        except psycopg2.IntegrityError:
            self.conn.rollback()
            return Status.DATABASE_ERROR

        return Status.INSERT_SUCCESS

    # Accepts all of user_id's current pending requests
    def accept_all_friend_requests(self, user_id):
        pending = self.get_unconfirmed_friend_requests(user_id)
        if pending == None:
            return Status.INSERT_SUCCESS
        for request in pending:
            res = self.create_friendship(request["userID1"], request["userID2"])
            if not res == Status.INSERT_SUCCESS:
                return res
        return Status.INSERT_SUCCESS

    # Returns a list of dictionaries of unconfirmed group join requests for any groups managed by a
    # given user.
    def get_unconfirmed_group_join_requests(self, user_id):
        SQL =  "WITH a AS (SELECT gid, userid AS managerid FROM groupmembership WHERE userid = %s and role = 'manager'),\
                     b AS (SELECT a.managerid, groups.* FROM a JOIN groups ON groups.gid = a.gid),\
                     c AS (SELECT b.*, pendinggroupmembers.userid, pendinggroupmembers.message FROM b JOIN pendinggroupmembers ON pendinggroupmembers.gid = b.gid)\
               SELECT managerid, c.userid, fname, lname, message, gid, name, lmt, description FROM c JOIN profile ON c.userid = profile.userid;"

        data = (user_id,)
        self.cur.execute(SQL, data)
        results = self.cur.fetchall()
        if not results:
            return None
        return self.pendinggroupmembers_records_to_dictionaries(results)



class Request:

    def __init__(self, recipient_id, requester_id, first_name, last_name, message,\
                 group_id = None, group_name = None, limit = None, description = None):
        self.recipient_id = recipient_id
        self.requester_id = requester_id
        self.requester_f_name = first_name
        self.requester_l_name = last_name
        self.message = message
        self.group_id = group_id
        self.group_name = group_name
        self.limit = limit
        self.description = description

    # Given a list of dictionaries of join requests,
    # returns a list of Request objects with the relevant attributes set.
    @staticmethod
    def get_request_objects(requests):
        lst = []
        if not requests:
            return lst
        for request in requests:
            if "gID" in request.keys(): # a group request
                lst.append(Request(request["userID2"], request["userID1"],
                                       request["fname"], request["lname"],
                                       request["message"], group_id = request["gID"],
                                       group_name = request["name"], limit = request["lmt"],
                                       description = request["description"]))
            else:
                lst.append(Request(request["userID2"], request["userID1"],
                                       request["fname"], request["lname"],
                                       request["message"]))
        return lst


class User:

    def __init__(self, user_id = '', f_name = '', l_name = '', email = '', dob = ''):
        self.user_id = user_id
        self.f_name = f_name
        self.l_name = l_name
        self.email = email
        self.dob = dob
        self.logged_in = False
        self.db_helper = DatabaseHelper.get_instance()

    # Logs an existing user in using the given credentials. Returns Status.LOGIN_SUCCESS on success.
    def log_in(self, username, password):
        result = self.db_helper.check_passwords_match(username, password)
        if not result:
            return Status.USERNAME_PASS_DNM
        self.user_id = username
        self.f_name = result["fname"]
        self.l_name = result["lname"]
        self.email = result["email"]
        self.logged_in = True
        return Status.LOGIN_SUCCESS

    def log_out(self):
        self.user_id = ''
        self.f_name = ''
        self.l_name = ''
        self.email = ''
        self.logged_in = False

    # Creates and logs a new user in. Returns Status.CREATE_LOG_IN_SUCCESS if successful
    def create_and_log_in(self, username, f_name, l_name, email, password, DOB):
        res = self.db_helper.create_new_user(username, f_name, l_name, email, password, DOB)
        if (res != Status.CREATE_SUCCESS):
            return res
        res = self.log_in(username, password)
        if not res == Status.LOGIN_SUCCESS:
            return res
        return Status.CREATE_LOG_IN_SUCCESS

    # Send a request from this user to the user with user_id username, with message
    # message. Returns True if successful, False otherwise.
    def send_friend_request_to(self, username, message):
        if not self.db_helper.insert_friend_request(self.user_id, username, message) == Status.INSERT_SUCCESS:
            return False
        return True

    # Send a group join request from this user to the group with gid group_id,
    # Returns True if successful, False otherwise.
    def send_group_join_request_to(self, group_id,  message):
        if not self.db_helper.insert_group_join_request(self.user_id, group_id, message) == Status.INSERT_SUCCESS:
            return False
        return True

    def get_pending_friend_requests(self):
        return Request.get_request_objects(self.db_helper.get_unconfirmed_friend_requests(self.user_id))

    def get_pending_group_join_requests(self):
        return Request.get_request_objects(self.db_helper.get_unconfirmed_group_join_requests(self.user_id))

    # Accepts all of the users friend requests. Returns True if successful, false otherwise.
    def accept_all_friend_requests(self):
        if not self.db_helper.accept_all_friend_requests(self.user_id) == Status.INSERT_SUCCESS:
            return False
        return True

    # Accepts a friend request from user_id. Returns True if successful, false otherwise.
    def accept_friend_request_from(self, user_id):
        if not self.db_helper.create_friendship(user_id, self.user_id) == Status.INSERT_SUCCESS:
            return False
        return True

    # Deletes a friend request from user_id. Returns True if successful, false otherwise.
    def delete_friend_request_from(self, user_id):
        if not self.db_helper.delete_friend_request(user_id, self.user_id) == Status.DELETE_SUCCESS:
            return False
        return True

    # Accepts a group join request from user_id for the group group_id.
    # Returns True if successful, false otherwise.
    def accept_group_join_request_from(self, user_id, group_id):
        if not self.db_helper.check_is_group_manager(self.user_id, group_id):
            return False
        if not self.db_helper.add_group_member(user_id, group_id) == Status.INSERT_SUCCESS:
            return False
        return True

    # Deletes a group join request from user_id for the group group_id.
    # Returns True if successful, false otherwise.
    def delete_group_join_request_from(self, user_id, group_id):
        if not self.db_helper.check_is_group_manager(self.user_id, group_id):
            return False
        if not self.db_helper.delete_group_join_request(user_id, group_id) == Status.DELETE_SUCCESS:
            return False
        return True

    def get_all_friends(self):
        return User.get_user_objects(self.db_helper.get_all_friends(self.user_id))


    # Given a list of dictionaries of user profiles,
    # returns a list of User objects with the user_id, f_name, l_name, email attributes set.
    @staticmethod
    def get_user_objects(profiles):
        if not profiles:
            return []
        return list(map(lambda profile : User(user_id = profile["userID"],
                        f_name = profile["fname"], l_name = profile["lname"],
                        email = profile["email"], dob = profile["DOB"]), profiles))
