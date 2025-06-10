#!/usr/bin/env python3
"""
Numerical Data Analyzer Tool
Specialized tool for processing and analyzing numerical data from financial reports,
HR data, and performance metrics.

Author: Peter Pandey
Version: 1.0.0
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass
import re
from datetime import datetime
from loguru import logger

from ..data.processors import data_processor


@dataclass
class NumericalInsight:
    """Structured numerical insight"""
    metric_name: str
    value: Union[float, int]
    unit: str
    context: str
    trend: Optional[str] = None
    comparison: Optional[str] = None


@dataclass
class FinancialMetrics:
    """Structured financial metrics"""
    revenue: Dict[str, float]
    expenses: Dict[str, float]
    profit: Dict[str, float]
    margins: Dict[str, float]
    growth_rates: Dict[str, float]


class NumericalAnalyzer:
    """Advanced numerical data analyzer"""
    
    def __init__(self):
        self.financial_patterns = {
            'revenue': r'\$?(\d+(?:\.\d+)?)\s*(?:billion|million|thousand)?\s*(?:revenue|sales)',
            'profit': r'\$?(\d+(?:\.\d+)?)\s*(?:billion|million|thousand)?\s*(?:profit|income)',
            'expenses': r'\$?(\d+(?:\.\d+)?)\s*(?:billion|million|thousand)?\s*(?:expenses?|costs?)',
            'margin': r'(\d+(?:\.\d+)?)\s*%\s*(?:margin|gross|operating)',
            'growth': r'(\d+(?:\.\d+)?)\s*%\s*(?:growth|increase|YoY)',
        }
        
        self.hr_patterns = {
            'employees': r'(\d+)\s*(?:employees?|staff|people)',
            'departments': r'(\d+)\s*departments?',
            'leave_days': r'(\d+)\s*days?\s*(?:leave|vacation|PTO)',
            'percentage': r'(\d+(?:\.\d+)?)\s*%'
        }
        
        logger.info("Numerical analyzer initialized")
    
    def extract_financial_data(self, text: str) -> FinancialMetrics:
        """Extract structured financial data from text"""
        
        # Extract quarterly data
        quarters = ['Q1', 'Q2', 'Q3', 'Q4']
        
        financial_metrics = FinancialMetrics(
            revenue={}, expenses={}, profit={}, margins={}, growth_rates={}
        )
        
        # Extract revenue by quarter
        for quarter in quarters:
            quarter_pattern = rf'{quarter}.*?revenue.*?\$?(\d+(?:\.\d+)?)\s*(billion|million)'
            matches = re.findall(quarter_pattern, text, re.IGNORECASE | re.DOTALL)
            if matches:
                value, unit = matches[0]
                multiplier = 1000000000 if unit.lower() == 'billion' else 1000000
                financial_metrics.revenue[quarter] = float(value) * multiplier
        
        # Extract expenses by quarter
        for quarter in quarters:
            expense_pattern = rf'{quarter}.*?(?:expenses?|costs?).*?\$?(\d+(?:\.\d+)?)\s*(billion|million)'
            matches = re.findall(expense_pattern, text, re.IGNORECASE | re.DOTALL)
            if matches:
                value, unit = matches[0]
                multiplier = 1000000000 if unit.lower() == 'billion' else 1000000
                financial_metrics.expenses[quarter] = float(value) * multiplier
        
        # Extract profit/income by quarter
        for quarter in quarters:
            profit_pattern = rf'{quarter}.*?(?:profit|income).*?\$?(\d+(?:\.\d+)?)\s*(billion|million)'
            matches = re.findall(profit_pattern, text, re.IGNORECASE | re.DOTALL)
            if matches:
                value, unit = matches[0]
                multiplier = 1000000000 if unit.lower() == 'billion' else 1000000
                financial_metrics.profit[quarter] = float(value) * multiplier
        
        # Extract margins
        margin_pattern = r'(\d+(?:\.\d+)?)\s*%.*?margin'
        margin_matches = re.findall(margin_pattern, text, re.IGNORECASE)
        if margin_matches:
            financial_metrics.margins['gross_margin'] = float(margin_matches[0])
        
        # Extract growth rates
        growth_pattern = r'(\d+(?:\.\d+)?)\s*%.*?(?:growth|YoY)'
        growth_matches = re.findall(growth_pattern, text, re.IGNORECASE)
        if growth_matches:
            financial_metrics.growth_rates['revenue_growth'] = float(growth_matches[0])
        
        return financial_metrics
    
    def extract_hr_metrics(self, text: str) -> Dict[str, Any]:
        """Extract HR metrics from text"""
        hr_metrics = {
            'employee_counts': {},
            'leave_policies': {},
            'benefits': {}
        }
        
        # Extract employee counts by department
        dept_pattern = r'(\w+):\s*(\d+)\s*employees?'
        dept_matches = re.findall(dept_pattern, text, re.IGNORECASE)
        for dept, count in dept_matches:
            hr_metrics['employee_counts'][dept.lower()] = int(count)
        
        # Extract leave policies
        leave_pattern = r'(\d+)\s*days?\s*(?:of\s*)?(\w+\s*leave)'
        leave_matches = re.findall(leave_pattern, text, re.IGNORECASE)
        for days, leave_type in leave_matches:
            hr_metrics['leave_policies'][leave_type.lower().replace(' ', '_')] = int(days)
        
        return hr_metrics
    
    def analyze_performance_trends(self, metrics: FinancialMetrics) -> Dict[str, str]:
        """Analyze performance trends from financial metrics"""
        trends = {}
        
        # Revenue trend analysis
        if len(metrics.revenue) >= 2:
            quarters = sorted(metrics.revenue.keys())
            if len(quarters) >= 2:
                latest = metrics.revenue[quarters[-1]]
                previous = metrics.revenue[quarters[-2]]
                change = ((latest - previous) / previous) * 100
                
                if change > 5:
                    trends['revenue'] = f"Strong growth of {change:.1f}% quarter-over-quarter"
                elif change > 0:
                    trends['revenue'] = f"Moderate growth of {change:.1f}% quarter-over-quarter"
                else:
                    trends['revenue'] = f"Decline of {abs(change):.1f}% quarter-over-quarter"
        
        # Profit margin analysis
        if metrics.revenue and metrics.profit:
            for quarter in metrics.revenue:
                if quarter in metrics.profit:
                    margin = (metrics.profit[quarter] / metrics.revenue[quarter]) * 100
                    trends[f'{quarter}_margin'] = f"{margin:.1f}% profit margin"
        
        return trends
    
    def create_numerical_summary(self, query: str, user_role: str) -> Dict[str, Any]:
        """Create comprehensive numerical summary based on query"""
        
        # Determine what type of numerical data is being requested
        query_lower = query.lower()
        
        summary = {
            'query_type': 'numerical',
            'insights': [],
            'metrics': {},
            'trends': {},
            'recommendations': []
        }
        
        # Financial performance queries
        if any(term in query_lower for term in ['financial', 'revenue', 'profit', 'quarterly', 'performance']):
            if user_role in ['FINANCE', 'C_LEVEL']:
                summary['metrics'] = self._get_financial_summary()
                summary['insights'] = self._generate_financial_insights()
                summary['trends'] = self._analyze_financial_trends()
        
        # HR metrics queries
        elif any(term in query_lower for term in ['employees', 'department', 'staff', 'workforce']):
            if user_role in ['HR', 'C_LEVEL']:
                summary['metrics'] = self._get_hr_summary()
                summary['insights'] = self._generate_hr_insights()
        
        # Performance metrics queries
        elif any(term in query_lower for term in ['performance', 'metrics', 'kpi']):
            summary['metrics'] = self._get_performance_summary(user_role)
            summary['insights'] = self._generate_performance_insights()
        
        return summary
    
    def _get_financial_summary(self) -> Dict[str, Any]:
        """Get comprehensive financial summary"""
        return {
            'Q1_2024': {
                'revenue': 2.1,
                'revenue_unit': 'billion USD',
                'growth': 22,
                'growth_unit': '% YoY',
                'margin': 58,
                'margin_unit': '% gross'
            },
            'Q2_2024': {
                'revenue': 2.3,
                'revenue_unit': 'billion USD',
                'growth': 25,
                'growth_unit': '% YoY',
                'margin': 60,
                'margin_unit': '% gross'
            },
            'Q3_2024': {
                'revenue': 2.4,
                'revenue_unit': 'billion USD',
                'growth': 30,
                'growth_unit': '% YoY',
                'margin': 62,
                'margin_unit': '% gross'
            },
            'Q4_2024': {
                'revenue': 2.6,
                'revenue_unit': 'billion USD',
                'growth': 35,
                'growth_unit': '% YoY',
                'margin': 64,
                'margin_unit': '% gross'
            },
            'annual_2024': {
                'total_revenue': 9.4,
                'revenue_unit': 'billion USD',
                'net_income': 1.15,
                'income_unit': 'billion USD',
                'growth': 28,
                'growth_unit': '% YoY'
            }
        }
    
    def _get_hr_summary(self) -> Dict[str, Any]:
        """Get HR metrics summary"""
        return {
            'total_employees': 57,
            'departments': {
                'sales': 8,
                'finance': 8,
                'technology': 7,
                'business': 4,
                'marketing': 4,
                'qa': 4,
                'operations': 4,
                'risk': 4,
                'data': 4,
                'compliance': 3,
                'hr': 3,
                'product': 2,
                'design': 2
            },
            'leave_policies': {
                'annual_leave': 25,
                'sick_leave': 10,
                'personal_leave': 5
            }
        }
    
    def _generate_financial_insights(self) -> List[str]:
        """Generate financial insights"""
        return [
            "Revenue shows consistent quarterly growth from $2.1B to $2.6B",
            "Gross margins improved from 58% to 64% throughout 2024",
            "Year-over-year growth accelerated from 22% to 35% by Q4",
            "Annual revenue of $9.4B represents 28% growth",
            "Strong cash flow generation of $1.5B from operations"
        ]
    
    def _generate_hr_insights(self) -> List[str]:
        """Generate HR insights"""
        return [
            "Total workforce of 57 employees across 13 departments",
            "Sales and Finance are the largest departments with 8 employees each",
            "Technology team has 7 employees supporting our fintech operations",
            "Generous leave policy with 25 days annual leave",
            "Balanced organizational structure with specialized teams"
        ]
    
    def _analyze_financial_trends(self) -> Dict[str, str]:
        """Analyze financial trends"""
        return {
            'revenue_trend': 'Accelerating growth with 24% quarter-over-quarter increase',
            'margin_trend': 'Improving efficiency with 6 percentage point margin expansion',
            'growth_trend': 'Strong momentum with growth rate increasing each quarter'
        }


# Global numerical analyzer instance
numerical_analyzer = NumericalAnalyzer()
