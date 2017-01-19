INITDB=initdb
CREATEDB=createdb
PSQL=psql
PG_CTL=pg_ctl
SCHEMADATA=./schemadata
VENV=venv
PIP=./venv/bin/pip
PYTHON=./venv/bin/python


$(SCHEMADATA):
	$(INITDB) -D $(SCHEMADATA)
	$(PG_CTL) -D $(SCHEMADATA) -l logfile start
	sleep 1

clean: 
	$(PG_CTL) -D $(SCHEMADATA) -l logfile stop
	sleep 1
	rm -fr $(SCHEMADATA)

init: $(SCHEMADATA)
	$(CREATEDB) docstore

schema:
	$(PSQL) docstore -f schema.sql


$(VENV):
	virtualenv --no-site-packages $(VENV)
	$(PIP) install -U pip

requirements: $(VENV)
	$(PIP) install psycopg2
	$(PIP) install ujson
	$(PIP) install json_merge_patch

clean-venv:
	rm -fr $(VENV)

test: $(VENV)
	$(PYTHON) -m unittest discover
