import psycopg2
import sys
import random
import time
import datetime
import string

if (len(sys.argv) != 4):
	print("Usage: python populate.py <DATABASE NAME> <USER> <PASSWORD>")
fname_file = open('first_names.txt', 'r')
lname_file = open('last_names.txt', 'r')
noun_file = open('nouns.txt', 'r')
adjective_file = open('adjectives.txt', 'r')
first_names = fname_file.readlines()
last_names = lname_file.readlines()
nouns = noun_file.readlines()
adjectives = adjective_file.readlines()
fname_file.close()
lname_file.close()
adjective_file.close()
noun_file.close()

#conn = psycopg2.connect("dbname=" + sys.argv[1] +" host=127.0.0.1")
conn = psycopg2.connect("dbname=" + sys.argv[1] + " user=" + sys.argv[2] + " password=" + sys.argv[3] + " host=127.0.0.1")
cur = conn.cursor()


# Inserts random users
def insertUsers(n_users):
	for i in range(n_users):
		userID = (str(i + 1))#.zfill(20) # pad with 0s
		fname = random.choice(first_names).strip()
		lname = random.choice(last_names).strip()
		email = fname[0].lower() + lname[0].lower() + str(i + 1) + '@nyu.edu'
		password = 'password'
		day = str(random.randint(1, 28))
		month = str(random.randint(1, 12))
		year = str(random.randint(1990, 2002))
		DOB = year + '-' + month + '-' + day
		ts = time.time()
		lastlogin = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

		try:
			cur.execute('INSERT INTO profile(userID, fname, lname, email, password, DOB, lastlogin) VALUES (%s, %s, %s, %s, %s, %s, %s);',\
		 	(userID, fname, lname, email, password, DOB, lastlogin))
			conn.commit()
		except psycopg2.IntegrityError:
			conn.rollback()

# Inserts random friendships
def insertFriendships(n_users, n_friendships):
	n_possible_friendships = (n_users * (n_users - 1)) / 2
	if (n_friendships > n_possible_friendships):
		return -1

	t = float(n_friendships) / n_possible_friendships
	count = 0
	while (count < n_friendships) :
		for i in range(n_users - 1):
			for j in range(i + 1, n_users):
				x = random.uniform(0, 1)
				if (x <= t):
					userID1 = str(i + 1)#.zfill(20)
					userID2 = str(j + 1)#.zfill(20)
					ts = time.time()
					friendshipDate = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
					try:
						cur.execute('INSERT INTO friends(userID1, userID2, friendshipDate) VALUES (%s, %s, %s)', (userID1, userID2, friendshipDate))
						conn.commit()
						count += 1;
					except psycopg2.IntegrityError:
						conn.rollback()
	return 1

def insertGroups(n_groups, n_users):
	for i in range(n_groups):
		#create group
		gID = str(i + 1)#.zfill(20)
		word1 = random.choice(adjectives).strip()
		word2 = random.choice(nouns).strip()
		name = word1 + '-' + word2
		lmt = random.randint(10, 25)
		description = word1 + " " + word2 + "."
		try:
			cur.execute('INSERT INTO groups(gID, name, lmt, description) VALUES (%s, %s, %s, %s)', (gID, name, lmt, description))
			conn.commit()
		except psycopg2.IntegrityError:
			conn.rollback()

		#add members
		members = random.sample(range(1, n_users + 1), random.randint(2, lmt))
		manager = random.choice(members)

		for member in members:
			try:
				if member == manager:
					role = 'manager'
				else:
					role = 'member'
				userID = str(member)#.zfill(20)
				cur.execute('INSERT INTO groupMembership(gID, userID, role) VALUES (%s, %s, %s)', (gID, userID, role))
				conn.commit()
			except psycopg2.IntegrityError:
				conn.rollback()

def insertMessages(n_users, n_groups, n_messages):
	for i in range(n_messages):
		user1, user2, gID = 'NULL', 'NULL', 'NULL'
		msgID = str(i+1).zfill(20)
		user1 = str(random.randint(1, n_users))#.zfill(20)

		to_user = random.randint(0, 2)
		if(to_user):
			#cannot send message to self
			user2 = str(random.randint(1, n_users))#.zfill(20)
			while user1 == user2:
				user2 = str(random.randint(1, n_users))#.zfill(20)
		else:
			gID = str(random.randint(1, n_groups))#.zfill(20)

		message = ''
		msg_len = random.randint(1, 200)
		selection = string.ascii_letters + string.digits + string.punctuation+string.whitespace
		for j in range(msg_len):
			message = message + random.choice(selection)

		ts = random.uniform(0,1)*time.time()
		date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

		if(gID == 'NULL'):
			gID = None
		else:
			user2 = None

		try:
			cur.execute('INSERT INTO messages (fromuserid, touserid, togroupid, message, datesent) VALUES (%s, %s, %s, %s, %s)', (user1, user2, gID, message, date))
			conn.commit()
		except psycopg2.IntegrityError as e:
			print(e)
			conn.rollback()

insertUsers(100)
insertFriendships(100, 300)
insertGroups(25, 100)
insertMessages(100, 25, 400)
