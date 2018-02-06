#!/bin/bash
#celery -A traffic_handling worker -B --loglevel=info --logfile=logs/traffic_handling.log --file=/opt/squid/Traffic-Handling/tests/resources/test_access.log
celery -A traffic_handling worker -B --loglevel=info --logfile=logs/traffic_handling.log
