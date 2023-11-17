#!/bin/bash
if [ ! -f /app/run.py ]; then
    echo "File not found!"
fi
python3 /app/run.py