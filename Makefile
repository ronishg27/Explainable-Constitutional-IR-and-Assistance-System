.DEFAULT_GOAL := run

.PHONY: backend frontend run

PY := backend\.venv\Scripts\python.exe

backend:
	cd backend && .venv\Scripts\python.exe app.py

frontend:
	cd frontend && npm run dev

run:
	powershell -Command "Start-Process cmd -ArgumentList '/k ""cd backend && .venv\Scripts\python.exe app.py""'"
	powershell -Command "Start-Process cmd -ArgumentList '/k ""cd frontend && npm run dev""'"