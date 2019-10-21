.PHONY: clean list install test run db shell recreate_db all

clean:
	find . -type f -name '*.pyc' -delete
	find . -type f -name '*.log' -delete

list:
	grep -e "^.*:$$" Makefile

install:
	poetry install

test:
	poetry run pytest -s tests

run:
	FLASK_ENV="development" python3 -u manage.py runserver

db:
	FLASK_ENV="development" python3 -u manage.py db

shell:
	FLASK_ENV="development" python3 -u manage.py shell

recreate_db:
	FLASK_ENV="development" python3 -u manage.py recreate_db

init:
	# python3 -u manage.py drop_all
	# python3 -u manage.py init_db

all: clean install test run
