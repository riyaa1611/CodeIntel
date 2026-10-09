@echo off
echo === CodeIntel Startup ===

echo [1/3] Building React frontend...
cd frontend
call npm install --silent
call npm run build
cd ..

echo [2/3] Installing Python dependencies...
cd backend
pip install -r requirements.txt --quiet
cd ..

echo [3/3] Starting CodeIntel server...
echo.
echo Dashboard available at: http://127.0.0.1:8000
echo API documentation at:   http://127.0.0.1:8000/docs
echo.
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
