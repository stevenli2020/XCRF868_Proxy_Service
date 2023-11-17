# XCRF868_Proxy_Service

### Purpose
To be deploed on Invengo XC-RF868, scan tags, create report and submit to server

### Usage
1. ssh into XC-RF868
2. install docker-compose
3. create folder /scanproxy
4. download docker-compose.yml, save to /scanproxy/docker-compose.yml
5. adjust the SERVICE_CONFIG in the docker-compose.yml
6. cd into /scanproxy
7. run: docker-compose up -d
8. Voilà
