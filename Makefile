SCHEMADATA=./schemadata
VENV=./venv/
PIP=$(VENV)/bin/pip
PYTHON=$(VENV)/bin/python
DOCKER_MACHINE_IP=192.168.99.100
DOCKER_POSTGRES_PORT=5432
DOCKER_ELASTIC_PORT=9200
PSQL=psql -h $(DOCKER_MACHINE_IP) -p $(DOCKER_POSTGRES_PORT) -U postgres
INITDB=initdb -h $(DOCKER_MACHINE_IP) -p $(DOCKER_POSTGRES_PORT) -U postgres
CREATEDB=createdb -h $(DOCKER_MACHINE_IP) -p $(DOCKER_POSTGRES_PORT) -U postgres
PG_CTL=pg_ctl
ELASTICSEARCH=$(DOCKER_MACHINE_IP):$(DOCKER_ELASTIC_PORT)

# $(PG_CTL) -D $(SCHEMADATA) -l logfile start
$(SCHEMADATA):
	$(INITDB) -D $(SCHEMADATA) 
	sleep 1

#$(PG_CTL) -D $(SCHEMADATA) -l logfile stop
clean: 
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
	$(PIP) install docker-compose
	$(PIP) install requests

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

docker-elastic-status:
	curl $(ELASTICSEARCH)


docker-elastic-full:
	curl -XGET $(ELASTICSEARCH)/staging_document_store/full_document/?pretty=true	
	curl -XGET $(ELASTICSEARCH)/staging_document_store/full_document/_search?pretty=true

docker-elastic-diff:
	curl -XGET $(ELASTICSEARCH)/staging_document_store/difference_document/_search?pretty=true
