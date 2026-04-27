#!/bin/bash
cd benchmarks/
[ ! -d venv ] && python3 -m venv venv && source venv/bin/activate && pip install -q -r requirements.txt
source venv/bin/activate
python3 main.py $@
