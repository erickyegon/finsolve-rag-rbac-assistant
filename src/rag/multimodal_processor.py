#!/usr/bin/env python3
"""
Multimodal Data Processor for Enhanced RAG
Separates text, numerical, and structured data processing with specialized tools.

Author: Peter Pandey
Version: 1.0.0
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass
from pathlib import Path
import json
from datetime import datetime
from loguru import logger

from ..core.config import settings, UserRole
from ..data.processors import data_processor, DataType, Department


@dataclass
class MultimodalDocument:
    """Enhanced document with multimodal content separation"""
    id: str
    text_content: str
    numerical_data: Dict[str, Any]
    structured_data: Dict[str, Any]
    metadata: Dict[str, Any]
    data_types: List[str]  # ['text', 'numerical', 'structured']


@dataclass
class MultimodalSearchResult:
    """Enhanced search result with multimodal scoring"""
    document: MultimodalDocument
    text_similarity: float
    numerical_relevance: float
    structured_relevance: float
    combined_score: float
    rank: int


class TextProcessor:
    """Specialized processor for text content"""
    
    def __init__(self):
        self.text_patterns = {
            'financial_terms': ['revenue', 'profit', 'expenses', 'margin', 'cash flow'],
            'hr_terms': ['employee', 'leave', 'policy', 'benefits', 'training'],
            'technical_terms': ['architecture', 'microservices', 'security', 'compliance'],
            'marketing_terms': ['campaign', 'customer', 'acquisition', 'conversion']
        }
    
    def extract_text_features(self, content: str) -> Dict[str, Any]:
        """Extract semantic features from text"""
        features = {
            'word_count': len(content.split()),
            'domain_relevance': {},
            'key_phrases': [],
            'sentiment_indicators': []
        }
        
        content_lower = content.lower()
        
        # Calculate domain relevance scores
        for domain, terms in self.text_patterns.items():
            relevance = sum(1 for term in terms if term in content_lower) / len(terms)
            features['domain_relevance'][domain] = relevance
        
        return features
    
    def enhance_text_for_embedding(self, content: str, metadata: Dict[str, Any]) -> str:
        """Enhance text with metadata for better embeddings"""
        enhanced_parts = [content]
        
        # Add metadata context
        if metadata.get('department'):
            enhanced_parts.append(f"Department: {metadata['department']}")
        
        if metadata.get('key_topics'):
            topics = metadata['key_topics'].split(', ') if isinstance(metadata['key_topics'], str) else metadata['key_topics']
            enhanced_parts.append(f"Topics: {' '.join(topics)}")
        
        if metadata.get('purpose'):
            enhanced_parts.append(f"Purpose: {metadata['purpose']}")
        
        return " | ".join(enhanced_parts)


class NumericalProcessor:
    """Specialized processor for numerical data"""
    
    def extract_numerical_data(self, content: str) -> Dict[str, Any]:
        """Extract and structure numerical data from text"""
        import re
        
        numerical_data = {
            'financial_metrics': {},
            'percentages': [],
            'dates': [],
            'quantities': [],
            'ratios': []
        }
        
        # Extract financial figures (billions, millions)
        billion_pattern = r'\$?(\d+(?:\.\d+)?)\s*billion'
        million_pattern = r'\$?(\d+(?:\.\d+)?)\s*million'
        
        billions = re.findall(billion_pattern, content, re.IGNORECASE)
        millions = re.findall(million_pattern, content, re.IGNORECASE)
        
        if billions:
            numerical_data['financial_metrics']['billions'] = [float(x) for x in billions]
        if millions:
            numerical_data['financial_metrics']['millions'] = [float(x) for x in millions]
        
        # Extract percentages
        percentage_pattern = r'(\d+(?:\.\d+)?)\s*%'
        percentages = re.findall(percentage_pattern, content)
        numerical_data['percentages'] = [float(x) for x in percentages]
        
        # Extract quarters
        quarter_pattern = r'Q([1-4])\s*(\d{4})'
        quarters = re.findall(quarter_pattern, content)
        numerical_data['quarters'] = quarters
        
        return numerical_data
    
    def create_numerical_index(self, numerical_data: Dict[str, Any]) -> Dict[str, float]:
        """Create searchable numerical index"""
        index = {}
        
        # Financial metrics indexing
        if 'financial_metrics' in numerical_data:
            metrics = numerical_data['financial_metrics']
            if 'billions' in metrics:
                index['max_billion_value'] = max(metrics['billions']) if metrics['billions'] else 0
                index['total_billion_value'] = sum(metrics['billions']) if metrics['billions'] else 0
            if 'millions' in metrics:
                index['max_million_value'] = max(metrics['millions']) if metrics['millions'] else 0
                index['total_million_value'] = sum(metrics['millions']) if metrics['millions'] else 0
        
        # Percentage indexing
        if numerical_data.get('percentages'):
            index['max_percentage'] = max(numerical_data['percentages'])
            index['avg_percentage'] = sum(numerical_data['percentages']) / len(numerical_data['percentages'])
        
        return index


class StructuredProcessor:
    """Specialized processor for structured data (CSV, JSON)"""
    
    def process_csv_data(self, file_path: str) -> Dict[str, Any]:
        """Process CSV data into structured format"""
        try:
            df = pd.read_csv(file_path)
            
            structured_data = {
                'schema': {
                    'columns': list(df.columns),
                    'dtypes': df.dtypes.to_dict(),
                    'shape': df.shape
                },
                'summary_stats': {},
                'categorical_counts': {},
                'numerical_aggregates': {}
            }
            
            # Generate summary statistics for numerical columns
            numerical_cols = df.select_dtypes(include=[np.number]).columns
            if len(numerical_cols) > 0:
                structured_data['summary_stats'] = df[numerical_cols].describe().to_dict()
                structured_data['numerical_aggregates'] = {
                    col: {
                        'sum': df[col].sum(),
                        'mean': df[col].mean(),
                        'median': df[col].median(),
                        'std': df[col].std()
                    } for col in numerical_cols
                }
            
            # Generate categorical counts
            categorical_cols = df.select_dtypes(include=['object']).columns
            for col in categorical_cols:
                if df[col].nunique() < 50:  # Only for reasonable number of categories
                    structured_data['categorical_counts'][col] = df[col].value_counts().to_dict()
            
            return structured_data
            
        except Exception as e:
            logger.error(f"Failed to process CSV {file_path}: {str(e)}")
            return {}
    
    def create_structured_queries(self, structured_data: Dict[str, Any]) -> List[str]:
        """Generate searchable queries from structured data"""
        queries = []
        
        # Schema-based queries
        if 'schema' in structured_data:
            columns = structured_data['schema'].get('columns', [])
            queries.extend([f"data about {col}" for col in columns])
            queries.append(f"dataset with {len(columns)} columns")
        
        # Statistical queries
        if 'categorical_counts' in structured_data:
            for col, counts in structured_data['categorical_counts'].items():
                for category, count in counts.items():
                    queries.append(f"{count} {category} in {col}")
        
        return queries


class MultimodalVectorStore:
    """Enhanced vector store with multimodal capabilities"""
    
    def __init__(self):
        self.text_processor = TextProcessor()
        self.numerical_processor = NumericalProcessor()
        self.structured_processor = StructuredProcessor()
        
        # Initialize Euriai embeddings if available
        self.use_euriai = self._initialize_euriai_embeddings()
        
        logger.info("Multimodal vector store initialized")
    
    def _initialize_euriai_embeddings(self) -> bool:
        """Initialize Euriai embeddings if available"""
        try:
            from euriai.langchain_embed import EuriaiEmbeddings
            
            # Use environment variable or settings for API key
            api_key = getattr(settings, 'euriai_api_key', None)
            if api_key:
                self.euriai_embeddings = EuriaiEmbeddings(api_key=api_key)
                logger.info("Euriai embeddings initialized successfully")
                return True
            else:
                logger.warning("Euriai API key not found, falling back to default embeddings")
                return False
        except ImportError:
            logger.warning("Euriai embeddings not available, using default embeddings")
            return False
    
    def process_document(self, source) -> MultimodalDocument:
        """Process document into multimodal format"""
        try:
            # Read content
            with open(source.path, 'r', encoding='utf-8') as f:
                raw_content = f.read()
            
            # Process text content
            text_features = self.text_processor.extract_text_features(raw_content)
            enhanced_text = self.text_processor.enhance_text_for_embedding(raw_content, source.__dict__)
            
            # Process numerical data
            numerical_data = self.numerical_processor.extract_numerical_data(raw_content)
            numerical_index = self.numerical_processor.create_numerical_index(numerical_data)
            
            # Process structured data (if CSV)
            structured_data = {}
            if source.data_type == DataType.CSV:
                structured_data = self.structured_processor.process_csv_data(source.path)
            
            # Determine data types present
            data_types = ['text']
            if numerical_data and any(numerical_data.values()):
                data_types.append('numerical')
            if structured_data:
                data_types.append('structured')
            
            # Create multimodal document
            multimodal_doc = MultimodalDocument(
                id=f"multimodal_{source.name}",
                text_content=enhanced_text,
                numerical_data={**numerical_data, **numerical_index},
                structured_data=structured_data,
                metadata={
                    **source.__dict__,
                    'text_features': text_features,
                    'processing_timestamp': datetime.now().isoformat()
                },
                data_types=data_types
            )
            
            return multimodal_doc
            
        except Exception as e:
            logger.error(f"Failed to process multimodal document {source.path}: {str(e)}")
            return None
    
    def search_multimodal(
        self, 
        query: str, 
        user_role: UserRole,
        query_type: str = 'hybrid',  # 'text', 'numerical', 'structured', 'hybrid'
        n_results: int = 5
    ) -> List[MultimodalSearchResult]:
        """Enhanced multimodal search"""
        
        # This would integrate with the existing vector store
        # and add multimodal scoring
        
        results = []
        # Implementation would combine:
        # 1. Text similarity (using Euriai or default embeddings)
        # 2. Numerical relevance (based on extracted numbers)
        # 3. Structured relevance (based on schema matching)
        
        return results


# Global multimodal processor instance
multimodal_processor = MultimodalVectorStore()
