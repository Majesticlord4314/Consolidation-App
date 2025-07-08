@echo off
REM Create venv if it doesn't exist
if not exist .venv (
    python -m venv .venv
)

REM Activate venv
call .venv\Scripts\activate

REM Upgrade pip just in case
python -m pip install --upgrade pip

REM Install requirements
pip install -r requirements.txt

REM Run Streamlit app
streamlit run main.py
