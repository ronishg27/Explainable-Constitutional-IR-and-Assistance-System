PY = backend\.venv\Scripts\python.exe

backend:
	$(PY) ./backend/app.py

frontend:
	cd frontend && npm run dev

run:
	powershell -Command "Start-Process cmd -ArgumentList '/k \"$(PY) ./backend/app.py\"' -WindowStyle Normal"
	powershell -Command "Start-Process cmd -ArgumentList '/k cd frontend && npm run dev' -WindowStyle Normal"