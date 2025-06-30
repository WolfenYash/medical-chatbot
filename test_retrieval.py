import os
from dotenv import load_dotenv
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings

# Load your API key
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set.")

# Load the embedding model
embedding = OpenAIEmbeddings()

# Load the Chroma vector DB
db = Chroma(persist_directory="chroma_db", embedding_function=embedding)

# User query (you can change this to test different questions)
query = "What are the symptoms of diabetes?"

# Retrieve top 3 relevant chunks
results = db.similarity_search(query, k=3)

# Show the results
print(f"🔍 Top results for: {query}\n")
for i, doc in enumerate(results):
    print(f"📄 Result {i+1}:")
    print(doc.page_content.strip())
    print("-" * 80)
