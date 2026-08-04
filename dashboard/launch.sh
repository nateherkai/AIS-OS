#!/bin/bash
cd "$(dirname "$0")/.."
echo "Starting Ag Coach Pro AIOS Dashboard..."
python3 dashboard/server.py
