#!/bin/sh
echo "Now waiting for opsdroid to start "
sleep 60
echo "Now Starting Opsdroid after 60 seconds"
opsdroid start -f /configurations/configuration.yaml