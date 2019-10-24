.PHONY: clean list install test run db model shell recreate_db migrate all

clean:
	find . -type f -name '*.pyc' -delete
	find . -type f -name '*.log' -delete

list:
	grep -e "^.*:$$" Makefile

install:
	poetry install

test:
	# poetry run pytest -s tests
	poetry run pytest tests/test_apis.py|grep -v .venv/lib/python3.7/site-packages/|grep -v DeprecationWarning

run:
	FLASK_ENV="development" python3 -u manage.py runserver

db:
	FLASK_ENV="development" python3 -u manage.py db

model:
	flask-sqlacodegen sqlite:////tmp/test.db|sed -e"s/\(Base\)/BaseModel/"

route:
	FLASK_ENV="development" python3 -u manage.py list_routes

shell:
	FLASK_ENV="development" python3 -u manage.py shell

recreate_db:
	FLASK_ENV="development" python3 -u manage.py recreate_db

migrate:
	FLASK_ENV="development" python3 -u manage.py db migrate
	FLASK_ENV="development" python3 -u manage.py db upgrade

# init:
# 	python3 -u manage.py drop_all
# 	python3 -u manage.py init_db

all: clean install test run
