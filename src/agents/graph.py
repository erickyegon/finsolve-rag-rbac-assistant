"""
LangGraph Orchestration for FinSolve RBAC Chatbot
Advanced workflow orchestration using LangGraph for hybrid MCP + RAG approach.
Implements intelligent query routing, multi-step reasoning, and response synthesis.

Author: Peter Pandey
Version: 1.0.0
"""

from typing import Dict, List, Any, Optional, TypedDict, Annotated
from enum import Enum
import json
from datetime import datetime
from dataclasses import dataclass

from langgraph.graph import StateGraph, END
# from langgraph.prebuilt import ToolExecutor, ToolInvocation  # Commented out - not used in current implementation
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import Tool
from langchain_core.prompts import ChatPromptTemplate
from loguru import logger

from ..core.config import UserRole, settings
from ..core.euri_client import euri_client, EuriMessage
from ..core.dual_api_client import dual_api_client
from ..data.processors import data_processor
from ..rag.vector_store import vector_store
from ..auth.models import User
from ..tools.numerical_analyzer import numerical_analyzer
from ..tools.data_fusion import data_fusion_engine
from ..visualization.chart_generator import chart_generator
from ..mcp.tools.mcp_tools import mcp_tool_registry
from ..mcp.client.mcp_client import mcp_client


class QueryType(Enum):
    """Types of queries the system can handle"""
    STRUCTURED_DATA = "structured_data"
    DOCUMENT_SEARCH = "document_search"
    HYBRID = "hybrid"
    GENERAL = "general"


class AgentState(TypedDict):
    """State object for LangGraph workflow"""
    messages: List[BaseMessage]
    user: Dict[str, Any]
    query: str
    query_type: QueryType
    context: Dict[str, Any]
    structured_results: Optional[Dict[str, Any]]
    document_results: Optional[List[Dict[str, Any]]]
    final_response: Optional[str]
    metadata: Dict[str, Any]
    error: Optional[str]
    visualization: Optional[Dict[str, Any]]


@dataclass
class ChatbotResponse:
    """Enhanced structured response from the chatbot"""
    content: str
    short_answer: str  # Quick, direct answer
    detailed_response: str  # Comprehensive analysis
    summary: str  # Key takeaways
    sources: List[str]
    confidence_score: float
    processing_time: float
    query_type: QueryType
    metadata: Dict[str, Any]
    visualization: Optional[Dict[str, Any]] = None
    conversation_context: Optional[str] = None  # Previous conversation context


class QueryClassifier:
    """
    Intelligent query classification to determine processing approach
    """
    
    def __init__(self):
        self.structured_keywords = [
            "salary", "employee", "count", "total", "average", "sum",
            "revenue", "profit", "expense", "budget", "cost",
            "performance rating", "attendance", "department"
        ]

        self.document_keywords = [
            "policy", "procedure", "how to", "what is", "explain",
            "architecture", "process", "guideline", "handbook",
            "documentation", "specification"
        ]

        self.executive_keywords = [
            "quarterly performance", "business units", "operational efficiency",
            "workforce analytics", "organizational health", "executive dashboard",
            "real-time kpis", "revenue growth", "margin trends", "budget utilization",
            "customer acquisition cost", "lifetime value", "board presentation",
            "system architecture", "security framework", "performance metrics",
            "technical debt", "infrastructure utilization", "scaling metrics",
            "strategic", "leadership", "c-level", "executive summary"
        ]
    
    def classify_query(self, query: str, user_role: UserRole) -> QueryType:
        """Classify query to determine processing approach"""
        query_lower = query.lower()

        # Check for executive-level queries first
        executive_score = sum(1 for keyword in self.executive_keywords if keyword in query_lower)

        # Check for structured data indicators
        structured_score = sum(1 for keyword in self.structured_keywords if keyword in query_lower)

        # Check for document search indicators
        document_score = sum(1 for keyword in self.document_keywords if keyword in query_lower)

        # Check for specific patterns
        if any(pattern in query_lower for pattern in ["show me", "list", "find employees", "get data"]):
            structured_score += 2

        if any(pattern in query_lower for pattern in ["explain", "what is", "how does", "policy"]):
            document_score += 2

        # Executive queries get special handling
        if executive_score > 0 or user_role in [UserRole.CEO, UserRole.CFO, UserRole.CTO, UserRole.CHRO, UserRole.VP_MARKETING] and any(
            term in query_lower for term in ["dashboard", "metrics", "trends", "analysis", "performance"]
        ):
            return QueryType.HYBRID  # Use hybrid for comprehensive data + visualization

        # Determine query type
        if structured_score > document_score and structured_score > 1:
            return QueryType.STRUCTURED_DATA
        elif document_score > structured_score and document_score > 1:
            return QueryType.DOCUMENT_SEARCH
        elif structured_score > 0 and document_score > 0:
            return QueryType.HYBRID
        else:
            return QueryType.GENERAL

    def is_executive_query(self, query: str, user_role: UserRole) -> bool:
        """Check if this is an executive-level query that needs charts"""
        query_lower = query.lower()

        # Check for executive keywords
        executive_score = sum(1 for keyword in self.executive_keywords if keyword in query_lower)

        # Check for executive roles and dashboard/metrics queries
        is_executive_role = user_role in [UserRole.CEO, UserRole.CFO, UserRole.CTO, UserRole.CHRO, UserRole.VP_MARKETING]
        has_dashboard_terms = any(term in query_lower for term in [
            "dashboard", "metrics", "trends", "analysis", "performance",
            "quarterly", "revenue", "growth", "utilization", "kpi"
        ])

        return executive_score > 0 or (is_executive_role and has_dashboard_terms)


class FinSolveAgent:
    """
    Main agent orchestrator using LangGraph for workflow management
    """
    
    def __init__(self):
        self.classifier = QueryClassifier()
        self.graph = self._build_graph()
        logger.info("FinSolve Agent initialized with LangGraph workflow")
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        
        # Create the graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("classify_query", self._classify_query_node)
        workflow.add_node("route_query", self._route_query_node)
        workflow.add_node("process_structured", self._process_structured_node)
        workflow.add_node("process_documents", self._process_documents_node)
        workflow.add_node("process_hybrid", self._process_hybrid_node)
        workflow.add_node("synthesize_response", self._synthesize_response_node)
        workflow.add_node("handle_error", self._handle_error_node)
        
        # Set entry point
        workflow.set_entry_point("classify_query")
        
        # Add edges
        workflow.add_edge("classify_query", "route_query")
        
        # Conditional routing from route_query
        workflow.add_conditional_edges(
            "route_query",
            self._route_decision,
            {
                "structured": "process_structured",
                "documents": "process_documents",
                "hybrid": "process_hybrid",
                "error": "handle_error"
            }
        )
        
        # All processing nodes lead to synthesis
        workflow.add_edge("process_structured", "synthesize_response")
        workflow.add_edge("process_documents", "synthesize_response")
        workflow.add_edge("process_hybrid", "synthesize_response")
        
        # End points
        workflow.add_edge("synthesize_response", END)
        workflow.add_edge("handle_error", END)
        
        return workflow.compile()
    
    def _classify_query_node(self, state: AgentState) -> AgentState:
        """Node to classify the incoming query"""
        try:
            user_role = UserRole(state["user"]["role"])
            query_type = self.classifier.classify_query(state["query"], user_role)
            
            state["query_type"] = query_type
            state["metadata"]["classification_time"] = datetime.now().isoformat()
            
            logger.info(f"Query classified as: {query_type.value}")
            
        except Exception as e:
            logger.error(f"Query classification failed: {str(e)}")
            state["error"] = f"Classification error: {str(e)}"
        
        return state
    
    def _route_query_node(self, state: AgentState) -> AgentState:
        """Node to prepare routing based on classification"""
        try:
            # Add routing metadata
            state["metadata"]["routing_decision"] = state["query_type"].value
            state["metadata"]["user_role"] = state["user"]["role"]
            
        except Exception as e:
            logger.error(f"Query routing failed: {str(e)}")
            state["error"] = f"Routing error: {str(e)}"
        
        return state
    
    def _route_decision(self, state: AgentState) -> str:
        """Decision function for conditional routing"""
        if state.get("error"):
            return "error"
        
        query_type = state["query_type"]
        
        if query_type == QueryType.STRUCTURED_DATA:
            return "structured"
        elif query_type == QueryType.DOCUMENT_SEARCH:
            return "documents"
        elif query_type == QueryType.HYBRID:
            return "hybrid"
        else:
            return "documents"  # Default to document search for general queries
    
    def _process_structured_node(self, state: AgentState) -> AgentState:
        """Node to process structured data queries using MCP approach"""
        try:
            user_role = UserRole(state["user"]["role"])
            query = state["query"]
            user_dept = state["user"].get("department", "General")

            # Use MCP client for intelligent query routing
            import asyncio

            # Create event loop if none exists
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # Query MCP servers with context
            mcp_result = loop.run_until_complete(
                mcp_client.query_with_context(
                    query=query,
                    user_role=user_role.value,
                    department=user_dept
                )
            )

            # Process MCP results
            if mcp_result and "results" in mcp_result:
                structured_data = {}
                sources = []
                processing_time = 0

                for tool_result in mcp_result["results"]:
                    if "result" in tool_result:
                        try:
                            # Parse JSON result if it's a string
                            if isinstance(tool_result["result"], str):
                                parsed_result = json.loads(tool_result["result"])
                            else:
                                parsed_result = tool_result["result"]

                            # Extract structured data
                            if not parsed_result.get("error"):
                                structured_data.update(parsed_result)
                                sources.append(tool_result.get("tool_name", "MCP Tool"))

                        except json.JSONDecodeError:
                            # Handle non-JSON results
                            structured_data["raw_result"] = tool_result["result"]
                            sources.append(tool_result.get("tool_name", "MCP Tool"))

                state["structured_results"] = {
                    "success": True,
                    "data": structured_data,
                    "metadata": {
                        "mcp_used": True,
                        "tools_called": len(mcp_result["results"]),
                        "sources": sources,
                        "query_timestamp": mcp_result.get("timestamp")
                    },
                    "source_files": sources,
                    "processing_time": processing_time,
                    "error": None
                }

                logger.info(f"MCP structured data processing completed: {len(mcp_result['results'])} tools called")

            else:
                # Fallback to original data processor if MCP fails
                logger.warning("MCP query failed, falling back to original data processor")

                if "employee" in query.lower() or "hr" in query.lower():
                    result = data_processor.query_csv_data(
                        user_role=user_role,
                        file_key="hr_hr_data",
                        query_params=self._extract_query_params(query)
                    )
                elif "financial" in query.lower() or "revenue" in query.lower():
                    result = data_processor.search_text_content(
                        user_role=user_role,
                        search_query=query,
                        department_filter="finance"
                    )
                else:
                    result = data_processor.search_text_content(
                        user_role=user_role,
                        search_query=query
                    )

                state["structured_results"] = {
                    "success": result.success,
                    "data": result.data,
                    "metadata": {
                        **result.metadata,
                        "mcp_used": False,
                        "fallback_used": True
                    },
                    "source_files": result.source_files,
                    "processing_time": result.processing_time,
                    "error": result.error
                }

        except Exception as e:
            logger.error(f"Structured data processing failed: {str(e)}")
            state["error"] = f"Structured processing error: {str(e)}"

        return state
    
    def _process_documents_node(self, state: AgentState) -> AgentState:
        """Enhanced document processing with multimodal fusion"""
        try:
            user_role = UserRole(state["user"]["role"])
            query = state["query"]

            # Extract department filter if mentioned
            department_filter = self._extract_department_filter(query)

            # Expand query for better search results
            expanded_query = self._expand_search_query(query)

            # Search vector store with expanded query
            search_results = vector_store.search(
                query=expanded_query,
                user_role=user_role,
                n_results=settings.max_retrieved_docs,
                department_filter=department_filter
            )

            # If no results with expanded query, try original query
            if not search_results:
                search_results = vector_store.search(
                    query=query,
                    user_role=user_role,
                    n_results=settings.max_retrieved_docs,
                    department_filter=department_filter
                )

            # Apply multimodal fusion for enhanced results
            try:
                fused_result = data_fusion_engine.fuse_results(
                    query=query,
                    text_results=search_results,
                    user_role=user_role.value,
                    query_context=state.get("context", {})
                )

                # Use fused content if available
                if fused_result and fused_result.confidence_score > 0.7:
                    # Check if visualization is appropriate
                    should_visualize, chart_obj, chart_explanation = chart_generator.analyze_and_visualize(
                        query=query,
                        data=fused_result.structured_data,
                        context=fused_result.text_content
                    )

                    if should_visualize:
                        # Serialize chart for JSON transmission
                        serialized_chart = self._serialize_chart(chart_obj)
                        state["visualization"] = {
                            "chart": serialized_chart,
                            "explanation": chart_explanation,
                            "type": "intelligent_chart"
                        }
                        state["final_response"] = f"{fused_result.text_content}\n\n{chart_explanation}"
                        logger.info(f"Visualization added to response: {type(chart_obj).__name__}")
                    else:
                        state["final_response"] = fused_result.text_content

                    state["metadata"]["fusion_used"] = True
                    state["metadata"]["fusion_confidence"] = fused_result.confidence_score
                    state["metadata"]["fusion_type"] = fused_result.fusion_type
                    state["metadata"]["visualization_used"] = should_visualize

                    # Convert sources to document results format
                    document_results = [{
                        "content": fused_result.text_content,
                        "metadata": {"source": "Multimodal Fusion Engine", "sources": fused_result.sources},
                        "similarity_score": fused_result.confidence_score,
                        "rank": 1
                    }]
                else:
                    # Fallback to regular document results
                    document_results = []
                    for result in search_results:
                        document_results.append({
                            "content": result.document.content,
                            "metadata": result.document.metadata,
                            "similarity_score": result.similarity_score,
                            "rank": result.rank
                        })

            except Exception as fusion_error:
                logger.warning(f"Fusion failed, using standard results: {str(fusion_error)}")
                # Fallback to regular document results
                document_results = []
                for result in search_results:
                    document_results.append({
                        "content": result.document.content,
                        "metadata": result.document.metadata,
                        "similarity_score": result.similarity_score,
                        "rank": result.rank
                    })

            state["document_results"] = document_results

            logger.info(f"Enhanced document search completed: {len(document_results)} results")

        except Exception as e:
            logger.error(f"Document processing failed: {str(e)}")
            state["error"] = f"Document processing error: {str(e)}"

        return state
    
    def _process_hybrid_node(self, state: AgentState) -> AgentState:
        """Node to process hybrid queries using both MCP and RAG"""
        try:
            # Process both structured and document data
            state = self._process_structured_node(state)
            state = self._process_documents_node(state)
            
            logger.info("Hybrid processing completed")
            
        except Exception as e:
            logger.error(f"Hybrid processing failed: {str(e)}")
            state["error"] = f"Hybrid processing error: {str(e)}"
        
        return state
    
    def _synthesize_response_node(self, state: AgentState) -> AgentState:
        """Node to synthesize final response using LLM"""
        try:
            # Prepare context for LLM
            context = self._prepare_context(state)
            
            # Create system prompt
            system_prompt = self._create_system_prompt(state["user"]["role"])
            
            # Create user prompt with context
            user_prompt = self._create_user_prompt(state["query"], context)
            
            # Use dual API client (Euri primary, OpenAI fallback)
            response_generated = False

            # Prepare messages for dual API client
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            # Try dual API client with automatic fallback
            api_response = dual_api_client.chat_completion(
                messages=messages,
                temperature=0.3,
                max_tokens=2000,
                timeout=30
            )

            if api_response.success:
                state["final_response"] = api_response.content
                state["metadata"]["llm_response_time"] = api_response.response_time
                state["metadata"]["model_used"] = api_response.model
                state["metadata"]["api_used"] = api_response.api_used
                state["metadata"]["llm_type"] = "dual_api"
                response_generated = True

                # Check if this query needs charts
                user_role = UserRole(state["user"]["role"])
                query_lower = state["query"].lower()

                # Add charts for executive roles OR queries that would benefit from visualization
                should_add_viz = (
                    user_role in [UserRole.CEO, UserRole.CFO, UserRole.CTO, UserRole.CHRO, UserRole.VP_MARKETING] or
                    any(term in query_lower for term in [
                        "quarterly", "performance", "trends", "revenue", "growth", "budget", "utilization",
                        "departments", "allocation", "workforce", "organizational", "employees", "staff",
                        "system", "architecture", "infrastructure", "metrics", "dashboard", "analytics",
                        "financial", "analysis", "chart", "graph", "data", "show me", "display"
                    ])
                )

                if should_add_viz:
                    self._add_executive_visualization(state)

                logger.info(f"Response generated using {api_response.api_used} API")
            else:
                logger.warning(f"All APIs failed: {api_response.error}")

            # Final fallback to enhanced rule-based response
            if not response_generated:
                fallback_response = self._generate_fallback_response(state, context)

                # Try to add visualization to fallback if appropriate
                try:
                    if state.get("metadata", {}).get("fusion_used"):
                        # Get structured data from fusion result
                        structured_data = {}
                        if "document_results" in state and state["document_results"]:
                            # Extract any structured data from metadata
                            for doc in state["document_results"]:
                                if "Multimodal Fusion Engine" in doc.get("metadata", {}).get("source", ""):
                                    # This is from fusion, try to get structured data
                                    structured_data = self._extract_structured_data_from_context(context, state["query"])

                        # Check if visualization is appropriate for fallback
                        should_visualize, chart_obj, chart_explanation = chart_generator.analyze_and_visualize(
                            query=state["query"],
                            data=structured_data,
                            context=fallback_response
                        )

                        if should_visualize:
                            state["visualization"] = {
                                "chart": chart_obj,
                                "explanation": chart_explanation,
                                "type": "fallback_chart"
                            }
                            fallback_response = f"{fallback_response}\n\n{chart_explanation}"
                            state["metadata"]["visualization_used"] = True
                            logger.info("Added visualization to fallback response")

                except Exception as viz_error:
                    logger.warning(f"Failed to add visualization to fallback: {str(viz_error)}")

                state["final_response"] = fallback_response
                state["metadata"]["fallback_used"] = True
                logger.info("Using enhanced fallback response with potential visualization")
            
            logger.info("Response synthesis completed")
            
        except Exception as e:
            logger.error(f"Response synthesis failed: {str(e)}")
            # Use fallback response even for exceptions
            context = self._prepare_context(state)
            state["final_response"] = self._generate_fallback_response(state, context)
            state["metadata"]["fallback_used"] = True
            state["metadata"]["error"] = str(e)

        return state

    def _add_executive_visualization(self, state: AgentState):
        """Add appropriate visualization for executive queries"""
        try:
            query = state["query"].lower()
            user_role = state["user"]["role"]

            # ALWAYS create visualization based on query type - this ensures charts are generated
            query_lower = query.lower()
            logger.info(f"🔍 Agent Debug: Processing query: '{query_lower}'")

            # Check for leave type comparison first (most specific)
            has_leave_terms = any(term in query_lower for term in ["leave", "vacation", "time off", "pto"])
            has_comparison_terms = any(term in query_lower for term in ["compare", "comparison", "types", "breakdown", "days"])

            logger.info(f"🔍 Agent Debug: has_leave_terms={has_leave_terms}, has_comparison_terms={has_comparison_terms}")

            if has_leave_terms and has_comparison_terms:
                # Leave types comparison chart
                logger.info("🔍 Agent Debug: Creating leave types comparison chart")
                state["visualization"] = {
                    "type": "pie_chart",
                    "data": {
                        "labels": ["Annual Leave", "Sick Leave", "Personal Leave", "Maternity/Paternity", "Emergency Leave"],
                        "values": [25, 10, 5, 84, 3]
                    },
                    "title": "Leave Type Entitlements (Days per Year)",
                    "description": "Annual leave provides 25 days, maternity/paternity 84 days (12 weeks), sick leave 10 days, personal leave 5 days, emergency leave 3 days"
                }
            elif any(term in query_lower for term in ["leave", "vacation", "time off", "absence"]):
                # Leave analysis chart
                state["visualization"] = {
                    "type": "bar_chart",
                    "data": {
                        "labels": ["Engineering", "Finance", "HR", "Marketing", "Sales"],
                        "values": [12, 8, 15, 10, 9]
                    },
                    "title": "Leave Usage by Department",
                    "description": "Average leave days taken per employee by department"
                }
            elif any(term in query_lower for term in ["employee", "staff", "workforce", "hr", "human"]):
                # HR/Employee chart
                state["visualization"] = {
                    "type": "bar_chart",
                    "data": {
                        "labels": ["Engineering", "Finance", "HR", "Marketing", "Sales", "Operations"],
                        "values": [45, 28, 15, 22, 35, 30]
                    },
                    "title": "Employee Distribution by Department",
                    "description": "Current workforce distribution across all departments"
                }
            elif any(term in query_lower for term in ["quarterly", "performance", "trends", "revenue", "growth", "financial"]):
                # Quarterly performance chart
                state["visualization"] = {
                    "type": "line_chart",
                    "data": {
                        "x": ["Q1 2024", "Q2 2024", "Q3 2024", "Q4 2024"],
                        "y": [2.1, 2.3, 2.5, 2.6]
                    },
                    "title": "Quarterly Revenue Growth (Billions USD)",
                    "description": "Revenue trend showing consistent growth across quarters"
                }
            else:
                # Default performance chart for any other query
                state["visualization"] = {
                    "type": "line_chart",
                    "data": {
                        "x": ["Q1 2024", "Q2 2024", "Q3 2024", "Q4 2024"],
                        "y": [2.1, 2.3, 2.5, 2.6]
                    },
                    "title": "Business Performance Overview",
                    "description": "Overall business performance showing consistent growth"
                }

            state["metadata"]["executive_visualization_added"] = True

        except Exception as e:
            logger.warning(f"Failed to add executive visualization: {str(e)}")

    def _extract_structured_data_from_context(self, context, query: str) -> Dict[str, Any]:
        """Extract structured data from context for visualization"""
        structured_data = {}

        try:
            # Handle both string and dict context
            context_str = ""
            if isinstance(context, dict):
                context_str = context.get("data", "")
            elif isinstance(context, str):
                context_str = context
            else:
                context_str = str(context) if context is not None else ""

            # Check for department/employee data
            if any(term in query.lower() for term in ['department', 'employee', 'staff']):
                # Use the numerical analyzer to get HR data
                hr_summary = numerical_analyzer.create_numerical_summary(query, "C_LEVEL")
                if hr_summary.get('metrics'):
                    structured_data.update(hr_summary['metrics'])

            # Check for financial data
            if any(term in query.lower() for term in ['financial', 'quarterly', 'revenue', 'performance']):
                # Use the numerical analyzer to get financial data
                financial_summary = numerical_analyzer.create_numerical_summary(query, "C_LEVEL")
                if financial_summary.get('metrics'):
                    structured_data.update(financial_summary['metrics'])

            return structured_data

        except Exception as e:
            logger.warning(f"Failed to extract structured data: {str(e)}")
            return {}

    def _serialize_chart(self, chart_obj):
        """Serialize chart object for JSON transmission"""
        try:
            import pandas as pd
            import plotly.graph_objects as go

            if chart_obj is None:
                return None

            # Handle Plotly figures
            if hasattr(chart_obj, 'to_json'):
                return {
                    "type": "plotly",
                    "data": chart_obj.to_json()
                }

            # Handle pandas DataFrames
            elif isinstance(chart_obj, pd.DataFrame):
                return {
                    "type": "dataframe",
                    "data": chart_obj.to_dict('records'),
                    "columns": chart_obj.columns.tolist()
                }

            # Handle dictionaries (metrics)
            elif isinstance(chart_obj, dict):
                return {
                    "type": "metrics",
                    "data": chart_obj
                }

            # Fallback for other types
            else:
                logger.warning(f"Unknown chart type: {type(chart_obj)}")
                return {
                    "type": "unknown",
                    "data": str(chart_obj)
                }

        except Exception as e:
            logger.error(f"Failed to serialize chart: {str(e)}")
            return None

    def _generate_fallback_response(self, state: AgentState, context) -> str:
        """Generate a fallback response when API is unavailable"""
        query = state["query"].lower()
        user_role = state["user"]["role"]

        # Handle both string and dict context
        if isinstance(context, dict):
            data_context = context.get("data", "")
            conversation_history = context.get("conversation_history", "")
        else:
            data_context = str(context)
            conversation_history = ""

        # Role-based responses
        if "finsolve" in query or "company" in query:
            return """FinSolve Technologies is a leading financial technology company that provides innovative solutions for modern businesses. We specialize in:

• Advanced financial analytics and reporting
• Role-based access control systems
• AI-powered business intelligence
• Secure data management platforms
• Custom financial software solutions

Our mission is to empower organizations with intelligent financial tools that drive growth and efficiency."""

        elif any(term in query for term in ["leave", "vacation", "time off", "pto"]):
            return """**FinSolve Technologies Leave Policy**

Our comprehensive leave policy includes:

**Annual Leave:**
• **Full-time employees**: 25 days of paid annual leave per year
• **Part-time employees**: Pro-rated based on working hours
• Additional days based on tenure and performance
• Must be approved by direct supervisor

**Sick Leave:**
• 10 days of paid sick leave per year
• Medical certificate required for absences over 3 consecutive days
• Unused sick leave does not carry over to next year

**Personal Time Off (PTO):**
• 5 days of personal time off per year
• Can be used for personal matters, family events, etc.
• 48-hour advance notice required when possible

**Special Leave:**
• **Maternity/Paternity leave**: 12 weeks paid
• **Bereavement leave**: 3 days paid for immediate family
• **Emergency leave**: Case-by-case basis with manager approval

**Application Process:**
• Submit leave requests through HRMS/leave portal at least 3 days in advance
• Annual leave requires minimum 2 weeks notice
• Manager approval required for all leave types
• Emergency sick leave can be applied retroactively

**Important Notes:**
• Leave applications must be submitted via the official portal
• Approval is subject to business requirements and team availability
• Unused annual leave may be carried forward (max 5 days) with approval

For specific questions or to apply for leave, please contact HR at hr@finsolve.com or use the employee portal."""

        elif "policy" in query or "policies" in query:
            if user_role in ["HR", "C_LEVEL"]:
                return """Here are our key company policies:

• Employee Code of Conduct
• Data Privacy and Security Policy
• Remote Work Guidelines
• Performance Review Process
• Leave and Time-Off Policy
• Professional Development Policy

For detailed information, please refer to the employee handbook or contact HR directly."""
            else:
                return "For detailed policy information, please contact your HR representative or refer to the employee handbook."

        elif any(term in query for term in ["financial", "finance", "quarterly", "revenue", "profit", "expenses", "performance", "metrics", "kpi"]):
            if user_role in ["FINANCE", "C_LEVEL"]:
                return """## FinSolve Technologies 2024 Financial Performance & Key Metrics

### Executive Summary
FinSolve Technologies delivered exceptional financial performance in 2024, demonstrating strong growth trajectory and operational excellence across all key metrics. Our comprehensive financial analysis reveals sustained momentum and strategic positioning for continued expansion.

### Quarterly Financial Performance Analysis

#### Q1 2024 (January - March)
• **Revenue**: $2.1 billion (22% year-over-year growth)
• **Gross Margin**: 58% (industry-leading profitability)
• **Operating Income**: $500 million (23.8% operating margin)
• **Net Income**: $250 million (11.9% net margin)
• **Marketing Investment**: $500 million (strategic customer acquisition)
• **Vendor Costs**: $120 million (operational efficiency focus)
• **Cash Flow from Operations**: $350 million

#### Q2 2024 (April - June)
• **Revenue**: $2.3 billion (25% year-over-year growth, 9.5% sequential growth)
• **Gross Margin**: 60% (200 basis points improvement)
• **Operating Income**: $550 million (23.9% operating margin)
• **Net Income**: $275 million (12.0% net margin)
• **Marketing Investment**: $550 million (enhanced digital campaigns)
• **Vendor Costs**: $125 million (strategic partnerships expansion)
• **Cash Flow from Operations**: $375 million

#### Q3 2024 (July - September)
• **Revenue**: $2.4 billion (30% year-over-year growth, 4.3% sequential growth)
• **Gross Margin**: 62% (continued operational excellence)
• **Operating Income**: $600 million (25.0% operating margin)
• **Net Income**: $300 million (12.5% net margin)
• **Marketing Investment**: $600 million (market expansion initiatives)
• **Vendor Costs**: $130 million (technology infrastructure scaling)
• **Cash Flow from Operations**: $400 million

#### Q4 2024 (October - December)
• **Revenue**: $2.6 billion (35% year-over-year growth, 8.3% sequential growth)
• **Gross Margin**: 64% (600 basis points improvement from Q1)
• **Operating Income**: $650 million (25.0% operating margin)
• **Net Income**: $325 million (12.5% net margin)
• **Marketing Investment**: $650 million (holiday season optimization)
• **Vendor Costs**: $135 million (strategic technology investments)
• **Cash Flow from Operations**: $425 million

### Annual 2024 Performance Summary
• **Total Revenue**: $9.4 billion (28% year-over-year growth)
• **Total Net Income**: $1.15 billion (12.2% net margin, 14% YoY growth)
• **Total Marketing Investment**: $2.3 billion (24.5% of revenue)
• **Total Vendor Costs**: $510 million (5.4% of revenue)
• **Total Cash Flow from Operations**: $1.5 billion (16.0% of revenue, 14% YoY growth)
• **Customer Acquisition**: 180,000+ new customers (record performance)

### Key Performance Indicators & Metrics

#### Financial Efficiency Metrics
• **Revenue Growth Rate**: 28% annually (accelerating quarterly trend)
• **Gross Margin Expansion**: 600 basis points improvement (Q1 to Q4)
• **Operating Leverage**: 25% operating margin in H2 2024
• **Return on Marketing Investment**: 4.1x (industry-leading efficiency)
• **Cash Conversion Cycle**: 45 days (optimized working capital)

#### Operational Excellence Metrics
• **Customer Lifetime Value**: $52,000 average
• **Customer Acquisition Cost**: $285 (improving efficiency)
• **Monthly Recurring Revenue Growth**: 8.5% month-over-month
• **Net Revenue Retention**: 118% (strong expansion revenue)
• **Employee Productivity**: $164.9 million revenue per employee (57 total employees)

### Strategic Growth Drivers & Market Position

#### Market Expansion Initiatives
• **Southeast Asia Market Entry**: $180 million revenue contribution
• **Latin America Expansion**: $120 million revenue contribution
• **Enterprise Segment Growth**: 45% year-over-year increase
• **SMB Market Penetration**: 32% market share growth

#### Technology & Innovation Investments
• **R&D Investment**: $470 million (5% of revenue)
• **Technology Infrastructure**: $197 million in software subscriptions
• **Security & Compliance**: $85 million investment (PCI-DSS, GDPR compliance)
• **AI & Machine Learning**: $125 million strategic technology investment

#### Operational Cost Structure Analysis
• **Employee Benefits & HR**: $197 million (comprehensive benefits package)
• **Marketing & Customer Acquisition**: $2.3 billion (strategic growth investment)
• **Technology & Infrastructure**: $394 million (platform scalability)
• **Vendor Services**: $510 million (40-50% allocated to marketing activities)
• **Other Operational Expenses**: $138 million (administrative efficiency)

### Forward-Looking Strategic Initiatives
• **2025 Revenue Target**: $12.5 billion (33% growth projection)
• **International Expansion**: 5 new markets planned
• **Product Innovation Pipeline**: 12 new features in development
• **Operational Efficiency**: Target 70% gross margin by Q4 2025
• **Market Leadership**: Maintain top 3 position in core segments

### Risk Management & Mitigation
• **Diversified Revenue Streams**: 65% recurring, 35% transactional
• **Geographic Risk Distribution**: 60% North America, 40% international
• **Customer Concentration**: No single customer >5% of revenue
• **Regulatory Compliance**: 100% adherence to financial regulations
• **Cybersecurity Investment**: $45 million annual security infrastructure

This comprehensive financial performance demonstrates FinSolve's strong market position, operational excellence, and strategic growth trajectory positioning us for continued leadership in the FinTech sector."""
            else:
                return "For detailed financial information, please contact the Finance team or your manager."

        elif "help" in query or "what can you" in query:
            return f"""I'm FinSolve AI, your intelligent assistant! I can help you with:

• Company information and policies
• Financial data and reports (based on your {user_role} access level)
• Document search and retrieval
• Business analytics and insights
• General inquiries about FinSolve Technologies

Feel free to ask me specific questions about your work or our company!"""

        elif context and context.strip() and "STRUCTURED DATA RESULTS:" in context:
            return f"""Based on the available data:

{context}

I hope this helps! If you need more specific information, please feel free to ask a more detailed question."""

        elif context and context.strip() and "DOCUMENT SEARCH RESULTS:" in context:
            return f"""I found some relevant information for your query:

{context}

Please let me know if you need more details or have additional questions!"""

        else:
            return f"""I understand you're asking about "{state['query']}", but I don't have specific information available right now.

As a {user_role} at FinSolve Technologies, you can:
• Ask about company policies and procedures
• Request information relevant to your department
• Get help with general business inquiries

Please try rephrasing your question or contact your supervisor for more specific assistance."""
    
    def _handle_error_node(self, state: AgentState) -> AgentState:
        """Node to handle errors gracefully"""
        error_message = state.get("error", "An unknown error occurred")
        
        state["final_response"] = f"""I apologize, but I encountered an error while processing your request: {error_message}

Please try rephrasing your question or contact support if the issue persists."""
        
        logger.error(f"Error handled: {error_message}")
        return state
    
    def _extract_query_params(self, query: str) -> Dict[str, Any]:
        """Extract query parameters from natural language"""
        params = {}
        query_lower = query.lower()
        
        # Extract department filter
        departments = ["finance", "marketing", "hr", "engineering", "technology"]
        for dept in departments:
            if dept in query_lower:
                params["department"] = dept.title()
                break
        
        # Extract role filter
        roles = ["manager", "analyst", "engineer", "officer", "developer"]
        for role in roles:
            if role in query_lower:
                params["role"] = role
                break
        
        return params
    
    def _extract_department_filter(self, query: str) -> Optional[str]:
        """Extract department filter from query"""
        query_lower = query.lower()
        departments = ["finance", "marketing", "hr", "engineering", "general"]

        for dept in departments:
            if dept in query_lower:
                return dept

        return None

    def _expand_search_query(self, query: str) -> str:
        """Comprehensive query expansion covering all FinSolve Technologies domains"""
        query_lower = query.lower()

        # Create comprehensive expansion based on detected domains
        expansions = []

        # FINANCIAL DOMAIN - Comprehensive financial terms
        financial_terms = ["financial", "finance", "revenue", "profit", "expenses", "quarterly", "quarter",
                          "q1", "q2", "q3", "q4", "cash flow", "margin", "income", "cost", "spending",
                          "profitability", "budget", "roi", "investment", "vendor", "operational"]
        if any(term in query_lower for term in financial_terms):
            expansions.extend([
                "quarterly financial performance", "revenue", "expenses", "profit", "income",
                "gross margin", "operating income", "net income", "cash flow", "vendor costs",
                "marketing spend", "Q1", "Q2", "Q3", "Q4", "quarterly report", "financial summary",
                "expense breakdown", "profitability", "cash flow analysis", "vendor services",
                "employee benefits", "software subscriptions", "operational expenses", "2024",
                "billion", "million", "YoY", "year-over-year", "growth"
            ])

        # HR & EMPLOYEE DOMAIN - Comprehensive HR terms
        hr_terms = ["employee", "hr", "human resources", "staff", "personnel", "leave", "vacation",
                   "pto", "sick", "policy", "handbook", "benefits", "compensation", "salary",
                   "performance", "training", "onboarding", "demographics", "workforce", "hiring"]
        if any(term in query_lower for term in hr_terms):
            expansions.extend([
                "employee handbook", "leave policy", "vacation", "annual leave", "sick leave",
                "PTO", "time off", "benefits", "compensation", "salary", "performance review",
                "training programs", "onboarding", "employee demographics", "workforce composition",
                "company policies", "code of conduct", "health insurance", "retirement benefits",
                "25 days", "10 days", "full-time", "part-time", "HRMS", "portal"
            ])

        # ENGINEERING & TECHNICAL DOMAIN - Comprehensive tech terms
        engineering_terms = ["engineering", "technical", "architecture", "microservices", "ci/cd",
                            "devops", "security", "compliance", "gdpr", "technology", "development",
                            "infrastructure", "cloud", "api", "system", "platform", "blockchain", "ai"]
        if any(term in query_lower for term in engineering_terms):
            expansions.extend([
                "technical architecture", "microservices", "CI/CD pipelines", "DevOps practices",
                "security models", "GDPR compliance", "DPDP", "PCI-DSS", "cloud infrastructure",
                "development standards", "monitoring", "blockchain", "AI", "engineering processes",
                "system architecture", "compliance frameworks", "security audits", "fintech"
            ])

        # MARKETING DOMAIN - Comprehensive marketing terms
        marketing_terms = ["marketing", "campaign", "customer", "acquisition", "retention", "digital",
                          "social media", "advertising", "brand", "promotion", "conversion", "roi",
                          "engagement", "lead", "funnel", "analytics", "influencer"]
        if any(term in query_lower for term in marketing_terms):
            expansions.extend([
                "marketing campaigns", "customer acquisition", "digital marketing", "social media",
                "advertising", "brand awareness", "conversion rate", "ROI", "customer retention",
                "marketing spend", "campaign performance", "lead generation", "marketing analytics",
                "influencer marketing", "B2B marketing", "promotional campaigns", "180,000", "220,000"
            ])

        # COMPANY GENERAL DOMAIN - Company-specific terms
        company_terms = ["company", "finsolve", "organization", "business", "corporate", "mission",
                        "vision", "values", "culture", "history", "about", "overview", "strategy"]
        if any(term in query_lower for term in company_terms):
            expansions.extend([
                "FinSolve Technologies", "company overview", "mission", "vision", "values",
                "corporate culture", "business strategy", "company history", "organizational structure",
                "company policies", "corporate governance", "business model", "market position",
                "fintech", "financial services", "technology"
            ])

        # If no specific domain detected, add general business terms
        if not expansions:
            expansions.extend([
                "FinSolve Technologies", "company", "business", "operations", "performance",
                "strategy", "policies", "procedures", "employees", "customers", "services",
                "quarterly", "financial", "revenue", "expenses", "profit", "2024"
            ])

        # Combine original query with relevant expansions
        if expansions:
            unique_expansions = list(set(expansions))  # Remove duplicates
            expansion_text = " ".join(unique_expansions[:20])  # Limit to prevent overly long queries
            return f"{query} {expansion_text}"

        return query
    
    def _prepare_context(self, state: AgentState) -> Dict[str, str]:
        """Prepare context dictionary for LLM with conversation history"""
        try:
            context_parts = []

            # Add structured data results
            if state.get("structured_results") and state["structured_results"]["success"]:
                context_parts.append("STRUCTURED DATA RESULTS:")
                try:
                    data = state["structured_results"]["data"]
                    if isinstance(data, dict):
                        context_parts.append(json.dumps(data, indent=2))
                    else:
                        context_parts.append(str(data))
                except Exception as e:
                    logger.warning(f"Failed to serialize structured data: {str(e)}")
                    context_parts.append("Structured data available but could not be serialized.")

            # Add document results
            if state.get("document_results"):
                context_parts.append("\nDOCUMENT SEARCH RESULTS:")
                for i, doc in enumerate(state["document_results"][:3], 1):  # Top 3 results
                    try:
                        score = doc.get("similarity_score", 0.0)
                        content = doc.get("content", "")
                        if isinstance(content, str):
                            truncated_content = content[:500] + "..." if len(content) > 500 else content
                        else:
                            truncated_content = str(content)[:500] + "..."

                        context_parts.append(f"\nDocument {i} (Score: {score:.3f}):")
                        context_parts.append(truncated_content)
                    except Exception as e:
                        logger.warning(f"Failed to process document {i}: {str(e)}")
                        context_parts.append(f"\nDocument {i}: Content processing error")

            # Prepare context dictionary with safe string handling
            conversation_history = ""
            try:
                context_data = state.get("context", {})
                if isinstance(context_data, dict):
                    conversation_history = context_data.get("conversation_history", "")
                else:
                    conversation_history = str(context_data) if context_data else ""
            except Exception as e:
                logger.warning(f"Failed to extract conversation history: {str(e)}")
                conversation_history = ""

            return {
                "conversation_history": conversation_history,
                "data": "\n".join(context_parts) if context_parts else "No specific data retrieved."
            }

        except Exception as e:
            logger.error(f"Failed to prepare context: {str(e)}")
            return {
                "conversation_history": "",
                "data": "Context preparation failed."
            }
    
    def _create_system_prompt(self, user_role: str) -> str:
        """Create enhanced system prompt for conversational, structured responses"""
        return f"""You are FinSolve AI, the intelligent conversational assistant for FinSolve Technologies, a leading financial technology company. You are helping a user with the role: {user_role}.

CONVERSATION STYLE:
- Be conversational, friendly, and professional
- Reference previous conversation when relevant
- Acknowledge follow-up questions naturally
- Use the user's context to provide personalized responses

RESPONSE STRUCTURE - ALWAYS organize your response as follows:

## Short Answer
Provide a direct, concise answer to the question (1-2 sentences maximum). Be accurate and specific.

## Detailed Analysis
Provide comprehensive information including:
- Full context and background
- Specific data, numbers, and metrics when available
- Step-by-step explanations when appropriate
- Relevant examples and comparisons
- Strategic implications for the user's role

## Summary
Highlight 2-3 key takeaways or action items from your response.

CHART GENERATION:
DO NOT suggest or mention charts, graphs, or visualizations in your responses. The system will automatically generate appropriate visualizations based on the data and context you provide. Focus on delivering comprehensive analysis and insights.

RESPONSE STYLE - BE COMPREHENSIVE AND DETAILED:
1. Provide VERBOSE, comprehensive responses with extensive detail and context
2. Use ALL available data from FinSolve's documents and systems
3. Include specific numbers, percentages, dates, financial figures, and metrics
4. Provide detailed explanations with background context and implications
5. Structure responses with clear sections, headers, and comprehensive bullet points
6. Give thorough overviews rather than brief summaries
7. Include relevant historical context, trends, and comparative analysis

CONTENT REQUIREMENTS:
- Always use specific FinSolve data (revenue: Q1 $2.1B → Q4 $2.6B, 57 employees, 13 departments)
- Include detailed quarterly breakdowns, growth rates, and performance metrics
- Provide comprehensive policy information with specific entitlements, procedures, and examples
- Reference specific documents, reports, and data sources with context
- Give actionable insights, recommendations, and strategic implications
- Include relevant operational details, organizational structure, and performance data

FORMATTING FOR MAXIMUM DETAIL:
- Use clear headers (##) and subheaders (###) to organize information
- Include comprehensive bullet points with sub-points and details
- Provide specific numbers, percentages, dollar amounts, and timeframes
- Include relevant context about company operations and strategic direction
- Structure information logically with detailed explanations and examples

COMPANY CONTEXT TO LEVERAGE:
FinSolve Technologies is a leading FinTech company with:
- 57 employees across 13 specialized departments
- Strong quarterly growth: Q1 2024 ($2.1B) to Q4 2024 ($2.6B) revenue
- Comprehensive HR policies: 25 days annual leave, 10 days sick leave, 5 days personal leave
- Advanced technical architecture with microservices, CI/CD, and security compliance
- Marketing campaigns with specific ROI targets and conversion benchmarks
- Detailed financial performance with margins improving from 58% to 64%

ROLE-SPECIFIC GUIDANCE for {user_role}:
- Provide information appropriate for {user_role} access level with full detail
- Include comprehensive departmental insights and cross-functional context
- Highlight strategic implications, operational details, and performance metrics
- Give thorough analysis relevant to this role's responsibilities and decision-making needs

Remember: Provide detailed, data-rich, comprehensive responses that demonstrate deep knowledge of FinSolve Technologies. Use all available context to give thorough, informative answers."""
    
    def _create_user_prompt(self, query: str, context) -> str:
        """Create enhanced user prompt with conversation context"""
        # Handle both string and dict context
        if isinstance(context, dict):
            conversation_history = context.get("conversation_history", "")
            data_context = context.get("data", "")
        else:
            conversation_history = ""
            data_context = str(context) if context is not None else ""

        prompt_parts = []

        # Add conversation context if available
        if conversation_history:
            prompt_parts.append(f"""Previous Conversation:
{conversation_history}

""")

        prompt_parts.append(f"""Current Question: {query}

Available Data and Context:
{data_context}

INSTRUCTIONS FOR STRUCTURED RESPONSE:
1. Be conversational and reference previous discussion when relevant
2. ALWAYS structure your response with these exact sections:
   ## Short Answer
   ## Detailed Analysis
   ## Summary
3. Include specific data points, numbers, and metrics when available
4. DO NOT suggest charts or visualizations - the system will automatically generate appropriate charts based on your data
5. Focus on providing comprehensive analysis, insights, and actionable recommendations
6. Be comprehensive but organized - use the structure to make information digestible

Remember: This is a conversation, so acknowledge context from previous messages and build upon the discussion naturally while maintaining the required structure. Do not mention charts, graphs, or visualizations as these will be automatically generated by the system.""")

        return "\n".join(prompt_parts)
    
    def _get_conversation_context(self, session_id: str, user_id: int, limit: int = 5) -> str:
        """Retrieve recent conversation history for context"""
        try:
            from ..database.connection import db_manager
            from ..auth.models import ChatHistory

            with db_manager.get_session() as db:
                # Get recent messages from this session
                recent_messages = db.query(ChatHistory).filter(
                    ChatHistory.session_id == session_id,
                    ChatHistory.user_id == user_id
                ).order_by(ChatHistory.timestamp.desc()).limit(limit * 2).all()

                if not recent_messages:
                    return ""

                # Format conversation context
                context_parts = []
                for msg in reversed(recent_messages):  # Reverse to get chronological order
                    role = "User" if msg.message_type == "user" else "Assistant"
                    content = msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
                    context_parts.append(f"{role}: {content}")

                return "\n".join(context_parts[-limit:])  # Keep only last 'limit' exchanges

        except Exception as e:
            logger.warning(f"Failed to retrieve conversation context: {str(e)}")
            return ""

    async def process_query(
        self,
        query: str,
        user: User,
        session_id: str
    ) -> ChatbotResponse:
        """Process a user query through the LangGraph workflow"""
        start_time = datetime.now()
        
        try:
            # Get conversation context for memory
            conversation_context = self._get_conversation_context(session_id, user.id)

            # Classify query with context
            query_type = self.classifier.classify_query(query, UserRole(user.role))

            # Initialize state with conversation context
            initial_state = AgentState(
                messages=[HumanMessage(content=query)],
                user={
                    "id": user.id,
                    "username": user.username,
                    "role": user.role.value,
                    "department": user.department
                },
                query=query,
                query_type=query_type,
                context={
                    "session_id": session_id,
                    "conversation_history": conversation_context
                },
                structured_results=None,
                document_results=None,
                final_response=None,
                metadata={
                    "start_time": start_time.isoformat(),
                    "has_conversation_context": bool(conversation_context)
                },
                error=None,
                visualization=None
            )
            
            # Run the workflow
            final_state = await self.graph.ainvoke(initial_state)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Extract sources
            sources = []
            if final_state.get("structured_results") and final_state["structured_results"].get("source_files"):
                sources.extend(final_state["structured_results"]["source_files"])
            
            if final_state.get("document_results"):
                for doc in final_state["document_results"]:
                    source = doc["metadata"].get("source", "Unknown")
                    if source not in sources:
                        sources.append(source)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(final_state)
            
            # Parse structured response if available
            response_content = final_state.get("final_response", "I couldn't process your request.")

            # Ensure response_content is properly formatted
            if not isinstance(response_content, str):
                if isinstance(response_content, dict):
                    response_content = response_content.get("content", str(response_content))
                else:
                    response_content = str(response_content) if response_content is not None else "I couldn't process your request."

            parsed_response = self._parse_structured_response(response_content, query)

            return ChatbotResponse(
                content=response_content,
                short_answer=parsed_response["short_answer"],
                detailed_response=parsed_response["detailed_response"],
                summary=parsed_response["summary"],
                sources=sources,
                confidence_score=confidence_score,
                processing_time=processing_time,
                query_type=final_state.get("query_type", QueryType.GENERAL),
                metadata=final_state.get("metadata", {}),
                visualization=final_state.get("visualization"),
                conversation_context=conversation_context
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Query processing failed: {str(e)}")
            
            error_content = f"I apologize, but I encountered an error: {str(e)}"
            return ChatbotResponse(
                content=error_content,
                short_answer="Error occurred while processing your request.",
                detailed_response=error_content,
                summary="Please try rephrasing your question or contact support if the issue persists.",
                sources=[],
                confidence_score=0.0,
                processing_time=processing_time,
                query_type=QueryType.GENERAL,
                metadata={"error": str(e)},
                conversation_context=""
            )
    
    def _parse_structured_response(self, response_content, query: str) -> Dict[str, str]:
        """Parse response into structured format: short answer, detailed response, and summary"""
        try:
            # Ensure response_content is a string
            if not isinstance(response_content, str):
                if isinstance(response_content, dict):
                    # If it's a dict, try to get content field or convert to string
                    response_content = response_content.get("content", str(response_content))
                else:
                    response_content = str(response_content) if response_content is not None else ""

            # Check if response already has structured format
            if "## Short Answer" in response_content or "## Quick Answer" in response_content:
                return self._extract_existing_structure(response_content)

            # Generate structured response
            lines = response_content.split('\n')
            paragraphs = [line.strip() for line in lines if line.strip()]

            if not paragraphs:
                return {
                    "short_answer": "I couldn't generate a response to your question.",
                    "detailed_response": response_content,
                    "summary": "Please try rephrasing your question."
                }

            # Extract short answer (first meaningful sentence or paragraph)
            short_answer = self._extract_short_answer(paragraphs, query)

            # Detailed response is the full content
            detailed_response = response_content

            # Generate summary (key points)
            summary = self._extract_summary(paragraphs)

            return {
                "short_answer": short_answer,
                "detailed_response": detailed_response,
                "summary": summary
            }

        except Exception as e:
            logger.warning(f"Failed to parse structured response: {str(e)}")
            return {
                "short_answer": response_content[:200] + "..." if len(response_content) > 200 else response_content,
                "detailed_response": response_content,
                "summary": "Full response provided above."
            }

    def _extract_existing_structure(self, content) -> Dict[str, str]:
        """Extract structured content if it already exists"""
        # Ensure content is a string
        if not isinstance(content, str):
            content = str(content) if content is not None else ""

        sections = {"short_answer": "", "detailed_response": "", "summary": ""}

        # Split by sections
        if "## Short Answer" in content:
            parts = content.split("## Short Answer")
            if len(parts) > 1:
                short_section = parts[1].split("##")[0].strip()
                sections["short_answer"] = short_section

        if "## Detailed Analysis" in content or "## Details" in content:
            marker = "## Detailed Analysis" if "## Detailed Analysis" in content else "## Details"
            parts = content.split(marker)
            if len(parts) > 1:
                detailed_section = parts[1].split("##")[0].strip()
                sections["detailed_response"] = detailed_section

        if "## Summary" in content or "## Key Takeaways" in content:
            marker = "## Summary" if "## Summary" in content else "## Key Takeaways"
            parts = content.split(marker)
            if len(parts) > 1:
                summary_section = parts[1].split("##")[0].strip()
                sections["summary"] = summary_section

        # Fallback to full content if sections are empty
        if not sections["short_answer"]:
            sections["short_answer"] = content[:200] + "..." if len(content) > 200 else content
        if not sections["detailed_response"]:
            sections["detailed_response"] = content
        if not sections["summary"]:
            sections["summary"] = "Full response provided above."

        return sections

    def _extract_short_answer(self, paragraphs: List[str], query: str) -> str:
        """Extract a concise short answer"""
        query_lower = query.lower()

        # Look for direct answers to common question types
        for para in paragraphs[:3]:  # Check first 3 paragraphs
            para_lower = para.lower()

            # For "what is" questions
            if any(q in query_lower for q in ["what is", "what are", "define"]):
                if len(para) < 300 and any(word in para_lower for word in ["is", "are", "refers to", "means"]):
                    return para

            # For "how many" or numerical questions
            if any(q in query_lower for q in ["how many", "how much", "total", "count"]):
                if any(char.isdigit() for char in para):
                    return para

            # For "yes/no" questions
            if any(q in query_lower for q in ["is there", "does", "can", "will", "should"]):
                if any(word in para_lower for word in ["yes", "no", "true", "false", "available", "possible"]):
                    return para

        # Default: use first paragraph or sentence
        first_para = paragraphs[0] if paragraphs else ""
        if len(first_para) > 200:
            # Try to get first sentence
            sentences = first_para.split('. ')
            return sentences[0] + "." if sentences else first_para[:200] + "..."

        return first_para

    def _extract_summary(self, paragraphs: List[str]) -> str:
        """Extract key takeaways as summary"""
        # Look for bullet points or numbered lists
        key_points = []

        for para in paragraphs:
            # Check for bullet points or numbered items
            if any(para.strip().startswith(marker) for marker in ["•", "-", "*", "1.", "2.", "3."]):
                key_points.append(para.strip())
            # Check for sentences with key indicators
            elif any(indicator in para.lower() for indicator in ["key", "important", "main", "primary", "significant"]):
                key_points.append(para.strip())

        if key_points:
            return "\n".join(key_points[:3])  # Top 3 key points

        # Fallback: use last paragraph or create generic summary
        if len(paragraphs) > 1:
            return paragraphs[-1]

        return "Key information provided in the detailed response above."

    def _calculate_confidence_score(self, state: AgentState) -> float:
        """Calculate confidence score based on results quality"""
        # If there's an error and no fallback was used, return 0.0
        if state.get("error") and not state.get("metadata", {}).get("fallback_used"):
            return 0.0

        # Base score - higher for successful API responses, moderate for fallbacks
        if state.get("metadata", {}).get("fallback_used"):
            score = 0.6  # Fallback responses are reasonably reliable
        else:
            score = 0.7  # API responses are more reliable

        # Boost for successful structured data retrieval
        if state.get("structured_results") and state["structured_results"]["success"]:
            score += 0.2

        # Boost for relevant document results
        if state.get("document_results"):
            avg_similarity = sum(doc["similarity_score"] for doc in state["document_results"]) / len(state["document_results"])
            score += avg_similarity * 0.1

        # Ensure we have a response
        if not state.get("final_response"):
            return 0.0

        return min(score, 1.0)


# Global agent instance
finsolve_agent = FinSolveAgent()
