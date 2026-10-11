import os
from dotenv import load_dotenv
import pydantic, ollama

load_dotenv()
model = os.getenv("MODEL_NAME")
print("MODEL_NAME:", model)
print("pydantic:", pydantic.__version__)

import fitz
print("pymupdf OK")
import docx
print("python-docx OK")

reply = ollama.chat(model=model, messages=[{"role": "user", "content": "Say OK"}], think=False)
print("Model replied:", reply.message.content)