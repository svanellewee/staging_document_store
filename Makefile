INITDB=initdb
CREATEDB=createdb
PSQL=psql
PG_CTL=pg_ctl
SCHEMADATA=./schemadata
VENV=venv
PIP=./venv/bin/pip
PYTHON=./venv/bin/python
DOCKER_MACHINE_IP=192.168.99.100

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

docker-start: 
	source ./scripts/env-setup.sh && \
	cd tests/ &&  \
	../$(VENV)/bin/docker-compose pull &&  \
	../$(VENV)/bin/docker-compose up -d && \
	echo "Sleeping" && sleep 10

docker-stop: 
	source ./scripts/env-setup.sh && \
	cd tests/ && \
	../$(VENV_DIR)/bin/docker-compose kill && \
	../$(VENV_DIR)/bin/docker-compose rm -f



docker-ps:
	source ./scripts/env-setup.sh && \
	docker ps

docker-postgres-ssh:
	source ./scripts/env-setup.sh && \
	docker exec -it  tests_postgres_1  /bin/bash

docker-elasticsearch-ssh:
	source ./scripts/env-setup.sh && \
	docker exec -it  tests_elasticsearch_1  /bin/bash
