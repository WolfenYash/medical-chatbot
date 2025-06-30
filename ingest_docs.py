# 1. Get the API key from the .env file
import os
from dotenv import load_dotenv
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set in the .env file.")

# 2. get the langchain libraries
from langchain.embeddings import OpenAIEmbeddings
# from langchain.vectorstores import Chroma {outdated}
from langchain_chroma import Chroma
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter

# 3. Initialize the text_splitter
text_splitter = CharacterTextSplitter(chunk_size = 500, chunk_overlap = 100)

# 4. Initialize the embedding
embedding = OpenAIEmbeddings()

# 5 . storing all the chunks of the pdf
all_chunks = []

# 6. Name of the folder where all the pdfs are stored
pdf_folder = "data"

# 7. accessing each pdf-file inside the data folder
for filename in os.listdir(pdf_folder):
    if filename.endswith(".pdf"):
        pdf_path = os.path.join(pdf_folder,filename)
        print(f"Loading: {filename}")
        loader = PyPDFLoader(pdf_path) #it is like a cursor for pdf files
        documents = loader.load() #loading the pdf file in the form of document objects

         # ➕ Add filename to each doc's metadata
        for doc in documents:
            doc.metadata["source"] = filename
                # (page is already present from PyPDFLoader)

        # Now we have to split it into chunks
        chunks = text_splitter.split_documents(documents)
        print(f"--> Split into {len(chunks)} chunks")
        # add the chunks of the current pdf to all_chunks

        all_chunks.extend(chunks)

# Now all the chunks are ready
print(f"\nTotal chunks to embed: {len(all_chunks)}")
# 8. we embed every chunk inside our chroma db
print(" Embedding and saving to chroma_db...")
db = Chroma.from_documents(all_chunks,embedding,persist_directory="chroma_db") # this embeds it into the db
# db.persist() # if we wan to permanently store it into the local disk
print("Done! Chroma DB created at './chroma_db'")


