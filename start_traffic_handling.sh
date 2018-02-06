#!/bin/bash
screen -dm -S traffic-handling /opt/squid/Traffic-Handling/start_server.sh http://10.30.0.227:8001/services/vcache/traffic 5
