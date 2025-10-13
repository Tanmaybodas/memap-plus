.PHONY: install run fmt

install:
	python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

run:
	streamlit run app.py
