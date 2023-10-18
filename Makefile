install:
	virtualenv venv
	source venv/bin/activate
	pip install -r requirements.txt

run-chatbot:
	streamlit run chatbot/bot.py
