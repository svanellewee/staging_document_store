#!/usr/bin/env bash
# To be called
#    source ./scripts/env-setup.sh
#

function docker_machine_setup() {
    DOCKER_MACHINE=`which docker-machine`
    if [ "x$DOCKER_MACHINE" == "x" ]; then
	echo "No docker machine";
	exit 0;
    fi
    
    echo "Docker machine $DOCKER_MACHINE"
    
    if [ "$(docker-machine status)" != "running" ]; then
	docker-machine start
    fi
    
    eval $($DOCKER_MACHINE env)
}

docker_machine_setup
