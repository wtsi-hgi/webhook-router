# webhook-router

A system that accepts incoming webhooks from the Internet and routes them to internal locations, depending on a configuration that can be dynamically modified by users.

## Running using docker-compose

### On Mac:
When running on mac, docker has a memory limit of 2GB, which is the exact amount of memory required by elastic search. To run this you need to increase the amount of memory allocated for the docker deamon

Once you run docker-compose the UI is accessible from `http://localhost:8080/` (NOTE: not 127.0.0.1 or the google API won't work) and kibana is accessible from `http://localhost:5601/`