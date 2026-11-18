from groq import Groq

client = Groq()
for m in client.models.list().data:
    print(m.id)