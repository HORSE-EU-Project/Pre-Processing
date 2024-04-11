#!/bin/sh

# Start Flask app in the background
python3 -u app.py &

# Start ElastAlert as the primary process in the foreground
exec elastalert --verbose --config ./elastalert/config.yaml
