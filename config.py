import os
from dotenv import load_dotenv

load_dotenv()

class Config():
    PDF_PATH = "./pdf"
    SINGLE_PDF_PATH = "/pdf/ppcbcc.pdf"
    GEMINI_EMBEDDING_MODEL = "models/text-embedding-004"
    GEMINI_MODEL = "gemini-1.5-flash"
    GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
    ATLAS_CONNECTION_URL = "mongodb://localhost:27017/?directConnection=true"
    ATLAS_DB_NAME = "search_db"
    ATLAS_COLLECTION_NAME = "search_collection"
    ATLAS_SEARCH_INDEX_NAME = "vsearch"
    QUESTION = "Descreva como funciona o TCC I e o TCC II"