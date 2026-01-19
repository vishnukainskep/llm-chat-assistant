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

BASE_DIR = Path(__file__).parent
DOCS_PATH = BASE_DIR / "docs.txt"
CHROMA_DIR = BASE_DIR / "chroma_db"

# ------------------ Embeddings ------------------

def get_embeddings():
    return AzureOpenAIEmbeddings(
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        azure_endpoint=os.environ["EMBEDDING_ENDPOINT"],
        # model=os.environ["EMBEDDING_DEPLOYMENT"],
        # api_version=os.environ["EMBEDDING_VERSION"],
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
