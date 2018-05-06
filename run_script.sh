#!/bin/bash

psql -f initialise.sql social_club_nyuad
python populate.py social_club_nyuad aadijoshi pass
python App.py social_club_nyuad aadijoshi pass
