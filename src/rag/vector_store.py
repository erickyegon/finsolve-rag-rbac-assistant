"""
Vector Store Management for FinSolve RBAC Chatbot
Production-grade vector database implementation with ChromaDB,
document chunking, embedding generation, and similarity search.

Author: Peter Pandey
Version: 1.0.0
"""

import os
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import chromadb
from chromadb.config import Settings
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None
import numpy as np
from datetime import datetime
from dataclasses import dataclass
from loguru import logger

from ..core.config import settings, UserRole
from ..data.processors import data_processor, DataType, Department


@dataclass
class Document:
    """Document representation for vector storage"""
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None


@dataclass
class SearchResult:
    """Search result from vector store"""
    document: Document
    similarity_score: float
    rank: int


class DocumentChunker:
    """
    Advanced document chunking with overlap and semantic awareness
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[Document]:
        """Chunk text into overlapping segments"""
        chunks = []

        # Split by paragraphs first
        paragraphs = text.split('\n\n')
        current_chunk = ""
        chunk_index = 0

        # Create unique prefix for this chunking session
        section_prefix = metadata.get('section_index', '')
        base_id = metadata.get('source', 'unknown')

        for paragraph in paragraphs:
            # If adding this paragraph would exceed chunk size
            if len(current_chunk) + len(paragraph) > self.chunk_size and current_chunk:
                # Create unique chunk ID
                if section_prefix != '':
                    chunk_id = f"{base_id}_s{section_prefix}_c{chunk_index}"
                else:
                    chunk_id = f"{base_id}_c{chunk_index}"

                chunk_metadata = {
                    **metadata,
                    "chunk_index": chunk_index,
                    "chunk_type": "paragraph_based"
                }

                chunks.append(Document(
                    id=chunk_id,
                    content=current_chunk.strip(),
                    metadata=chunk_metadata
                ))

                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk)
                current_chunk = overlap_text + paragraph
                chunk_index += 1
            else:
                current_chunk += "\n\n" + paragraph if current_chunk else paragraph

        # Add final chunk
        if current_chunk.strip():
            if section_prefix != '':
                chunk_id = f"{base_id}_s{section_prefix}_c{chunk_index}"
            else:
                chunk_id = f"{base_id}_c{chunk_index}"

            chunk_metadata = {
                **metadata,
                "chunk_index": chunk_index,
                "chunk_type": "paragraph_based"
            }

            chunks.append(Document(
                id=chunk_id,
                content=current_chunk.strip(),
                metadata=chunk_metadata
            ))

        return chunks
    
    def _get_overlap_text(self, text: str) -> str:
        """Get overlap text from the end of current chunk"""
        if len(text) <= self.chunk_overlap:
            return text
        
        # Try to find a good breaking point (sentence end)
        overlap_start = len(text) - self.chunk_overlap
        overlap_text = text[overlap_start:]
        
        # Look for sentence boundaries
        sentence_ends = ['.', '!', '?', '\n']
        for i, char in enumerate(overlap_text):
            if char in sentence_ends and i > self.chunk_overlap // 2:
                return overlap_text[i+1:].strip()
        
        return overlap_text
    
    def chunk_markdown(self, text: str, metadata: Dict[str, Any]) -> List[Document]:
        """Specialized chunking for markdown documents"""
        chunks = []
        sections = self._split_markdown_sections(text)
        
        for section_index, (header, content) in enumerate(sections):
            if not content.strip():
                continue
            
            # Create section-based chunks
            section_chunks = self.chunk_text(content, {
                **metadata,
                "section_header": header,
                "section_index": section_index
            })
            
            chunks.extend(section_chunks)
        
        return chunks
    
    def _split_markdown_sections(self, text: str) -> List[Tuple[str, str]]:
        """Split markdown text by headers"""
        lines = text.split('\n')
        sections = []
        current_header = "Introduction"
        current_content = []
        
        for line in lines:
            if line.startswith('#'):
                # Save previous section
                if current_content:
                    sections.append((current_header, '\n'.join(current_content)))
                
                # Start new section
                current_header = line.strip('#').strip()
                current_content = []
            else:
                current_content.append(line)
        
        # Add final section
        if current_content:
            sections.append((current_header, '\n'.join(current_content)))
        
        return sections


class VectorStore:
    """
    Production-grade vector store with ChromaDB backend
    """
    
    def __init__(self):
        self.persist_directory = settings.chroma_persist_directory
        self.collection_name = settings.vector_db_collection_name
        self.embedding_model_name = settings.embedding_model
        
        # Initialize ChromaDB
        self._initialize_chroma()
        
        # Initialize embedding model
        self._initialize_embedding_model()
        
        # Initialize document chunker
        self.chunker = DocumentChunker(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )
        
        logger.info("Vector store initialized successfully")
    
    def _initialize_chroma(self):
        """Initialize ChromaDB client and collection"""
        try:
            # Create persist directory if it doesn't exist
            os.makedirs(self.persist_directory, exist_ok=True)
            
            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection
            try:
                self.collection = self.client.get_collection(name=self.collection_name)
                logger.info(f"Loaded existing collection: {self.collection_name}")
            except ValueError:
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "FinSolve RBAC Chatbot document collection"}
                )
                logger.info(f"Created new collection: {self.collection_name}")
                
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {str(e)}")
            raise
    
    def _initialize_embedding_model(self):
        """Initialize embedding model with Euriai support for enhanced quality"""
        try:
            # Try to use Euriai embeddings first for better quality
            if self._try_euriai_embeddings():
                logger.info("Using Euriai embeddings for enhanced quality")
                return

            # Fallback to sentence transformers with memory optimization
            if SENTENCE_TRANSFORMERS_AVAILABLE:
                # Use device='cpu' to avoid GPU memory issues and enable model sharing
                self.embedding_model = SentenceTransformer(
                    self.embedding_model_name,
                    device='cpu',
                    cache_folder=os.path.join(settings.chroma_persist_directory, 'models')
                )
                self.use_euriai = False
                logger.info(f"Loaded embedding model: {self.embedding_model_name} (CPU optimized)")
            else:
                raise ImportError("SentenceTransformers not available")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {str(e)}")
            raise

    def _try_euriai_embeddings(self) -> bool:
        """Try to initialize Euriai embeddings for better quality"""
        try:
            from euriai.langchain_embed import EuriaiEmbeddings

            # Use environment variable or settings for API key
            api_key = getattr(settings, 'euriai_api_key', None)

            if not api_key:
                logger.info("Euriai API key not found, using default embeddings")
                self.use_euriai = False
                return False

            self.euriai_embeddings = EuriaiEmbeddings(api_key=api_key)
            self.use_euriai = True

            # Test the embeddings
            test_embedding = self.euriai_embeddings.embed_query("test query")
            if test_embedding and len(test_embedding) > 0:
                logger.info(f"Euriai embeddings initialized successfully (dimension: {len(test_embedding)})")
                logger.info(f"Sample embedding values: {test_embedding[:5]}")
                return True
            else:
                logger.warning("Euriai embeddings test failed, falling back to default")
                self.use_euriai = False
                return False

        except ImportError:
            logger.warning("Euriai embeddings package not available, using default embeddings")
            self.use_euriai = False
            return False
        except Exception as e:
            logger.warning(f"Failed to initialize Euriai embeddings: {str(e)}, using default")
            self.use_euriai = False
            return False
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts using best available model"""
        try:
            if hasattr(self, 'use_euriai') and self.use_euriai:
                # Use Euriai embeddings for better quality
                embeddings = []
                for text in texts:
                    embedding = self.euriai_embeddings.embed_query(text)
                    embeddings.append(embedding)
                return embeddings
            else:
                # Use sentence transformers
                embeddings = self.embedding_model.encode(texts, convert_to_tensor=False)
                return embeddings.tolist()
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {str(e)}")
            raise
    
    def add_documents(self, documents: List[Document]) -> bool:
        """Add documents to the vector store"""
        try:
            if not documents:
                return True
            
            # Generate embeddings for all documents
            texts = [doc.content for doc in documents]
            embeddings = self.generate_embeddings(texts)
            
            # Prepare data for ChromaDB
            ids = [doc.id for doc in documents]
            metadatas = [doc.metadata for doc in documents]
            
            # Add to collection
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas
            )
            
            logger.info(f"Added {len(documents)} documents to vector store")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add documents: {str(e)}")
            return False
    
    def search(
        self,
        query: str,
        user_role: UserRole,
        n_results: int = 5,
        department_filter: Optional[str] = None
    ) -> List[SearchResult]:
        """Search for similar documents with role-based filtering"""
        try:
            # Generate query embedding
            query_embedding = self.generate_embeddings([query])[0]
            
            # Build where clause for role-based filtering
            where_clause = self._build_where_clause(user_role, department_filter)
            
            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results * 2,  # Get more results for filtering
                where=where_clause if where_clause else None,
                include=["documents", "metadatas", "distances"]
            )
            
            # Process results
            search_results = []
            for i, (doc_id, document, metadata, distance) in enumerate(zip(
                results['ids'][0],
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            )):
                # Convert distance to similarity score
                similarity_score = 1 / (1 + distance)
                
                # Apply additional role-based filtering
                if self._check_document_access(metadata, user_role):
                    doc = Document(
                        id=doc_id,
                        content=document,
                        metadata=metadata
                    )
                    
                    search_results.append(SearchResult(
                        document=doc,
                        similarity_score=similarity_score,
                        rank=i + 1
                    ))
            
            # Sort by similarity and limit results
            search_results.sort(key=lambda x: x.similarity_score, reverse=True)
            return search_results[:n_results]
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return []
    
    def _build_where_clause(self, user_role: UserRole, department_filter: Optional[str]) -> Dict[str, Any]:
        """Build where clause for ChromaDB query based on user role"""
        where_clause = {}
        
        # Department filtering based on role permissions
        accessible_departments = []
        
        if user_role in [UserRole.CEO, UserRole.CFO, UserRole.CTO, UserRole.CHRO, UserRole.VP_MARKETING]:
            accessible_departments = ["engineering", "finance", "hr", "marketing", "general"]
        elif user_role == UserRole.HR:
            accessible_departments = ["hr", "general"]
        elif user_role == UserRole.FINANCE:
            accessible_departments = ["finance", "general"]
        elif user_role == UserRole.MARKETING:
            accessible_departments = ["marketing", "general"]
        elif user_role == UserRole.ENGINEERING:
            accessible_departments = ["engineering", "general"]
        else:  # EMPLOYEE
            accessible_departments = ["general"]
        
        # Apply department filter if specified
        if department_filter and department_filter.lower() in accessible_departments:
            where_clause["department"] = department_filter.lower()
        else:
            where_clause["department"] = {"$in": accessible_departments}
        
        return where_clause

    def _check_document_access(self, metadata: Dict[str, Any], user_role: UserRole) -> bool:
        """Enhanced document-level access control with comprehensive metadata"""

        # Check sensitivity level
        sensitivity_level = metadata.get("sensitivity_level", "").lower()
        if "high" in sensitivity_level:
            # High sensitivity documents need specific role access
            access_roles_str = metadata.get("access_roles", "")
            if access_roles_str:
                access_roles = [role.strip() for role in access_roles_str.split(",")]
                if user_role.value not in access_roles:
                    return False

        # Check if document contains sensitive information
        sensitive_keywords = ["salary", "compensation", "confidential", "restricted"]
        content_lower = metadata.get("content", "").lower()

        if any(keyword in content_lower for keyword in sensitive_keywords):
            # Only HR and C-level executives can access salary/compensation data
            executive_roles = [UserRole.HR, UserRole.CEO, UserRole.CFO, UserRole.CHRO]
            if user_role not in executive_roles:
                return False

        return True

    def _calculate_enhanced_similarity(
        self,
        query: str,
        metadata: Dict[str, Any],
        distance: float
    ) -> float:
        """Calculate enhanced similarity score using metadata"""

        # Base similarity from vector distance
        base_similarity = 1 / (1 + distance)

        # Boost based on key topics match
        query_lower = query.lower()
        key_topics_str = metadata.get("key_topics", "")
        topic_boost = 0.0

        if key_topics_str:
            # Split the comma-separated topics
            key_topics = [topic.strip() for topic in key_topics_str.split(",")]
            for topic in key_topics:
                if topic.lower() in query_lower:
                    topic_boost += 0.1

        # Boost based on content summary match
        content_summary = metadata.get("content_summary", "").lower()
        summary_boost = 0.0
        if any(word in content_summary for word in query_lower.split()):
            summary_boost = 0.05

        # Boost based on purpose match
        purpose = metadata.get("purpose", "").lower()
        purpose_boost = 0.0
        if any(word in purpose for word in query_lower.split()):
            purpose_boost = 0.05

        # Calculate final score
        enhanced_score = base_similarity + topic_boost + summary_boost + purpose_boost
        return min(enhanced_score, 1.0)  # Cap at 1.0
    
    def index_data_sources(self) -> bool:
        """Index all available data sources into vector store"""
        try:
            logger.info("Starting data source indexing...")
            
            total_documents = 0
            
            # Process each data source
            for source_key, source in data_processor.data_sources.items():
                if source.data_type in [DataType.MARKDOWN, DataType.TEXT]:
                    documents = self._process_text_file(source)
                    if documents:
                        success = self.add_documents(documents)
                        if success:
                            total_documents += len(documents)
                            logger.info(f"Indexed {len(documents)} chunks from {source.name}")
            
            logger.info(f"Indexing completed. Total documents: {total_documents}")
            return True
            
        except Exception as e:
            logger.error(f"Indexing failed: {str(e)}")
            return False
    
    def _process_text_file(self, source) -> List[Document]:
        """Process a text file into document chunks with error handling"""
        try:
            # Use more robust file reading with error handling
            try:
                with open(source.path, 'r', encoding='utf-8') as file:
                    content = file.read()
            except UnicodeDecodeError:
                # Try with different encoding if UTF-8 fails
                with open(source.path, 'r', encoding='latin-1') as file:
                    content = file.read()
                logger.warning(f"Used latin-1 encoding for {source.path}")
            except Exception as e:
                logger.error(f"Failed to read file {source.path}: {str(e)}")
                return []
            
            # Create comprehensive metadata (convert lists to strings for ChromaDB)
            usage_context = getattr(source, 'usage_context', [])
            key_topics = getattr(source, 'key_topics', [])
            access_roles = [role.value for role in source.access_roles]

            metadata = {
                "source": source.name,
                "file_path": source.path,
                "department": source.department.value,
                "data_type": source.data_type.value,
                "last_updated": source.last_updated.isoformat(),
                "size_bytes": source.size_bytes,

                # Enhanced metadata from your specifications (convert lists to strings)
                "purpose": getattr(source, 'purpose', ''),
                "ownership": getattr(source, 'ownership', ''),
                "update_frequency": getattr(source, 'update_frequency', ''),
                "sensitivity_level": getattr(source, 'sensitivity_level', ''),
                "usage_context": ", ".join(usage_context) if usage_context else "",
                "content_summary": getattr(source, 'content_summary', ''),
                "key_topics": ", ".join(key_topics) if key_topics else "",
                "file_hash": getattr(source, 'file_hash', ''),

                # Access control metadata
                "access_roles": ", ".join(access_roles) if access_roles else "",
                "is_sensitive": str(source.department.value in ["finance", "hr", "engineering"])
            }
            
            # Chunk the document
            if source.data_type == DataType.MARKDOWN:
                documents = self.chunker.chunk_markdown(content, metadata)
            else:
                documents = self.chunker.chunk_text(content, metadata)
            
            return documents
            
        except Exception as e:
            logger.error(f"Failed to process file {source.path}: {str(e)}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store collection"""
        try:
            count = self.collection.count()
            
            # Get sample of metadata to analyze
            sample_results = self.collection.get(limit=min(100, count))
            
            departments = {}
            data_types = {}
            
            for metadata in sample_results.get('metadatas', []):
                dept = metadata.get('department', 'unknown')
                dtype = metadata.get('data_type', 'unknown')
                
                departments[dept] = departments.get(dept, 0) + 1
                data_types[dtype] = data_types.get(dtype, 0) + 1
            
            return {
                "total_documents": count,
                "departments": departments,
                "data_types": data_types,
                "collection_name": self.collection_name,
                "embedding_model": self.embedding_model_name
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {str(e)}")
            return {}
    
    def reset_collection(self) -> bool:
        """Reset the vector store collection (use with caution!)"""
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "FinSolve RBAC Chatbot document collection"}
            )
            logger.warning("Vector store collection reset")
            return True
        except Exception as e:
            logger.error(f"Failed to reset collection: {str(e)}")
            return False


# Global vector store instance
vector_store = VectorStore()
