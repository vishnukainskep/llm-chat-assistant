# from uuid import uuid4
# from langchain_openai import AzureOpenAIEmbeddings
# from langchain_text_splitters import RecursiveCharacterTextSplitter
# from langchain_chroma import Chroma
# from langchain_community.document_loaders import TextLoader, PyPDFLoader
# import os
# import logging
# from pathlib import Path
# from dotenv import load_dotenv

# # Set up logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # Load environment variables
# load_dotenv()

# # Disable ONNX to avoid potential issues
# os.environ['ONNX_DISABLE'] = '1'

# # ---------- Paths ----------
# BASE_DIR = Path(__file__).resolve().parent
# DOCS_PATH = BASE_DIR / "docs.txt"
# CHROMA_DIR = BASE_DIR / "chroma_db"

# # Singleton instances
# _embeddings = None
# _vectorstore = None
# _pdf_loaded = False


# def get_embeddings():
#     """Create Azure OpenAI embeddings (singleton)."""
#     global _embeddings

#     if _embeddings is None:
#         logger.info("Initializing Azure OpenAI embeddings...")
#         _embeddings = AzureOpenAIEmbeddings(
#             api_key=os.environ["AZURE_OPENAI_API_KEY"],
#             azure_endpoint=os.environ["EMBEDDING_ENDPOINT"],
#             model=os.environ["EMBEDDING_DEPLOYMENT"],
#             api_version=os.environ["EMBEDDING_VERSION"],
#         )
#         logger.info("Azure OpenAI embeddings initialized successfully")

#     return _embeddings


# def load_and_chunk_pdf(pdf_path: str = "./resume.pdf"):
#     """Load PDF and split into chunks"""
#     try:
#         logger.info(f"Loading PDF from {pdf_path}...")
#         loader = PyPDFLoader(pdf_path)
#         document = loader.load()
#         text_splitter = RecursiveCharacterTextSplitter(
#             chunk_size=600,
#             chunk_overlap=100
#         )
#         chunks = text_splitter.split_documents(document)
#         logger.info(f"Split PDF into {len(chunks)} chunks")
#         return chunks
#     except Exception as e:
#         logger.error(f"Error loading PDF: {e}")
#         raise


# def load_and_chunk_text(text_path: str = str(DOCS_PATH)):
#     """Load text file and split into chunks"""
#     try:
#         logger.info(f"Loading text from {text_path}...")
#         loader = TextLoader(text_path, encoding="utf-8")
#         documents = loader.load()
#         text_splitter = RecursiveCharacterTextSplitter(
#             chunk_size=600,
#             chunk_overlap=100
#         )
#         chunks = text_splitter.split_documents(documents)
#         logger.info(f"Split text into {len(chunks)} chunks")
#         return chunks
#     except Exception as e:
#         logger.error(f"Error loading text file: {e}")
#         raise


# def get_vectorstore():
#     """Load or create the Chroma vector store (singleton)."""
#     global _vectorstore

#     if _vectorstore is None:
#         try:
#             logger.info("Initializing Chroma vector store...")
            
#             # Get embeddings
#             embeddings = get_embeddings()
            
#             # Check if Chroma DB already exists
#             if CHROMA_DIR.exists() and len(list(CHROMA_DIR.glob("*.bin"))) > 0:
#                 logger.info(f"Loading existing Chroma DB from {CHROMA_DIR}")
#                 _vectorstore = Chroma(
#                     collection_name="test_collection",
#                     persist_directory=str(CHROMA_DIR),
#                     embedding_function=embeddings,
#                     collection_metadata={
#                         "hnsw:space": "cosine",
#                         "hnsw:construction_ef": 100,
#                         "hnsw:M": 16,
#                     }
#                 )
#                 logger.info("Existing Chroma DB loaded successfully")
#             else:
#                 logger.info(f"Creating new Chroma DB at {CHROMA_DIR}")
                
#                 # Load documents from docs.txt by default
#                 chunks = load_and_chunk_text()
                
#                 # Generate UUIDs for each chunk
#                 uuids = [str(uuid4()) for _ in range(len(chunks))]
                
#                 # Create Chroma vector store
#                 _vectorstore = Chroma.from_documents(
#                     documents=chunks,
#                     embedding=embeddings,
#                     persist_directory=str(CHROMA_DIR),
#                     collection_name="test_collection",
#                     ids=uuids,
#                     collection_metadata={
#                         "hnsw:space": "cosine",
#                         "hnsw:construction_ef": 100,
#                         "hnsw:M": 16,
#                     }
#                 )
#                 logger.info("New Chroma DB created successfully")
#         except Exception as e:
#             logger.error(f"Failed to initialize vector store: {e}")
#             import traceback
#             traceback.print_exc()
#             raise

#     return _vectorstore


# def initialize_pdf(pdf_path: str = "./resume.pdf"):
#     """Initialize PDF documents in the vector store"""
#     global _pdf_loaded, _vectorstore
    
#     try:
#         vectorstore = get_vectorstore()
        
#         # Check if vector store already has documents
#         existing_docs = vectorstore.get()
#         if existing_docs['ids']:
#             logger.info(f"Vector store already contains {len(existing_docs['ids'])} documents")
#             _pdf_loaded = True
#         else:
#             logger.info("Loading PDF for the first time...")
#             chunks = load_and_chunk_pdf(pdf_path)
#             uuids = [str(uuid4()) for _ in range(len(chunks))]
#             vectorstore.add_documents(documents=chunks, ids=uuids)
#             logger.info(f"Successfully loaded {len(chunks)} chunks into vector store")
#             _pdf_loaded = True
#     except Exception as e:
#         logger.error(f"Error initializing PDF: {e}")
#         _pdf_loaded = False
    
#     return _pdf_loaded


# def is_pdf_loaded():
#     """Check if PDF is loaded"""
#     return _pdf_loaded


# # -------------------------------------------------
# # Backward compatibility
# # -------------------------------------------------
# def __getattr__(name):
#     if name == "vectorstore":
#         return get_vectorstore()
#     raise AttributeError(f"module '{__name__}' has no attribute '{name}'")



from uuid import uuid4
from pathlib import Path
import os
import logging

from dotenv import load_dotenv
from langchain_openai import AzureOpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.document_loaders import TextLoader, PyPDFLoader

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = Path(__file__).parent
DOCS_PATH = BASE_DIR / "docs.txt"
CHROMA_DIR = BASE_DIR / "chroma_db"

os.environ["ONNX_DISABLE"] = "1"

# ------------------ Embeddings ------------------

def get_embeddings():
    return AzureOpenAIEmbeddings(
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        azure_endpoint=os.environ["EMBEDDING_ENDPOINT"],
        model=os.environ["EMBEDDING_DEPLOYMENT"],
        api_version=os.environ["EMBEDDING_VERSION"],
    )

# ------------------ Load & Chunk ------------------

def load_text(path: str):
    loader = TextLoader(path, encoding="utf-8")
    docs = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=100)
    return splitter.split_documents(docs)

def load_pdf(path: str):
    loader = PyPDFLoader(path)
    docs = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=100)
    return splitter.split_documents(docs)

# ------------------ Vector Store ------------------

def get_vectorstore():
    embeddings = get_embeddings()

    if CHROMA_DIR.exists():
        logger.info("Loading existing Chroma DB")
        return Chroma(
            persist_directory=str(CHROMA_DIR),
            collection_name="docs",
            embedding_function=embeddings,
        )

    logger.info("Creating new Chroma DB")
    chunks = load_text(str(DOCS_PATH))
    ids = [str(uuid4()) for _ in chunks]

    return Chroma.from_documents(
        documents=chunks,
        ids=ids,
        embedding=embeddings,
        persist_directory=str(CHROMA_DIR),
        collection_name="docs",
    )
