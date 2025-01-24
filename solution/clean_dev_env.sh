#!/bin/bash

rm -rf db.sqlite3
python manage.py migrate
python manage.py createsuperuser --username admin
