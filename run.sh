#!/bin/bash
cd TheWebsite/
python3 -m pipenv run python3 -m uvicorn WebService:app --host 0.0.0.0
