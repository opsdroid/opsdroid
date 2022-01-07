#!bin/sh

./wait-for http://rasa:5005 -- echo "The rasa container is up and running! Now starting Opsdroid!"