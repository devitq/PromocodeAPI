#!/bin/bash

GREEN='\033[1;32m'
NC='\033[0m'

uvx ruff format .
uvx ruff check . --fix
printf "${GREEN}Linters/formatters runned${NC}\n"

uv run python manage.py makemigrations --check
uv run python manage.py test
printf "${GREEN}Tests runned${NC}\n"
