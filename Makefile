install:
	test -d venv || virtualenv venv
	. venv/bin/activate && pip install -r requirements.txt

run-chatbot:
	streamlit run chatbot/bot.py
