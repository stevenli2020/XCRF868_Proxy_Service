#!/bin/bash
if [ ! -f /app/run.py ]; then
    curl https://raw.githubusercontent.com/stevenli2020/XCRF868_Proxy_Service/master/source/run.py > /app/run.py
fi
python3 /app/run.py