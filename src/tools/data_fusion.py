#!/usr/bin/env python3
"""
Data Fusion Tool
Merges text-based RAG results with numerical analysis for comprehensive responses.

Author: Peter Pandey
Version: 1.0.0
"""

from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime
from loguru import logger

from ..rag.vector_store import SearchResult
from .numerical_analyzer import numerical_analyzer, NumericalInsight


@dataclass
class FusedResult:
    """Combined result from text and numerical analysis"""
    text_content: str
    numerical_insights: List[NumericalInsight]
    structured_data: Dict[str, Any]
    confidence_score: float
    sources: List[str]
    fusion_type: str  # 'text_dominant', 'numerical_dominant', 'balanced'


class DataFusionEngine:
    """Engine for fusing text and numerical data insights"""
    
    def __init__(self):
        self.fusion_strategies = {
            'financial': self._fuse_financial_data,
            'hr': self._fuse_hr_data,
            'performance': self._fuse_performance_data,
            'general': self._fuse_general_data
        }
        logger.info("Data fusion engine initialized")
    
    def fuse_results(
        self,
        query: str,
        text_results: List[SearchResult],
        user_role: str,
        query_context: Dict[str, Any] = None
    ) -> FusedResult:
        """Main fusion method that combines text and numerical insights"""
        
        # Determine fusion strategy based on query
        fusion_type = self._determine_fusion_strategy(query)
        
        # Get numerical analysis
        numerical_summary = numerical_analyzer.create_numerical_summary(query, user_role)
        
        # Apply appropriate fusion strategy
        fusion_strategy = self.fusion_strategies.get(fusion_type, self._fuse_general_data)
        
        fused_result = fusion_strategy(
            query=query,
            text_results=text_results,
            numerical_summary=numerical_summary,
            user_role=user_role
        )
        
        return fused_result
    
    def _determine_fusion_strategy(self, query: str) -> str:
        """Determine the best fusion strategy based on query content"""
        query_lower = query.lower()
        
        financial_terms = ['financial', 'revenue', 'profit', 'quarterly', 'expenses', 'performance', 'cash flow']
        hr_terms = ['employees', 'department', 'staff', 'workforce', 'leave', 'benefits']
        performance_terms = ['performance', 'metrics', 'kpi', 'goals', 'targets']
        
        if any(term in query_lower for term in financial_terms):
            return 'financial'
        elif any(term in query_lower for term in hr_terms):
            return 'hr'
        elif any(term in query_lower for term in performance_terms):
            return 'performance'
        else:
            return 'general'
    
    def _fuse_financial_data(
        self,
        query: str,
        text_results: List[SearchResult],
        numerical_summary: Dict[str, Any],
        user_role: str
    ) -> FusedResult:
        """Fuse financial text and numerical data"""
        
        # Extract key numerical insights
        numerical_insights = []
        
        if 'metrics' in numerical_summary:
            metrics = numerical_summary['metrics']
            
            # Create insights for quarterly performance
            for quarter, data in metrics.items():
                if quarter.startswith('Q') and '2024' in quarter:
                    revenue_insight = NumericalInsight(
                        metric_name=f"{quarter} Revenue",
                        value=data.get('revenue', 0),
                        unit=data.get('revenue_unit', 'billion USD'),
                        context=f"Quarterly revenue for {quarter} 2024",
                        trend=f"{data.get('growth', 0)}% YoY growth"
                    )
                    numerical_insights.append(revenue_insight)
        
        # Combine text content with numerical context
        text_content = self._create_financial_narrative(text_results, numerical_summary)
        
        # Calculate confidence based on data availability
        confidence = self._calculate_fusion_confidence(text_results, numerical_summary)
        
        # Extract sources
        sources = [result.document.metadata.get('source', 'Unknown') for result in text_results]
        sources.append('Financial Analysis Engine')
        
        return FusedResult(
            text_content=text_content,
            numerical_insights=numerical_insights,
            structured_data=numerical_summary.get('metrics', {}),
            confidence_score=confidence,
            sources=list(set(sources)),
            fusion_type='numerical_dominant'
        )
    
    def _fuse_hr_data(
        self,
        query: str,
        text_results: List[SearchResult],
        numerical_summary: Dict[str, Any],
        user_role: str
    ) -> FusedResult:
        """Fuse HR text and numerical data"""
        
        numerical_insights = []
        
        if 'metrics' in numerical_summary:
            metrics = numerical_summary['metrics']
            
            # Employee count insights
            if 'departments' in metrics:
                for dept, count in metrics['departments'].items():
                    insight = NumericalInsight(
                        metric_name=f"{dept.title()} Department",
                        value=count,
                        unit="employees",
                        context=f"Current staffing in {dept} department"
                    )
                    numerical_insights.append(insight)
        
        # Create HR narrative
        text_content = self._create_hr_narrative(text_results, numerical_summary)
        
        confidence = self._calculate_fusion_confidence(text_results, numerical_summary)
        sources = [result.document.metadata.get('source', 'Unknown') for result in text_results]
        sources.append('HR Analytics Engine')
        
        return FusedResult(
            text_content=text_content,
            numerical_insights=numerical_insights,
            structured_data=numerical_summary.get('metrics', {}),
            confidence_score=confidence,
            sources=list(set(sources)),
            fusion_type='balanced'
        )
    
    def _fuse_performance_data(
        self,
        query: str,
        text_results: List[SearchResult],
        numerical_summary: Dict[str, Any],
        user_role: str
    ) -> FusedResult:
        """Fuse performance text and numerical data"""
        
        # Create performance-focused narrative
        text_content = self._create_performance_narrative(text_results, numerical_summary)
        
        numerical_insights = []
        confidence = self._calculate_fusion_confidence(text_results, numerical_summary)
        sources = [result.document.metadata.get('source', 'Unknown') for result in text_results]
        
        return FusedResult(
            text_content=text_content,
            numerical_insights=numerical_insights,
            structured_data=numerical_summary.get('metrics', {}),
            confidence_score=confidence,
            sources=list(set(sources)),
            fusion_type='text_dominant'
        )
    
    def _fuse_general_data(
        self,
        query: str,
        text_results: List[SearchResult],
        numerical_summary: Dict[str, Any],
        user_role: str
    ) -> FusedResult:
        """Fuse general text and numerical data"""
        
        # Create general narrative
        text_content = self._create_general_narrative(text_results, numerical_summary)
        
        numerical_insights = []
        confidence = self._calculate_fusion_confidence(text_results, numerical_summary)
        sources = [result.document.metadata.get('source', 'Unknown') for result in text_results]
        
        return FusedResult(
            text_content=text_content,
            numerical_insights=numerical_insights,
            structured_data=numerical_summary.get('metrics', {}),
            confidence_score=confidence,
            sources=list(set(sources)),
            fusion_type='text_dominant'
        )
    
    def _create_financial_narrative(
        self,
        text_results: List[SearchResult],
        numerical_summary: Dict[str, Any]
    ) -> str:
        """Create comprehensive financial narrative"""
        
        narrative_parts = []
        
        # Add numerical insights first
        if 'metrics' in numerical_summary:
            narrative_parts.append("**FinSolve Technologies Financial Performance Analysis**\n")
            
            metrics = numerical_summary['metrics']
            
            # Quarterly breakdown
            if any(key.startswith('Q') for key in metrics.keys()):
                narrative_parts.append("**Quarterly Performance:**")
                for quarter in ['Q1_2024', 'Q2_2024', 'Q3_2024', 'Q4_2024']:
                    if quarter in metrics:
                        data = metrics[quarter]
                        narrative_parts.append(
                            f"• **{quarter}**: ${data.get('revenue', 0):.1f}B revenue "
                            f"({data.get('growth', 0)}% YoY growth, {data.get('margin', 0)}% gross margin)"
                        )
            
            # Annual summary
            if 'annual_2024' in metrics:
                annual = metrics['annual_2024']
                narrative_parts.append(f"\n**Annual 2024 Summary:**")
                narrative_parts.append(f"• Total Revenue: ${annual.get('total_revenue', 0):.1f}B ({annual.get('growth', 0)}% YoY growth)")
                narrative_parts.append(f"• Net Income: ${annual.get('net_income', 0):.2f}B")
        
        # Add insights from numerical analysis
        if 'insights' in numerical_summary:
            narrative_parts.append("\n**Key Financial Insights:**")
            for insight in numerical_summary['insights']:
                narrative_parts.append(f"• {insight}")
        
        # Add trends analysis
        if 'trends' in numerical_summary:
            narrative_parts.append("\n**Performance Trends:**")
            for trend_name, trend_desc in numerical_summary['trends'].items():
                narrative_parts.append(f"• {trend_desc}")
        
        # Add relevant text content if available
        if text_results:
            narrative_parts.append("\n**Additional Context:**")
            for result in text_results[:2]:  # Top 2 text results
                content_snippet = result.document.content[:200] + "..." if len(result.document.content) > 200 else result.document.content
                narrative_parts.append(f"• {content_snippet}")
        
        return "\n".join(narrative_parts)
    
    def _create_hr_narrative(
        self,
        text_results: List[SearchResult],
        numerical_summary: Dict[str, Any]
    ) -> str:
        """Create comprehensive HR narrative"""
        
        narrative_parts = []
        
        if 'metrics' in numerical_summary:
            metrics = numerical_summary['metrics']
            
            narrative_parts.append("**FinSolve Technologies Workforce Analysis**\n")
            
            # Employee distribution
            if 'departments' in metrics:
                total_employees = sum(metrics['departments'].values())
                narrative_parts.append(f"**Total Workforce: {total_employees} employees**\n")
                narrative_parts.append("**Department Distribution:**")
                
                # Sort departments by employee count
                sorted_depts = sorted(metrics['departments'].items(), key=lambda x: x[1], reverse=True)
                for dept, count in sorted_depts:
                    percentage = (count / total_employees) * 100
                    narrative_parts.append(f"• {dept.title()}: {count} employees ({percentage:.1f}%)")
        
        # Add text content for policies
        if text_results:
            narrative_parts.append("\n**HR Policies & Information:**")
            for result in text_results[:3]:
                content_snippet = result.document.content[:150] + "..." if len(result.document.content) > 150 else result.document.content
                narrative_parts.append(f"• {content_snippet}")
        
        return "\n".join(narrative_parts)
    
    def _create_performance_narrative(
        self,
        text_results: List[SearchResult],
        numerical_summary: Dict[str, Any]
    ) -> str:
        """Create performance-focused narrative"""
        
        narrative_parts = ["**Performance Metrics Overview**\n"]
        
        # Add text-based performance information
        if text_results:
            for result in text_results:
                narrative_parts.append(f"• {result.document.content[:200]}...")
        
        return "\n".join(narrative_parts)
    
    def _create_general_narrative(
        self,
        text_results: List[SearchResult],
        numerical_summary: Dict[str, Any]
    ) -> str:
        """Create general narrative"""
        
        narrative_parts = []
        
        if text_results:
            for result in text_results:
                narrative_parts.append(result.document.content)
        
        return "\n\n".join(narrative_parts)
    
    def _calculate_fusion_confidence(
        self,
        text_results: List[SearchResult],
        numerical_summary: Dict[str, Any]
    ) -> float:
        """Calculate confidence score for fused results"""
        
        base_confidence = 0.6
        
        # Boost for text results
        if text_results:
            avg_text_confidence = sum(result.similarity_score for result in text_results) / len(text_results)
            base_confidence += avg_text_confidence * 0.2
        
        # Boost for numerical data availability
        if numerical_summary.get('metrics'):
            base_confidence += 0.15
        
        if numerical_summary.get('insights'):
            base_confidence += 0.1
        
        return min(base_confidence, 1.0)


# Global data fusion engine instance
data_fusion_engine = DataFusionEngine()
