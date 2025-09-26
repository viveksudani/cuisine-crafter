import os
import json
import streamlit as st
from dotenv import load_dotenv

# Load env vars (e.g., OPENAI_API_KEY)
load_dotenv()

from langchain.chat_models import init_chat_model
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser


st.set_page_config(page_title="Cuisine Crafter", page_icon="✨")
st.title("Cuisine Crafter")
st.write(
    "Generate a fancy restaurant name and a menu based on a chosen cuisine."
)


def create_model(provider: str, model_name: str):
    """Create and return a chat model for the selected provider and model.

    The appropriate API key must be present in the environment.
    """
    return init_chat_model(model_name, model_provider=provider)


def build_chain(model):
    """Build the two-step chain: cuisine -> restaurant_name -> menu items."""
    output_parser = StrOutputParser()

    name_template = PromptTemplate.from_template(
        "I want to open a {diet} {cuisine} restaurant. Suggest a fancy name for this. only return one name. Do not return any other words"
    )
    name_chain = {"cuisine": RunnablePassthrough(), "diet": RunnablePassthrough()} | name_template | model | output_parser

    json_schema = {
        "categories": [
            {
                "name": "Starters",
                "items": [{"name": "Item Name", "ingredients": ["ing1", "ing2", "ing3"], "price": 12.5}]
            }
        ]
    }
    json_schema_str = json.dumps(json_schema)
    # Escape curly braces so PromptTemplate treats JSON as literal text
    escaped_json_schema_str = json_schema_str.replace("{", "{{").replace("}", "}}")

    items_template = PromptTemplate.from_template(
        (
            "For the restaurant {restaurant_name} with {cuisine} cuisine, suggest a {diet} menu organized into 2-3 categories."
            "Use realistic category names like 'Starters', 'Main Course', 'Desserts'. "
            "Return STRICT JSON only with this schema:" + escaped_json_schema_str + " "
            "Prices should be reasonable as integrers in INR. No extra commentary."
        )
    )

    full_chain = (
        {"restaurant_name": name_chain, "cuisine": RunnablePassthrough(), "diet": RunnablePassthrough()}
        | items_template
        | model
        | output_parser
    )
    return name_chain, full_chain


with st.sidebar:
    st.header("Cuisine")
    cuisine_options = (
        "Indian",
        "Mexican",
        "Chinese",
        "Italian",
        "Arabic",
        "French",
        "Japanese",
        "Thai",
        "Greek",
    )
    selected_cuisine = st.selectbox("Select cuisine", options=cuisine_options, index=0)
    custom_cuisine = st.text_input("Or type a custom cuisine", placeholder="e.g., Peruvian")
    diet_choice = st.radio("Diet preference", options=("Veg", "Non-Veg"), index=0, horizontal=True)
    generate = st.button("Generate", type="primary")

    st.divider()
    st.header("Model")
    # Popular provider/model options. Labels are user-friendly; values map to provider+model.
    model_options = [
        {"label": "OpenAI — GPT-4o-mini", "provider": "openai", "model": "gpt-4o-mini", "env": "OPENAI_API_KEY"},
        {"label": "OpenAI — GPT-4o", "provider": "openai", "model": "gpt-4o", "env": "OPENAI_API_KEY"},
        {"label": "OpenAI — o3-mini", "provider": "openai", "model": "o3-mini", "env": "OPENAI_API_KEY"},
        {"label": "Anthropic — Claude 3.5 Sonnet", "provider": "anthropic", "model": "claude-3-5-sonnet-20240620", "env": "ANTHROPIC_API_KEY"},
        {"label": "Google — Gemini 1.5 Flash", "provider": "google", "model": "gemini-1.5-flash", "env": "GOOGLE_API_KEY"},
        {"label": "Groq — Llama-3.1 70B", "provider": "groq", "model": "llama-3.1-70b-versatile", "env": "GROQ_API_KEY"},
        {"label": "Mistral — Mistral Large", "provider": "mistralai", "model": "mistral-large-latest", "env": "MISTRAL_API_KEY"},
        {"label": "OpenRouter — Claude 3.5 Sonnet", "provider": "openrouter", "model": "anthropic/claude-3.5-sonnet", "env": "OPENROUTER_API_KEY"},
    ]
    model_labels = [m["label"] for m in model_options]
    selected_label = st.selectbox("Choose model", options=model_labels, index=0)
    selected_model_cfg = next(m for m in model_options if m["label"] == selected_label)


required_env_var = selected_model_cfg["env"]
api_key_present = bool(os.getenv(required_env_var))
if not api_key_present:
    st.warning(
        f"{required_env_var} is not set. Add it to a .env file or your environment to run the app."
    )


if generate:
    cuisine = custom_cuisine.strip() if custom_cuisine.strip() else selected_cuisine
    diet = "vegetarian" if diet_choice == "Veg" else "non-vegetarian"

    if not api_key_present:
        st.stop()

    try:
        model = create_model(selected_model_cfg["provider"], selected_model_cfg["model"])
        name_chain, full_chain = build_chain(model)

        with st.spinner("Generating restaurant name..."):
            restaurant_name = name_chain.invoke({"cuisine": cuisine, "diet": diet})

        st.subheader("Restaurant Name")
        st.success(restaurant_name)

        with st.spinner("Creating menu items..."):
            menu_json_str = full_chain.invoke({"cuisine": cuisine, "diet": diet})

        st.subheader("Menu")
        parsed = None
        cleaned = menu_json_str
        # Strip markdown code fences if present
        if cleaned.strip().startswith("```"):
            try:
                import re
                match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned, flags=re.IGNORECASE)
                if match:
                    cleaned = match.group(1)
            except Exception:
                cleaned = menu_json_str
        # Attempt JSON parse on cleaned content
        try:
            parsed = json.loads(cleaned)
        except Exception:
            parsed = None

        if isinstance(parsed, dict) and isinstance(parsed.get("categories"), list):
            currency = "₹"
            for category in parsed["categories"]:
                name = category.get("name", "Category")
                st.markdown(f"**{name}**")
                items = category.get("items", [])
                if not items:
                    st.caption("No items returned")
                    continue
                for item in items:
                    item_name = item.get("name", "Item")
                    ingredients = item.get("ingredients", [])
                    price = item.get("price", "-")
                    ing_text = ", ".join(ingredients) if isinstance(ingredients, list) else str(ingredients)
                    price_text = f"{currency}{price}" if isinstance(price, (int, float)) else str(price)
                    st.markdown(f"- {item_name} — {price_text}")
                    st.caption(f"Ingredients: {ing_text}")
        else:
            # Fallback: show raw content if JSON parsing failed
            st.warning("Could not parse structured menu. Showing raw model output.")
            st.code(menu_json_str)

        with st.expander("Details"):
            st.caption("Raw model outputs")
            st.code(
                f"cuisine: {cuisine}\ndiet: {diet}\nrestaurant_name: {restaurant_name} \nmenu_json_str: {menu_json_str}"
            )

    except Exception as error:
        st.error(f"An error occurred: {error}")
