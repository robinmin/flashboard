.PHONY: clean list install test run db model shell recreate_db migrate i18n setup all

clean:
	find . -type f -name '*.pyc' -delete
	find . -type f -name '*.log' -delete

list:
	grep -e "^.*:$$" Makefile

install:
	poetry install

test:
	poetry run pytest tests|grep -v .venv/lib/python3.7/site-packages/|grep -v DeprecationWarning
	# poetry run pytest tests/test_apis.py|grep -v .venv/lib/python3.7/site-packages/|grep -v DeprecationWarning

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

i18n:
	# extract i18n string table from source code
	pybabel extract -F babel.cfg -k lazy_gettext -o flashboard/translations/messages.pot .

	## prepare to translate into zh_Hans_CN
	test -s flashboard/translations/zh_Hans_CN/LC_MESSAGES/messages.po || pybabel init -i flashboard/translations/messages.pot -d flashboard/translations -l zh_Hans_CN

	# create translation files for the supported languages
	pybabel update -i flashboard/translations/messages.pot -d flashboard/translations

	# compile Translations
	pybabel compile -d flashboard/translations

setup:
	dephell deps convert

lint:
	poetry run flake8 *.py flashboard tests

all: clean install test run
