"""
Data Processors for FinSolve RBAC Chatbot
Comprehensive data processing pipeline for structured and unstructured data.
Implements MCP-style tools for direct data access and manipulation.

Author: Peter Pandey
Version: 1.0.0
"""

import os
import pandas as pd
import json
import gc
import sys
from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import re
from datetime import datetime
from functools import lru_cache
import hashlib
import pickle
from loguru import logger

from ..core.config import settings, UserRole, ROLE_PERMISSIONS


class DataType(Enum):
    """Data types supported by the system"""
    CSV = "csv"
    MARKDOWN = "markdown"
    JSON = "json"
    TEXT = "text"


class Department(Enum):
    """Department categories for data organization"""
    ENGINEERING = "engineering"
    FINANCE = "finance"
    HR = "hr"
    MARKETING = "marketing"
    GENERAL = "general"


@dataclass
class DataSource:
    """Enhanced data source metadata with comprehensive information"""
    name: str
    path: str
    department: Department
    data_type: DataType
    description: str
    last_updated: datetime
    size_bytes: int
    access_roles: List[UserRole]

    # Enhanced metadata based on your specifications
    purpose: str = ""
    ownership: str = ""
    update_frequency: str = ""
    sensitivity_level: str = ""
    usage_context: List[str] = field(default_factory=list)
    content_summary: str = ""
    key_topics: List[str] = field(default_factory=list)
    file_hash: str = ""

    def __post_init__(self):
        """Generate file hash for caching and change detection"""
        if not self.file_hash and os.path.exists(self.path):
            self.file_hash = self._calculate_file_hash()

    def _calculate_file_hash(self) -> str:
        """Calculate MD5 hash of file content for change detection"""
        try:
            with open(self.path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return ""


@dataclass
class QueryResult:
    """Result of a data query operation"""
    success: bool
    data: Any
    metadata: Dict[str, Any]
    source_files: List[str]
    processing_time: float
    error: Optional[str] = None


class DataProcessor:
    """
    Production-grade data processor with MCP-style tools,
    caching, and comprehensive metadata management
    """

    def __init__(self, data_directory: str = None):
        self.data_directory = Path(data_directory or settings.data_directory)
        self.data_sources: Dict[str, DataSource] = {}
        self.cache_directory = Path(settings.data_directory) / ".cache"
        self.cache_directory.mkdir(exist_ok=True)

        # Initialize with caching
        self._initialize_data_sources()

        logger.info(f"Data processor initialized with directory: {self.data_directory}")
        logger.info(f"Cache directory: {self.cache_directory}")
    
    def _initialize_data_sources(self):
        """Scan and catalog all available data sources"""
        if not self.data_directory.exists():
            logger.warning(f"Data directory not found: {self.data_directory}")
            return
        
        # Scan each department directory
        for dept_dir in self.data_directory.iterdir():
            if dept_dir.is_dir() and dept_dir.name in [d.value for d in Department]:
                department = Department(dept_dir.name)
                self._scan_department_data(department, dept_dir)
        
        logger.info(f"Cataloged {len(self.data_sources)} data sources")
    
    def _scan_department_data(self, department: Department, dept_path: Path):
        """Scan data files in a department directory"""
        for file_path in dept_path.rglob("*"):
            if file_path.is_file() and file_path.suffix in [".csv", ".md", ".json", ".txt"]:
                try:
                    # Determine data type
                    data_type = self._get_data_type(file_path)
                    
                    # Get file stats
                    stat = file_path.stat()
                    
                    # Determine access roles based on department
                    access_roles = self._get_access_roles(department)
                    
                    # Generate comprehensive metadata
                    metadata = self._generate_comprehensive_metadata(file_path, department)

                    # Create data source
                    source = DataSource(
                        name=file_path.stem,
                        path=str(file_path),
                        department=department,
                        data_type=data_type,
                        description=metadata["description"],
                        last_updated=datetime.fromtimestamp(stat.st_mtime),
                        size_bytes=stat.st_size,
                        access_roles=access_roles,
                        purpose=metadata["purpose"],
                        ownership=metadata["ownership"],
                        update_frequency=metadata["update_frequency"],
                        sensitivity_level=metadata["sensitivity_level"],
                        usage_context=metadata["usage_context"],
                        content_summary=metadata["content_summary"],
                        key_topics=metadata["key_topics"]
                    )
                    
                    self.data_sources[f"{department.value}_{file_path.stem}"] = source
                    
                except Exception as e:
                    logger.warning(f"Failed to catalog file {file_path}: {str(e)}")
    
    def _get_data_type(self, file_path: Path) -> DataType:
        """Determine data type from file extension"""
        extension_map = {
            ".csv": DataType.CSV,
            ".md": DataType.MARKDOWN,
            ".json": DataType.JSON,
            ".txt": DataType.TEXT
        }
        return extension_map.get(file_path.suffix, DataType.TEXT)
    
    def _get_access_roles(self, department: Department) -> List[UserRole]:
        """Get roles that can access department data"""
        access_roles = [UserRole.CEO]  # CEO always has access
        
        # Add department-specific roles
        if department == Department.HR:
            access_roles.append(UserRole.HR)
        elif department == Department.FINANCE:
            access_roles.append(UserRole.FINANCE)
        elif department == Department.MARKETING:
            access_roles.append(UserRole.MARKETING)
        elif department == Department.ENGINEERING:
            access_roles.append(UserRole.ENGINEERING)
        elif department == Department.GENERAL:
            access_roles.extend([UserRole.EMPLOYEE, UserRole.HR, UserRole.FINANCE, 
                               UserRole.MARKETING, UserRole.ENGINEERING])
        
        return access_roles
    
    def _generate_comprehensive_metadata(self, file_path: Path, department: Department) -> Dict[str, Any]:
        """Generate comprehensive metadata based on your specifications"""
        name = file_path.stem.lower()

        # Engineering Data
        if department == Department.ENGINEERING or "engineering" in name or "technical" in name:
            return {
                "description": "FinSolve's complete technical architecture and engineering processes",
                "purpose": "Documents technical architecture, microservices, CI/CD pipelines, security models, and compliance (GDPR, DPDP, PCI-DSS)",
                "ownership": "Engineering Team",
                "update_frequency": "Updated quarterly",
                "sensitivity_level": "High - restricted to Engineering Team and C-Level Executives",
                "usage_context": ["audits", "onboarding", "scaling", "system maintenance", "compliance"],
                "content_summary": "Covers development standards, DevOps practices, monitoring, and future tech roadmap (AI, blockchain)",
                "key_topics": ["microservices", "CI/CD", "security", "compliance", "GDPR", "DPDP", "PCI-DSS", "DevOps", "monitoring", "AI", "blockchain"]
            }

        # Finance Department Data
        elif department == Department.FINANCE or "financial" in name or "finance" in name:
            return {
                "description": "FinSolve's quarterly financial performance for the year 2024",
                "purpose": "Documents quarterly financial performance including revenue, income, gross margin, marketing spend, vendor costs, and cash flow data",
                "ownership": "Finance Team",
                "update_frequency": "Updated quarterly",
                "sensitivity_level": "High - restricted to Finance Team and C-Level Executives",
                "usage_context": ["financial planning", "audits", "investor reporting", "strategic decisions"],
                "content_summary": "Provides detailed expense breakdowns and risk mitigation strategies for each quarter",
                "key_topics": ["revenue", "income", "gross margin", "marketing spend", "vendor costs", "cash flow", "expenses", "risk mitigation"]
            }

        # Employee Handbook
        elif "handbook" in name or "employee" in name:
            return {
                "description": "Comprehensive company policies covering all aspects of employment",
                "purpose": "Serves as the authoritative guide for employees on company vision, values, HR processes, legal compliance, and workplace standards",
                "ownership": "Human Resources Department",
                "update_frequency": "Reviewed and updated annually or as regulations and company practices change",
                "sensitivity_level": "Medium - accessible to all employees",
                "usage_context": ["new-hire orientation", "policy clarifications", "leave & attendance management", "performance reviews", "exit procedures"],
                "content_summary": "Covers onboarding & benefits, leave policies, work hours & attendance, code of conduct & workplace behavior, health & safety, compensation & payroll, reimbursement, training & development, performance & feedback, privacy & data security, exit procedures, FAQs",
                "key_topics": ["onboarding", "benefits", "leave policies", "attendance", "code of conduct", "health & safety", "compensation", "payroll", "training", "performance", "privacy", "data security"]
            }

        # HR Data
        elif department == Department.HR or "hr" in name:
            return {
                "description": "HR's employee dataset covering 100 records with comprehensive employee information",
                "purpose": "Documents HR's employee dataset with demographics, employment, compensation, leave, attendance, and performance fields",
                "ownership": "HR & People Analytics team",
                "update_frequency": "Refreshed monthly to capture hires, exits, and updates",
                "sensitivity_level": "High - restricted to HR and C-Level Executives",
                "usage_context": ["talent forecasting", "compensation reviews", "compliance reporting", "employee engagement initiatives"],
                "content_summary": "Provides workforce composition insights, turnover tracking, leave utilization, and performance trend analysis",
                "key_topics": ["demographics", "employment", "compensation", "leave", "attendance", "performance", "workforce composition", "turnover", "engagement"]
            }

        # Marketing Department
        elif department == Department.MARKETING or "marketing" in name or "campaign" in name:
            return {
                "description": "Marketing department data including campaign overviews and performance metrics",
                "purpose": "Includes campaign overviews, spend allocations, customer acquisition targets, revenue projections, conversion and ROI benchmarks",
                "ownership": "Marketing Team",
                "update_frequency": "Refreshed quarterly",
                "sensitivity_level": "Medium - restricted to Marketing Team and C-Level Executives",
                "usage_context": ["quarterly planning", "budget allocation", "performance reviews", "Q1 2025 strategy recommendations"],
                "content_summary": "Provides detailed highlights on digital marketing, B2B initiatives, customer retention programs, and preliminary performance analysis",
                "key_topics": ["campaigns", "spend allocation", "customer acquisition", "revenue projections", "conversion", "ROI", "digital marketing", "B2B", "customer retention"]
            }

        # Default/General
        else:
            return {
                "description": f"Data file: {file_path.name}",
                "purpose": "General company data and documentation",
                "ownership": "Various departments",
                "update_frequency": "As needed",
                "sensitivity_level": "Medium",
                "usage_context": ["general reference", "documentation"],
                "content_summary": f"Content from {file_path.name}",
                "key_topics": ["general", "documentation"]
            }
    
    def check_access_permission(self, user_role: UserRole, data_source_key: str) -> bool:
        """Check if user role has permission to access data source"""
        if data_source_key not in self.data_sources:
            return False
        
        source = self.data_sources[data_source_key]
        return user_role in source.access_roles
    
    def get_available_data_sources(self, user_role: UserRole) -> List[DataSource]:
        """Get list of data sources accessible to user role"""
        accessible_sources = []
        
        for source in self.data_sources.values():
            if user_role in source.access_roles:
                accessible_sources.append(source)
        
        return accessible_sources
    
    def query_csv_data(
        self,
        user_role: UserRole,
        file_key: str,
        query_params: Dict[str, Any] = None
    ) -> QueryResult:
        """
        Query CSV data with role-based filtering
        MCP-style tool for structured data access
        """
        start_time = datetime.now()
        
        try:
            # Check permissions
            if not self.check_access_permission(user_role, file_key):
                return QueryResult(
                    success=False,
                    data=None,
                    metadata={},
                    source_files=[],
                    processing_time=0,
                    error="Access denied: insufficient permissions"
                )
            
            source = self.data_sources[file_key]
            
            # Load CSV data
            df = pd.read_csv(source.path)
            
            # Apply role-based filtering
            df = self._apply_role_based_filtering(df, user_role, source.department)
            
            # Apply query parameters
            if query_params:
                df = self._apply_query_filters(df, query_params)
            
            # Convert to appropriate format
            result_data = df.to_dict('records') if len(df) <= 1000 else df.head(1000).to_dict('records')
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return QueryResult(
                success=True,
                data=result_data,
                metadata={
                    "total_rows": len(df),
                    "columns": list(df.columns),
                    "data_type": "csv",
                    "department": source.department.value,
                    "truncated": len(df) > 1000
                },
                source_files=[source.path],
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"CSV query failed for {file_key}: {str(e)}")
            
            return QueryResult(
                success=False,
                data=None,
                metadata={},
                source_files=[],
                processing_time=processing_time,
                error=str(e)
            )
    
    def _apply_role_based_filtering(
        self,
        df: pd.DataFrame,
        user_role: UserRole,
        department: Department
    ) -> pd.DataFrame:
        """Apply role-based filtering to dataframe"""
        
        # Get restricted fields for the role
        restricted_fields = ROLE_PERMISSIONS.get_restricted_fields(user_role)
        
        # Remove or mask restricted columns
        for field in restricted_fields:
            if field in df.columns:
                if user_role == UserRole.HR and field == "salary":
                    # HR can see salary ranges but not exact values
                    df[field] = df[field].apply(lambda x: self._mask_salary(x))
                else:
                    # Remove the column entirely
                    df = df.drop(columns=[field])
        
        # Apply department-specific filtering
        if department == Department.HR and user_role != UserRole.HR and user_role != UserRole.CEO:
            # Non-HR users can only see basic employee info
            allowed_columns = ["employee_id", "full_name", "role", "department", "email"]
            df = df[[col for col in allowed_columns if col in df.columns]]
        
        return df
    
    def _mask_salary(self, salary: Union[int, float]) -> str:
        """Mask salary values to show ranges instead of exact amounts"""
        if pd.isna(salary):
            return "Not specified"
        
        salary = float(salary)
        if salary < 500000:
            return "Below 5L"
        elif salary < 1000000:
            return "5L - 10L"
        elif salary < 1500000:
            return "10L - 15L"
        elif salary < 2000000:
            return "15L - 20L"
        else:
            return "Above 20L"
    
    def _apply_query_filters(self, df: pd.DataFrame, query_params: Dict[str, Any]) -> pd.DataFrame:
        """Apply query filters to dataframe"""
        
        for key, value in query_params.items():
            if key in df.columns:
                if isinstance(value, str):
                    # String filtering (case-insensitive contains)
                    df = df[df[key].astype(str).str.contains(value, case=False, na=False)]
                elif isinstance(value, (int, float)):
                    # Numeric filtering (exact match)
                    df = df[df[key] == value]
                elif isinstance(value, list):
                    # List filtering (isin)
                    df = df[df[key].isin(value)]
        
        return df
    
    def search_text_content(
        self,
        user_role: UserRole,
        search_query: str,
        department_filter: Optional[str] = None
    ) -> QueryResult:
        """
        Search through text content (markdown, text files)
        MCP-style tool for unstructured data search
        """
        start_time = datetime.now()
        
        try:
            results = []
            source_files = []
            
            # Get accessible sources
            accessible_sources = self.get_available_data_sources(user_role)
            
            # Filter by department if specified
            if department_filter:
                accessible_sources = [
                    s for s in accessible_sources 
                    if s.department.value == department_filter.lower()
                ]
            
            # Search through text-based files
            for source in accessible_sources:
                if source.data_type in [DataType.MARKDOWN, DataType.TEXT]:
                    matches = self._search_in_file(source.path, search_query)
                    if matches:
                        results.extend(matches)
                        source_files.append(source.path)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return QueryResult(
                success=True,
                data=results,
                metadata={
                    "search_query": search_query,
                    "total_matches": len(results),
                    "files_searched": len(accessible_sources),
                    "department_filter": department_filter
                },
                source_files=source_files,
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Text search failed: {str(e)}")
            
            return QueryResult(
                success=False,
                data=None,
                metadata={},
                source_files=[],
                processing_time=processing_time,
                error=str(e)
            )
    
    def _search_in_file(self, file_path: str, search_query: str) -> List[Dict[str, Any]]:
        """Search for query in a specific file"""
        matches = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                lines = content.split('\n')
                
                # Search for query (case-insensitive)
                query_pattern = re.compile(re.escape(search_query), re.IGNORECASE)
                
                for line_num, line in enumerate(lines, 1):
                    if query_pattern.search(line):
                        # Get context (surrounding lines)
                        start_line = max(0, line_num - 3)
                        end_line = min(len(lines), line_num + 2)
                        context = '\n'.join(lines[start_line:end_line])
                        
                        matches.append({
                            "file": file_path,
                            "line_number": line_num,
                            "matched_line": line.strip(),
                            "context": context,
                            "relevance_score": self._calculate_relevance(line, search_query)
                        })
        
        except Exception as e:
            logger.warning(f"Failed to search in file {file_path}: {str(e)}")
        
        # Sort by relevance score
        matches.sort(key=lambda x: x["relevance_score"], reverse=True)
        return matches[:10]  # Return top 10 matches per file
    
    def _calculate_relevance(self, text: str, query: str) -> float:
        """Calculate relevance score for search results"""
        text_lower = text.lower()
        query_lower = query.lower()
        
        # Exact match gets highest score
        if query_lower in text_lower:
            score = 1.0
            # Bonus for exact word match
            if f" {query_lower} " in f" {text_lower} ":
                score += 0.5
            # Bonus for beginning of line
            if text_lower.strip().startswith(query_lower):
                score += 0.3
            return score
        
        # Partial word matches
        query_words = query_lower.split()
        text_words = text_lower.split()
        
        matches = sum(1 for word in query_words if word in text_words)
        return matches / len(query_words) if query_words else 0
    
    def get_data_summary(self, user_role: UserRole) -> Dict[str, Any]:
        """Get summary of available data for user role"""
        accessible_sources = self.get_available_data_sources(user_role)
        
        summary = {
            "total_sources": len(accessible_sources),
            "by_department": {},
            "by_data_type": {},
            "total_size_mb": 0
        }
        
        for source in accessible_sources:
            # Count by department
            dept = source.department.value
            summary["by_department"][dept] = summary["by_department"].get(dept, 0) + 1
            
            # Count by data type
            dtype = source.data_type.value
            summary["by_data_type"][dtype] = summary["by_data_type"].get(dtype, 0) + 1
            
            # Sum total size
            summary["total_size_mb"] += source.size_bytes / (1024 * 1024)
        
        summary["total_size_mb"] = round(summary["total_size_mb"], 2)
        
        return summary

    @lru_cache(maxsize=128)
    def _get_cached_file_content(self, file_path: str, file_hash: str) -> str:
        """Get cached file content using LRU cache"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.warning(f"Failed to read file {file_path}: {str(e)}")
            return ""

    def _save_cache(self, cache_key: str, data: Any) -> None:
        """Save data to disk cache"""
        try:
            cache_file = self.cache_directory / f"{cache_key}.pkl"
            with open(cache_file, 'wb') as f:
                pickle.dump(data, f)
        except Exception as e:
            logger.warning(f"Failed to save cache {cache_key}: {str(e)}")

    def _load_cache(self, cache_key: str) -> Any:
        """Load data from disk cache"""
        try:
            cache_file = self.cache_directory / f"{cache_key}.pkl"
            if cache_file.exists():
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
        except Exception as e:
            logger.warning(f"Failed to load cache {cache_key}: {str(e)}")
        return None

    def clear_cache(self) -> None:
        """Clear all cached data"""
        try:
            for cache_file in self.cache_directory.glob("*.pkl"):
                cache_file.unlink()
            self._get_cached_file_content.cache_clear()
            logger.info("Cache cleared successfully")
        except Exception as e:
            logger.error(f"Failed to clear cache: {str(e)}")

    def get_memory_usage(self) -> Dict[str, Any]:
        """Get memory usage statistics"""
        stats = {
            "cache_hits": self._get_cached_file_content.cache_info().hits,
            "cache_misses": self._get_cached_file_content.cache_info().misses,
            "cache_size": self._get_cached_file_content.cache_info().currsize,
            "data_sources_count": len(self.data_sources),
            "python_objects": len(gc.get_objects())
        }

        # Try to get process memory info if psutil is available
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            stats.update({
                "rss_mb": memory_info.rss / 1024 / 1024,  # Resident Set Size
                "vms_mb": memory_info.vms / 1024 / 1024,  # Virtual Memory Size
            })
        except ImportError:
            stats.update({
                "rss_mb": "psutil not available",
                "vms_mb": "psutil not available"
            })

        return stats


# Global data processor instance
data_processor = DataProcessor()
