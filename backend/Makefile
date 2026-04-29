PY = py

init: 
	@echo "Initializing the project..."
	$(PY) -m venv venv
	@echo "Virtual environment created. Please activate it before running 'make install'."


install: 
	@echo "Installing dependencies..."
	$(PY) -m pip install -r requirements.txt

build: 
	@echo "Running data ingestion..."
	$(PY) -m preprocessing_scripts.run_ingestion

run:
	@echo "Running the application..."
	$(PY) ./app.py


build-run: build run

all : install build-run