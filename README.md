# webhook-router

A system that accepts incoming webhooks from the Internet and routes them to internal locations, depending on a configuration that can be dynamically modified by users. 

## Running using docker-compose

Note: when running on mac, docker has a memory limit of 2GB, which is the exact amount of memory required by elastic search. To run this you need to increase the amount of memory for docker.
```bash
cd webhook-router
docker-compose up
```