#!/bin/bash
celery -A traffic_handling worker -B --loglevel=info --file=tests/resources/test_access.log
