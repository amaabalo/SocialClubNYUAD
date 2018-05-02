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

    def error_string(self, status):
        if status == self.CONN_FAIL:
            return "Connection faied."
        if status == self.CONN_SUCCESS:
            return "Connection successful."
        if status == self.USERNAME_PASS_DNE:
            return "Username does not exist."
        if status == self.LOGIN_SUCCESS:
            return "Log in successful."
        if status == self.DATABASE_ERROR:
            return "DATABASE_ERROR"
        if status == self.USERNAME_ALREADY_EXISTS:
            return "Username already exists."
        if status == self.EMAIL_ALREADY_EXISTS:
            return "Email already exists."
        if status == self.USERNAME_PASS_DNM:
            return "Username and password do not match."
        if status == self.CREATE_SUCESS:
            return "User successfully created."
        if status == self.CREATE_LOG_IN_SUCCESS:
            return "User successfully created and logged in."

class DatabaseHelper:
    __instance = None

    def __init__(self):
        if DatabaseHelper.__instance != None:
            raise Exception("An instance of DatabaseHelper already exists. Use get_instance() instead.")
        else:
            DatabaseHelper.__instance = self
            self.conn = psycopg2.connect("dbname=" + sys.argv[1] + " user=" + sys.argv[2] + " password=" + sys.argv[3] + " host=127.0.0.1")
            self.cur = self.conn.cursor()

    @staticmethod
    def get_instance():
        if DatabaseHelper.__instance == None:
            DatabaseHelper()
        return DatabaseHelper.__instance


    def get_attributes_nullabities(self, table_name):
        SQL =  "SELECT column_name, is_nullable FROM information_schema.columns WHERE table_name = %s"
        data = (table_name,)
        self.cur.execute(SQL, data)
        results = self.cur.fetchall()
        dict = {}
        for result in results:
            dict[result[0]] = True if result[1] == 'YES' else False
        return dict

    # will only return attributes that have a maximum length specified
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

    def check_username_exists(self, username):
        SQL = "SELECT * FROM profile WHERE userID = %s"
        self.cur.execute(SQL, (username,))
        results = self.cur.fetchall()
        if (len(results) > 0):
            return True
        return False

    def check_email_exists(self, email):
        SQL = "SELECT * FROM profile WHERE email = %s"
        self.cur.execute(SQL, (email,))
        results = self.cur.fetchall()
        if (len(results) > 0):
            return True
        return False





class User:

    def __init__(self):
        # connect to database here
        success = self.create_connection()
        if (not success):
            raise Error('Could not connect to database.')
        self.user_id = ''
        self.f_name = ''
        self.l_name = ''
        self.email = ''
        self.logged_in = False

    def create_connection(self):
        try:
            self.conn = psycopg2.connect("dbname=" + sys.argv[1] + " user=" + sys.argv[2] + " password=" + sys.argv[3] + " host=127.0.0.1")
            self.cur = self.conn.cursor()
        except Exception as e:
            return False
        return True

    def get_profile_records(self, results):
        rval = []
        print
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

    def log_in(self, username, password):
        if not self.check_username_exists(username):
            return Status.USERNAME_PASS_DNE
        SQL = "SELECT * FROM profile WHERE userID = %s"
        self.cur.execute(SQL, (username,))
        results = self.cur.fetchall()
        result = self.get_profile_records(results)[0]
        if (result["password"] != password):
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
        self.conn.close()

    def check_username_exists(self, username):
        SQL = "SELECT * FROM profile WHERE userID = %s"
        self.cur.execute(SQL, (username,))
        results = self.cur.fetchall()
        if (len(results) > 0):
            return True
        return False

    def check_email_exists(self, email):
        SQL = "SELECT * FROM profile WHERE email = %s"
        self.cur.execute(SQL, (email,))
        results = self.cur.fetchall()
        if (len(results) > 0):
            return True
        return False

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


    def create_and_log_in(self, username, f_name, l_name, email, password, DOB):
        res = self.create_new_user(username, f_name, l_name, email, password, DOB)
        if (res != Status.CREATE_SUCCESS):
            return res
        if self.log_in(username, password) == Status.LOGIN_SUCCESS:
            return Status.CREATE_LOG_IN_SUCCESS
