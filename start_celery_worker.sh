#!/bin/bash
celery -A traffic_handling worker -B --loglevel=info --logfile=logs/traffic_handling.log --file=tests/resources/test_access.log
