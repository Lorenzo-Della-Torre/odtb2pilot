#!/bin/bash
echo "user is ${USER}"
docker run --rm -it -d --privileged=true --net=host -v $PWD/configuration/:/signalbroker/_build/prod/rel/signal_server/configuration aleksandarf/signalbroker-server:travis-12-arm32
