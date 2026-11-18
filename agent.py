import json, datetime, os
from groq import Groq

client = Groq()  # reads GROQ_API_KEY automatically
MODEL = "openai/gpt-oss-120b"  # check console.groq.com/docs/models if rejected

# ---------- TOOLS (plain Python functions) ----------
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

TOOL_FUNCTIONS = {
    "get_time": get_time,
    "calculate": calculate,
    "save_note": save_note,
    "read_notes": read_notes,
}

# ---------- TOOL DESCRIPTIONS (what the model sees) ----------
TOOLS = [
    {"type": "function", "function": {
        "name": "get_time", "description": "Get the current date and time",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {
        "name": "calculate", "description": "Evaluate a math expression",
        "parameters": {"type": "object",
                       "properties": {"expression": {"type": "string"}},
                       "required": ["expression"]}}},
    {"type": "function", "function": {
        "name": "save_note", "description": "Save a note for the user",
        "parameters": {"type": "object",
                       "properties": {"text": {"type": "string"}},
                       "required": ["text"]}}},
    {"type": "function", "function": {
        "name": "read_notes", "description": "Read all saved notes",
        "parameters": {"type": "object", "properties": {}}}},
]

# ---------- THE AGENT LOOP ----------
messages = [{"role": "system",
             "content": "You are a helpful assistant built and created by Debalina Acharjee. Whenever anyone asks who built, created, or made you, always state that Debalina Acharjee built you. Never mention OpenAI, Groq, or any other company. Use tools when they help."}]

while True:
    user = input("\nYou: ")
    if user.lower() in ("quit", "exit"):
        break
    messages.append({"role": "user", "content": user})

    for _ in range(6):  # max 6 tool steps per question
        resp = client.chat.completions.create(
            model=MODEL, messages=messages, tools=TOOLS, tool_choice="auto")
        msg = resp.choices[0].message
        messages.append(msg)

        if not msg.tool_calls:        # model is done, show the answer
            print("Agent:", msg.content)
            break

        for call in msg.tool_calls:   # run each requested tool
            args = json.loads(call.function.arguments or "{}")
            try:
                result = TOOL_FUNCTIONS[call.function.name](**args)
            except Exception as e:
                result = f"Tool error: {e}"
            print(f"  [tool] {call.function.name}({args}) -> {result}")
            messages.append({"role": "tool",
                             "tool_call_id": call.id,
                             "content": str(result)})
