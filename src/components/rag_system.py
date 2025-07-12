"""
RAG System Component
Retrieval-Augmented Generation for research papers
"""

import os
import warnings
from typing import List, Dict, Optional, Any
from datetime import datetime

# LangChain
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

from .config import Config
from .groq_processor import GroqLlamaLLM

warnings.filterwarnings('ignore')


class RAGSystem:
    """
    Advanced RAG (Retrieval-Augmented Generation) System
    Combines vector database search with LLM reasoning
    """
    
    def __init__(self, config: Config = None):
        self.config = config or Config()
        # Ensure directories exist
        self.config.create_directories()
        
        self.embeddings = None
        self.vectorstore = None
        self.llm = None
        self.qa_chain = None
        self.text_splitter = None
        self.papers_metadata = {}
        
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all RAG components"""
        try:
            # Initialize embeddings
            print("Initializing embeddings...")
            self.embeddings = HuggingFaceEmbeddings(
                model_name=self.config.EMBEDDING_MODEL,
                model_kwargs={'device': 'cpu'}
            )
            print("✅ Embeddings initialized!")
            
            # Initialize text splitter
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.config.CHUNK_SIZE,
                chunk_overlap=self.config.CHUNK_OVERLAP
            )
            print("✅ Text splitter initialized!")
            
            # Initialize LLM
            print("Initializing LLM...")
            self.llm = GroqLlamaLLM(
                api_key=self.config.GROQ_API_KEY,
                model_name=self.config.LLAMA_MODEL,
                temperature=self.config.TEMPERATURE,
                max_tokens=self.config.MAX_OUTPUT_TOKENS,
                top_p=self.config.TOP_P
            )
            print("✅ LLM initialized!")
            
            # Initialize or load vectorstore
            print("Initializing vectorstore...")
            self._initialize_vectorstore()
            
            # Initialize QA chain
            if self.vectorstore:
                print("Initializing QA chain...")
                self.qa_chain = RetrievalQA.from_chain_type(
                    llm=self.llm,
                    chain_type="stuff",
                    retriever=self.vectorstore.as_retriever(
                        search_kwargs={"k": self.config.TOP_K_SIMILAR}
                    ),
                    return_source_documents=True
                )
                print("✅ QA chain initialized!")
            
            print("✅ RAG System initialized successfully!")
            
        except Exception as e:
            print(f"❌ Error initializing RAG System: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _initialize_vectorstore(self):
        """Initialize or load existing vectorstore"""
        try:
            # Ensure persist directory exists with absolute path
            persist_dir = os.path.abspath(self.config.PERSIST_DIRECTORY)
            print(f"Initializing vectorstore at: {persist_dir}")
            os.makedirs(persist_dir, exist_ok=True)
            
            # Check if directory has existing data
            has_existing_data = os.path.exists(persist_dir) and any(
                f for f in os.listdir(persist_dir) 
                if not f.startswith('.') and os.path.isfile(os.path.join(persist_dir, f))
            )
            
            if has_existing_data:
                print("Loading existing vectorstore...")
                self.vectorstore = Chroma(
                    persist_directory=persist_dir,
                    embedding_function=self.embeddings,
                    collection_name=self.config.COLLECTION_NAME
                )
                try:
                    count = self.vectorstore._collection.count()
                    print(f"✅ Loaded vectorstore with {count} documents")
                except Exception as count_error:
                    print(f"✅ Loaded vectorstore (document count unavailable: {count_error})")
            else:
                print("Creating new vectorstore...")
                self.vectorstore = Chroma(
                    persist_directory=persist_dir,
                    embedding_function=self.embeddings,
                    collection_name=self.config.COLLECTION_NAME
                )
                print("✅ New vectorstore created successfully!")
                
        except Exception as e:
            print(f"❌ Error initializing vectorstore: {e}")
            print(f"   Persist directory: {getattr(self.config, 'PERSIST_DIRECTORY', 'NOT SET')}")
            print(f"   Collection name: {getattr(self.config, 'COLLECTION_NAME', 'NOT SET')}")
            print("   Continuing without vectorstore - search functionality will be limited")
            self.vectorstore = None
    
    def add_papers(self, papers: List[Dict[str, Any]]):
        """
        Add research papers to the RAG system
        
        Args:
            papers: List of paper dictionaries with 'title', 'content', 'summary', etc.
        """
        if not self.vectorstore:
            print("Vectorstore not initialized! Attempting to reinitialize...")
            try:
                self._initialize_vectorstore()
                if not self.vectorstore:
                    print("Failed to initialize vectorstore - papers will not be added to search index")
                    return
            except Exception as e:
                print(f"Failed to reinitialize vectorstore: {e}")
                return
        
        documents = []
        
        for paper in papers:
            # Create metadata - Chroma only supports str, int, float, bool, None
            authors = paper.get('authors', [])
            categories = paper.get('categories', [])
            
            metadata = {
                'title': str(paper.get('title', 'Unknown')),
                'authors': ', '.join(authors) if isinstance(authors, list) else str(authors),
                'published': str(paper.get('published', '')),
                'pdf_url': str(paper.get('pdf_url', '')),
                'arxiv_id': str(paper.get('arxiv_id', '')),
                'summary': str(paper.get('summary', '')),
                'categories': ', '.join(categories) if isinstance(categories, list) else str(categories),
                'source': str(paper.get('source', 'unknown')),
                'added_at': datetime.now().isoformat()
            }
            
            # Store metadata
            paper_id = paper.get('arxiv_id', paper.get('title', ''))
            self.papers_metadata[paper_id] = metadata
            
            # Process content
            content = paper.get('content', '')
            if not content:
                content = paper.get('summary', '')
            
            if content:
                # Split content into chunks
                chunks = self.text_splitter.split_text(content)
                
                # Create documents
                for i, chunk in enumerate(chunks):
                    doc_metadata = metadata.copy()
                    doc_metadata['chunk_id'] = i
                    doc_metadata['chunk_count'] = len(chunks)
                    
                    documents.append(Document(
                        page_content=chunk,
                        metadata=doc_metadata
                    ))
        
        if documents:
            try:
                print(f"Adding {len(documents)} chunks to vectorstore...")
                self.vectorstore.add_documents(documents)
                self.vectorstore.persist()
                print(f"✅ Successfully added {len(documents)} chunks from {len(papers)} papers!")
            except Exception as e:
                print(f"❌ Error adding documents to vectorstore: {e}")
                print("   This may be due to metadata formatting issues")
                # Try to add documents one by one to identify problematic ones
                success_count = 0
                for i, doc in enumerate(documents):
                    try:
                        self.vectorstore.add_documents([doc])
                        success_count += 1
                    except Exception as doc_error:
                        print(f"   Failed to add document {i}: {doc_error}")
                        print(f"   Metadata: {doc.metadata}")
                
                if success_count > 0:
                    self.vectorstore.persist()
                    print(f"✅ Successfully added {success_count}/{len(documents)} documents")
        else:
            print("No valid documents to add!")
    
    def search_papers(self, query: str, k: int = None) -> List[Dict[str, Any]]:
        """
        Search for relevant papers using vector similarity
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of relevant paper chunks with metadata
        """
        if not self.vectorstore:
            print("Vectorstore not initialized!")
            return []
        
        try:
            k = k or self.config.TOP_K_SIMILAR
            results = self.vectorstore.similarity_search_with_score(query, k=k)
            
            formatted_results = []
            for doc, score in results:
                result = {
                    'content': doc.page_content,
                    'score': score,
                    'metadata': doc.metadata,
                    'title': doc.metadata.get('title', 'Unknown'),
                    'authors': doc.metadata.get('authors', []),
                    'published': doc.metadata.get('published', ''),
                    'summary': doc.metadata.get('summary', ''),
                    'arxiv_id': doc.metadata.get('arxiv_id', ''),
                    'pdf_url': doc.metadata.get('pdf_url', ''),
                    'categories': doc.metadata.get('categories', [])
                }
                formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def answer_question(self, question: str) -> Dict[str, Any]:
        """
        Answer a research question using RAG
        
        Args:
            question: Research question
            
        Returns:
            Dictionary with answer and source information
        """
        if not self.qa_chain:
            return {
                'answer': "RAG system not properly initialized!",
                'sources': [],
                'error': "System not initialized"
            }
        
        try:
            print(f"Processing question: {question}")
            result = self.qa_chain({"query": question})
            
            # Extract source information
            sources = []
            for doc in result.get('source_documents', []):
                sources.append({
                    'title': doc.metadata.get('title', 'Unknown'),
                    'authors': doc.metadata.get('authors', []),
                    'content_snippet': doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                    'arxiv_id': doc.metadata.get('arxiv_id', ''),
                    'pdf_url': doc.metadata.get('pdf_url', ''),
                    'chunk_id': doc.metadata.get('chunk_id', 0)
                })
            
            return {
                'answer': result['result'],
                'sources': sources,
                'question': question,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error answering question: {e}")
            return {
                'answer': f"Error processing question: {str(e)}",
                'sources': [],
                'error': str(e)
            }
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base"""
        if not self.vectorstore:
            return {'status': 'not_initialized', 'count': 0}
        
        try:
            count = self.vectorstore._collection.count()
            return {
                'status': 'active',
                'total_chunks': count,
                'total_papers': len(self.papers_metadata),
                'embedding_model': self.config.EMBEDDING_MODEL,
                'chunk_size': self.config.CHUNK_SIZE,
                'chunk_overlap': self.config.CHUNK_OVERLAP
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def clear_database(self):
        """Clear all data from the vectorstore"""
        try:
            if self.vectorstore:
                self.vectorstore.delete_collection()
                print("Database cleared!")
            
            self.papers_metadata.clear()
            self._initialize_vectorstore()
            
        except Exception as e:
            print(f"Error clearing database: {e}")
    
    def export_papers_metadata(self) -> Dict[str, Any]:
        """Export papers metadata for backup or analysis"""
        return {
            'metadata': self.papers_metadata,
            'export_time': datetime.now().isoformat(),
            'total_papers': len(self.papers_metadata),
            'database_stats': self.get_database_stats()
        }
    
    def test_vectorstore(self) -> Dict[str, Any]:
        """Test vectorstore functionality and return status"""
        status = {
            'vectorstore_initialized': False,
            'can_add_documents': False,
            'can_search': False,
            'document_count': 0,
            'persist_directory': getattr(self.config, 'PERSIST_DIRECTORY', 'NOT SET'),
            'collection_name': getattr(self.config, 'COLLECTION_NAME', 'NOT SET'),
            'errors': []
        }
        
        try:
            if self.vectorstore is None:
                status['errors'].append("Vectorstore is None")
                return status
            
            status['vectorstore_initialized'] = True
            
            # Test document count
            try:
                count = self.vectorstore._collection.count()
                status['document_count'] = count
            except Exception as e:
                status['errors'].append(f"Cannot get document count: {e}")
            
            # Test adding a simple document
            try:
                test_doc = Document(
                    page_content="This is a test document",
                    metadata={"test": True, "source": "vectorstore_test"}
                )
                self.vectorstore.add_documents([test_doc])
                status['can_add_documents'] = True
                
                # Test searching
                results = self.vectorstore.similarity_search("test document", k=1)
                if results:
                    status['can_search'] = True
                    
                # Clean up test document
                try:
                    # Remove test document if possible
                    pass  # Chroma doesn't have easy delete by metadata
                except:
                    pass
                    
            except Exception as e:
                status['errors'].append(f"Cannot add/search documents: {e}")
            
        except Exception as e:
            status['errors'].append(f"Vectorstore test failed: {e}")
        
        return status
