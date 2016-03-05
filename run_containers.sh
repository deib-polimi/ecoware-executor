#!/bin/bash
docker run -it -d -p 8080:5000 --add-host="db:172.31.31.123" --name pwitter-web pwitter-web -w 3 -k eventlet
docker run -it -d -p 80:8080 --add-host="db:172.31.31.123" --name rubis-jboss polimi/rubis-jboss:nosensors /opt/jboss-4.2.2.GA/bin/run.sh --host=0.0.0.0 --bootdir=/opt/rubis/rubis-cvs-2008-02-25/Servlets_Hibernate -c default
