# Cuisine Crafter (Streamlit + LangChain)

Generate a fancy restaurant name and a menu from a chosen cuisine using LangChain and OpenAI. Built with Streamlit.

## Features
- Choose a cuisine or type your own
- Generates a fancy restaurant name
- Generates a category wise menu items and displays them

## Quickstart

### 1) Clone and install
```bash
git clone https://github.com/viveksudani/cuisine-crafter.git
cd cuisine-crafter

# optional steps (create an activate virtual environment):
# python -m venv .venv
# .venv/Scripts/activate  # Windows PowerShell

pip install -r requirements.txt
```

### 2) Configure API key
Create a `.env` file (copy from `.env.example`) and set your OpenAI key:
```bash
cp .env.example .env
# edit .env and set OPENAI_API_KEY
```

### 3) Run Streamlit app
```bash
streamlit run web.py
```

Open the printed local URL in your browser.

## How it works
- Uses `langchain`'s `init_chat_model` to create an OpenAI chat model (`gpt-4o-mini`).
- Step 1: Prompt to produce a single restaurant name from the cuisine.
- Step 2: Prompt to produce comma-separated menu items from the name.
- Implemented with LangChain Runnables and a `StrOutputParser` for clean strings.

Key code is in `web.py`.

