#!/bin/bash
set -e

echo "Compiling Tailwind CSS..."
./app/static/tailwindcss -i ./app/static/css/input.css -o ./app/static/css/output.css --minify

echo "Initializing Database..."
source .venv/bin/activate
python run.py init-db

echo "Starting TestAura AI..."
python run.py
