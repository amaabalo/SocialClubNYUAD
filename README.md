# Instructions

* Create a database with a chosen name, e.g. 'social\_club\_nyuad':
	```
	CREATE DATABASE social_club_nyuad;
	```

* Initialise the database's relations:
	```
	psql -f initialise.sql social_club_nyuad
	```

* Populate the database:
	```	
	python populate.py social_club_nyuad <USER> <PASSWORD>
	```
* Test the TUI:
	```
	python App.py <DATABASE> <USER> <PASSWORD>
	```
