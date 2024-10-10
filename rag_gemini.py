from langchain.text_splitter import MarkdownTextSplitter
from langchain_mongodb import MongoDBAtlasVectorSearch
from pymongo import MongoClient
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import os
import pymupdf4llm
from os.path import isfile, join
import google.generativeai as genai
import json
from config import Config

PROMPT_TEMPLATE = """Use os fragmentos de contexto a seguir para responder a questão no final. Deixe a resposta o mais concisa possível e formatada em Markdown.
	{context}
	Question: {question}
	Helpful Answer:"""

configs = Config()

def load_docs_from_directory():
    doc_list = [join(configs.PDF_PATH, f) for f in os.listdir(configs.PDF_PATH) if isfile(join(configs.PDF_PATH, f))]
    print(f"Doc list: {doc_list}")
    
    all_docs_list = []
    for file_path in doc_list:
        all_docs_list += pymupdf4llm.to_markdown(file_path, page_chunks=True)
    print(f"all_docs_list lenght: {len(all_docs_list)}")
    
    text_splitter = MarkdownTextSplitter()
    return text_splitter.create_documents([i['text'] for i in all_docs_list], [i['metadata'] for i in all_docs_list])

def load_single_doc():
    md_text = pymupdf4llm.to_markdown(configs.SINGLE_PDF_PATH, page_chunks=True)
    text_splitter = MarkdownTextSplitter()
    return text_splitter.create_documents([i['text'] for i in md_text], [i['metadata'] for i in md_text])

def setup_gemini_embeddings():
    embeddings = GoogleGenerativeAIEmbeddings(
        model=configs.GEMINI_EMBEDDING_MODEL, google_api_key=configs.GEMINI_API_KEY
    )
    return embeddings

def setup_atlas(embeddings):
    client = MongoClient(configs.ATLAS_CONNECTION_URL)
    atlas_collection = client[configs.ATLAS_DB_NAME][configs.ATLAS_COLLECTION_NAME]
    
    print(f'Db exists: {len([a for a in client.list_database_names() if a == "search_db"]) == 1}')
    if len([a for a in client.list_database_names() if a == "search_db"]) == 1: #database exists
        return True
    else:
        docs = load_docs_from_directory()
        #docs = load_single_doc()
        
        print("Inserting docs...")
        MongoDBAtlasVectorSearch.from_documents(
            documents = docs,
            embedding = embeddings,
            collection = atlas_collection,
            index_name = configs.ATLAS_SEARCH_INDEX_NAME
        )
        
        return setup_search_index_if_not_exists(atlas_collection)


def setup_search_index_if_not_exists(atlas_collection):
    # OBS.: for text_embedding_004, dimensions = 768

    search_index_definition = {
        "definition": {
            "mappings": {
                "dynamic": True, 
                "fields": {
                    "embedding" : {
                        "dimensions": 768,
                        "similarity": "cosine",
                        "type": "knnVector"
                    }
                }
            }
        },
        "name": configs.ATLAS_SEARCH_INDEX_NAME
    }

    search_index = atlas_collection.list_search_indexes().try_next()
    if search_index is None:
        print("Creating search index...")
        atlas_collection.create_search_index(search_index_definition)
        return False
    else:
        #Armengo caso o indice não funcione de primeira
        if search_index['status'] == "DOES_NOT_EXIST":
            atlas_collection.drop_search_index(configs.ATLAS_SEARCH_INDEX_NAME)
            atlas_collection.create_search_index(search_index_definition)
            return False
        return True

def drop_database():
    client = MongoClient(configs.ATLAS_CONNECTION_URL)
    client.drop_database(name_or_database=configs.ATLAS_DB_NAME)
    print("Database dropped")

def check_index():
    client = MongoClient(configs.ATLAS_CONNECTION_URL)
    atlas_collection = client[configs.ATLAS_DB_NAME][configs.ATLAS_COLLECTION_NAME]
    print(f"Index: {atlas_collection.list_search_indexes().try_next()}")

def setupGeminiModel():
	genai.configure(api_key=configs.GEMINI_API_KEY)
	return genai.GenerativeModel(configs.GEMINI_MODEL)

async def pdf_response(question: str, stream : bool = False):
    gemini_model = setupGeminiModel()
    prompt_template = PROMPT_TEMPLATE
    embeddings = setup_gemini_embeddings()
    run_query = setup_atlas(embeddings)
    if run_query:
        print("Running the search query...")
        docsearch = MongoDBAtlasVectorSearch.from_connection_string(
            configs.ATLAS_CONNECTION_URL,
            configs.ATLAS_DB_NAME + "." + configs.ATLAS_COLLECTION_NAME,
            embeddings,
            index_name=configs.ATLAS_SEARCH_INDEX_NAME,
        )
        
        results = docsearch.similarity_search(question, k=7)
        
        context = str("\n".join([x.page_content for x in results]))
        pergunta = prompt_template.format(context=context, question=question)
        if stream:
            result = await gemini_model.generate_content_async(pergunta, stream=stream)
            async for chunk in result:
                dic_chunck = {'response': chunk.text} 
                yield f'{json.dumps(dic_chunck)}\n'
        else:
            result = gemini_model.generate_content(pergunta, stream=False)
            yield json.dumps({"response": result.text})
    else:
        print("Wait until the index gets synced with the dataset")
        yield json.dumps({"response": "Wait until the index gets synced with the dataset"})


#drop_database()
#check_index()