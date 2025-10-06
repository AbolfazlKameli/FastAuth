#!/bin/sh

# Author: Denver
# Version: v0.3.0
# Date: 10/6/25
# Description: entrypoint for FastAuth API.
# Usage: ./entrypoint.sh

alembic upgrade head

uvicorn src.main:app --workers 5 --host 0.0.0.0 --port 8000
