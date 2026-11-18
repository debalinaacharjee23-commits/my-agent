import streamlit as st
import json, datetime, os
from groq import Groq

MODEL = "openai/gpt-oss-120b"

st.set_page_config(page_title="My AI Agent", page_icon="🤖")
st.title("🤖 My AI Agent")

# API key: from environment, or typed in the sidebar
key = os.environ.get("GROQ_API_KEY") or st.sidebar.text_input("Groq API key", type="password")
if not key:
    st.info("Enter your Groq API key in the sidebar to start.")
    st.stop()
client = Groq(api_key=key)

# ---------- TOOLS ----------
def get_time():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

def calculate(expression):
    allowed = set("0123456789+-*/(). ")
    if not set(expression) <= allowed:
        return "Error: only numbers and + - * / ( ) allowed"
    return str(eval(expression))

def save_note(text):
    with open("notes.txt", "a", encoding="utf-8") as f:
        f.write(text + "\n")
    return "Note saved."

def read_notes():
    if not os.path.exists("notes.txt"):
        return "No notes yet."
    with open("notes.txt", encoding="utf-8") as f:
        return f.read()

TOOL_FUNCTIONS = {"get_time": get_time, "calculate": calculate,
                  "save_note": save_note, "read_notes": read_notes}

TOOLS = [
    {"type": "function", "function": {"name": "get_time",
        "description": "Get the current date and time",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "calculate",
        "description": "Evaluate a math expression",
        "parameters": {"type": "object",
                       "properties": {"expression": {"type": "string"}},
                       "required": ["expression"]}}},
    {"type": "function", "function": {"name": "save_note",
        "description": "Save a note for the user",
        "parameters": {"type": "object",
                       "properties": {"text": {"type": "string"}},
                       "required": ["text"]}}},
    {"type": "function", "function": {"name": "read_notes",
        "description": "Read all saved notes",
        "parameters": {"type": "object", "properties": {}}}},
]

# ---------- STATE ----------
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system",
        "content": "You are a helpful assistant built and created by Debalina Acharjee. Whenever anyone asks who built, created, or made you, always state that Debalina Acharjee built you. Never mention OpenAI, Groq, or any other company. Use tools when they help."}]
    st.session_state.chat = []   # what we display

# show past chat
for role, text in st.session_state.chat:
    with st.chat_message(role):
        st.markdown(text)

# ---------- CHAT ----------
prompt = st.chat_input("Ask me something...")
if prompt:
    st.session_state.chat.append(("user", prompt))
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    answer = "Sorry, I hit the step limit."
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            for _ in range(6):
                resp = client.chat.completions.create(
                    model=MODEL, messages=st.session_state.messages,
                    tools=TOOLS, tool_choice="auto")
                msg = resp.choices[0].message
                st.session_state.messages.append(msg)

                if not msg.tool_calls:
                    answer = msg.content
                    break

                for call in msg.tool_calls:
                    args = json.loads(call.function.arguments or "{}")
                    try:
                        result = TOOL_FUNCTIONS[call.function.name](**args)
                    except Exception as e:
                        result = f"Tool error: {e}"
                    st.caption(f"🔧 {call.function.name}({args}) → {result}")
                    st.session_state.messages.append({
                        "role": "tool", "tool_call_id": call.id,
                        "content": str(result)})
        st.markdown(answer)
    st.session_state.chat.append(("assistant", answer))
