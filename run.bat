@echo off
set FLASK_APP=app.py
python -m pip install -r requirements.txt
python app.py
pause