#!/bin/bash

rm -rf db.sqlite3
python manage.py migrate
