#!/bin/bash
# Double-click to launch AIOS Dashboard.
cd "$(dirname "$0")"
echo "Starting AIOS Dashboard..."
python3 dashboard/server.py
