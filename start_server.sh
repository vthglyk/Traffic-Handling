#!/bin/bash
#export oam_url=http://10.30.0.227:8001/services/vcache/traffic
export oam_url=$1
FLASK_APP=server.py flask  run