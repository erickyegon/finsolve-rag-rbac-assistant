"""
FinSolve AI Assistant - Enhanced Professional Streamlit Interface
Ultra-modern, responsive chat interface with advanced UI/UX design,
real-time messaging, role-based access, and enterprise-grade features.

Author: Enhanced by AI for FinSolve
Version: 2.0.0
Features: Improved brand consistency, enhanced UX, optimized performance
"""

import streamlit as st
import requests
import json
import time
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import uuid
import base64
from io import BytesIO
import html
import re
from loguru import logger
from pathlib import Path

# Email service import
try:
    import sys
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    from src.utils.email_service import email_service
except ImportError:
    email_service = None
    logger.warning("Email service not available - inquiry emails will be disabled")

# ============================
# CONFIGURATION & CONSTANTS
# ============================

# Page configuration
st.set_page_config(
    page_title="FinSolve AI Assistant",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://finsolve.com/support',
        'Report a bug': 'https://finsolve.com/bugs',
        'About': "FinSolve AI Assistant - Your intelligent business companion"
    }
)

# API Configuration
API_CONFIG = {
    "base_url": "http://localhost:8000",
    "timeout": 30,
    "retry_attempts": 3
}

# FinSolve Brand Constants
FINSOLVE_BRAND = {
    "colors": {
        "deep_blue": "#0D1B2A",
        "teal": "#00F5D4",
        "white": "#FFFFFF",
        "grey": "#A9A9A9",
        "light_grey": "#F8F9FA",
        "dark_grey": "#666666",
        "success": "#4CAF50",
        "warning": "#FF9800",
        "error": "#F44336",
        "info": "#2196F3"
    },
    "fonts": {
        "primary": "'Poppins', sans-serif",
        "secondary": "'Roboto', sans-serif"
    },
    "gradients": {
        "primary": "linear-gradient(135deg, #0D1B2A 0%, #1a2332 100%)",
        "secondary": "linear-gradient(135deg, #00F5D4 0%, #00d4b8 100%)",
        "background": "linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%)"
    }
}

# Role Configuration
ROLE_CONFIG = {
    "c_level": {"icon": "👑", "color": FINSOLVE_BRAND["colors"]["teal"], "priority": 1},
    "hr": {"icon": "👥", "color": FINSOLVE_BRAND["colors"]["deep_blue"], "priority": 2},
    "finance": {"icon": "💰", "color": FINSOLVE_BRAND["colors"]["teal"], "priority": 2},
    "marketing": {"icon": "📈", "color": FINSOLVE_BRAND["colors"]["grey"], "priority": 3},
    "engineering": {"icon": "⚙️", "color": FINSOLVE_BRAND["colors"]["teal"], "priority": 2},
    "employee": {"icon": "👤", "color": FINSOLVE_BRAND["colors"]["grey"], "priority": 4}
}

# ============================
# ENHANCED CSS STYLING
# ============================

def get_enhanced_css() -> str:
    """Generate enhanced CSS with improved brand consistency and accessibility."""
    return f"""
    <style>
        /* Import Brand Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&family=Roboto:wght@300;400;500;700&display=swap');

        /* CSS Custom Properties for Brand Consistency */
        :root {{
            --finsolve-deep-blue: {FINSOLVE_BRAND["colors"]["deep_blue"]};
            --finsolve-teal: {FINSOLVE_BRAND["colors"]["teal"]};
            --finsolve-white: {FINSOLVE_BRAND["colors"]["white"]};
            --finsolve-grey: {FINSOLVE_BRAND["colors"]["grey"]};
            --finsolve-light-grey: {FINSOLVE_BRAND["colors"]["light_grey"]};
            --finsolve-dark-grey: {FINSOLVE_BRAND["colors"]["dark_grey"]};
            --finsolve-success: {FINSOLVE_BRAND["colors"]["success"]};
            --finsolve-warning: {FINSOLVE_BRAND["colors"]["warning"]};
            --finsolve-error: {FINSOLVE_BRAND["colors"]["error"]};
            --finsolve-info: {FINSOLVE_BRAND["colors"]["info"]};
            
            --font-primary: {FINSOLVE_BRAND["fonts"]["primary"]};
            --font-secondary: {FINSOLVE_BRAND["fonts"]["secondary"]};
            
            --gradient-primary: {FINSOLVE_BRAND["gradients"]["primary"]};
            --gradient-secondary: {FINSOLVE_BRAND["gradients"]["secondary"]};
            --gradient-background: {FINSOLVE_BRAND["gradients"]["background"]};
            
            --shadow-light: 0 4px 15px rgba(0, 0, 0, 0.08);
            --shadow-medium: 0 8px 32px rgba(0, 0, 0, 0.12);
            --shadow-heavy: 0 12px 40px rgba(0, 0, 0, 0.15);
            --shadow-brand: 0 8px 32px rgba(0, 245, 212, 0.2);
            
            --border-radius-small: 8px;
            --border-radius-medium: 12px;
            --border-radius-large: 16px;
            --border-radius-xl: 20px;
            
            --transition-fast: 0.2s ease;
            --transition-normal: 0.3s ease;
            --transition-slow: 0.5s ease;
        }}

        /* Global Reset and Base Styles */
        * {{
            box-sizing: border-box;
        }}

        .stApp {{
            font-family: var(--font-secondary);
            background: var(--gradient-background);
            color: var(--finsolve-deep-blue);
            font-size: 16px;
            line-height: 1.6;
        }}

        /* Remove Streamlit Branding */
        #MainMenu, footer, header, .stDeployButton {{
            visibility: hidden !important;
            display: none !important;
        }}

        /* Layout Optimization */
        .main > div {{
            padding-top: 0 !important;
            padding-bottom: 0 !important;
        }}

        .main .block-container {{
            padding-top: 1rem !important;
            padding-bottom: 1rem !important;
            margin-top: 0 !important;
            max-width: 1400px;
            padding-left: 1rem;
            padding-right: 1rem;
        }}

        header[data-testid="stHeader"] {{
            height: 0 !important;
            display: none !important;
        }}

        div[data-testid="stToolbar"] {{
            display: none !important;
        }}

        /* Enhanced Header Component */
        .finsolve-header {{
            background: var(--gradient-primary);
            padding: 2rem 2.5rem;
            border-radius: var(--border-radius-xl);
            color: var(--finsolve-white);
            margin-bottom: 2rem;
            box-shadow: var(--shadow-brand);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(0, 245, 212, 0.3);
            position: relative;
            overflow: hidden;
        }}

        .finsolve-header::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: var(--gradient-secondary);
            border-radius: var(--border-radius-xl) var(--border-radius-xl) 0 0;
        }}

        .finsolve-header::after {{
            content: '';
            position: absolute;
            top: -50%;
            right: -20%;
            width: 200px;
            height: 200px;
            background: radial-gradient(circle, rgba(0, 245, 212, 0.1) 0%, transparent 70%);
            border-radius: 50%;
        }}

        .header-logo {{
            background: var(--finsolve-white);
            width: 70px;
            height: 70px;
            border-radius: var(--border-radius-large);
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: var(--shadow-medium);
            padding: 8px;
            transition: var(--transition-normal);
        }}

        .header-logo:hover {{
            transform: scale(1.05);
        }}

        .header-title {{
            font-family: var(--font-primary);
            font-size: 2.4rem;
            font-weight: 800;
            color: var(--finsolve-white);
            margin: 0;
            letter-spacing: -1px;
            line-height: 1;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }}

        .header-subtitle {{
            font-size: 1.1rem;
            color: var(--finsolve-teal);
            margin: 0;
            font-weight: 600;
            letter-spacing: 0.5px;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
        }}

        /* Enhanced Chat Container */
        .chat-container {{
            background: rgba(255, 255, 255, 0.98);
            border-radius: var(--border-radius-xl);
            padding: 2rem;
            margin: 1rem 0;
            box-shadow: var(--shadow-medium);
            backdrop-filter: blur(10px);
            border: 2px solid rgba(0, 245, 212, 0.2);
            min-height: 500px;
            max-height: 600px;
            overflow-y: auto;
            scroll-behavior: smooth;
        }}

        .chat-container::-webkit-scrollbar {{
            width: 8px;
        }}

        .chat-container::-webkit-scrollbar-track {{
            background: rgba(0, 0, 0, 0.05);
            border-radius: 10px;
        }}

        .chat-container::-webkit-scrollbar-thumb {{
            background: var(--gradient-secondary);
            border-radius: 10px;
            transition: var(--transition-normal);
        }}

        .chat-container::-webkit-scrollbar-thumb:hover {{
            background: var(--finsolve-teal);
        }}

        /* Enhanced Message Styles */
        .chat-message {{
            margin: 1rem 0;
            animation: slideInFromBottom 0.4s ease-out;
            opacity: 0;
            animation-fill-mode: forwards;
        }}

        @keyframes slideInFromBottom {{
            from {{
                opacity: 0;
                transform: translateY(20px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        .user-message {{
            background: var(--gradient-primary);
            color: var(--finsolve-white);
            padding: 1rem 1.5rem;
            border-radius: var(--border-radius-large) var(--border-radius-large) var(--border-radius-small) var(--border-radius-large);
            margin-left: 15%;
            box-shadow: var(--shadow-light);
            border-left: 4px solid var(--finsolve-teal);
            position: relative;
        }}

        .assistant-message {{
            background: linear-gradient(135deg, var(--finsolve-white) 0%, var(--finsolve-light-grey) 100%);
            color: var(--finsolve-deep-blue);
            padding: 1rem 1.5rem;
            border-radius: var(--border-radius-large) var(--border-radius-large) var(--border-radius-large) var(--border-radius-small);
            margin-right: 15%;
            box-shadow: var(--shadow-light);
            border-left: 4px solid var(--finsolve-teal);
            border: 2px solid rgba(0, 245, 212, 0.2);
            position: relative;
        }}

        .message-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.5rem;
            font-size: 0.9rem;
            font-weight: 600;
        }}

        .message-content {{
            line-height: 1.6;
            font-size: 1rem;
        }}

        .confidence-badge {{
            background: var(--finsolve-success);
            color: var(--finsolve-white);
            padding: 0.2rem 0.6rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);
        }}

        .confidence-medium {{
            background: var(--finsolve-warning);
        }}

        .confidence-low {{
            background: var(--finsolve-error);
        }}

        /* Enhanced Cards and Components */
        .finsolve-card {{
            background: rgba(255, 255, 255, 0.95);
            padding: 1.5rem;
            border-radius: var(--border-radius-large);
            box-shadow: var(--shadow-light);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: var(--transition-normal);
        }}

        .finsolve-card:hover {{
            transform: translateY(-2px);
            box-shadow: var(--shadow-medium);
        }}

        .metric-card {{
            background: var(--finsolve-white);
            padding: 1.5rem;
            border-radius: var(--border-radius-medium);
            text-align: center;
            box-shadow: var(--shadow-light);
            border: 2px solid transparent;
            transition: var(--transition-normal);
            cursor: pointer;
        }}

        .metric-card:hover {{
            transform: translateY(-3px);
            box-shadow: var(--shadow-medium);
            border-color: var(--finsolve-teal);
        }}

        .metric-value {{
            font-size: 2rem;
            font-weight: 800;
            color: var(--finsolve-deep-blue);
            margin-bottom: 0.5rem;
            font-family: var(--font-primary);
        }}

        .metric-label {{
            font-size: 0.9rem;
            color: var(--finsolve-dark-grey);
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        /* Enhanced Button Styles */
        .stButton > button {{
            background: var(--gradient-secondary) !important;
            color: var(--finsolve-deep-blue) !important;
            border: none !important;
            border-radius: 25px !important;
            padding: 0.7rem 1.8rem !important;
            font-weight: 600 !important;
            font-family: var(--font-primary) !important;
            transition: var(--transition-normal) !important;
            box-shadow: var(--shadow-light) !important;
            text-transform: none !important;
            font-size: 0.95rem !important;
        }}

        .stButton > button:hover {{
            transform: translateY(-2px) !important;
            box-shadow: var(--shadow-medium) !important;
            background: linear-gradient(135deg, rgba(0, 245, 212, 0.9) 0%, var(--finsolve-teal) 100%) !important;
        }}

        .stButton > button:active {{
            transform: translateY(0) !important;
        }}

        /* Enhanced Form Inputs */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea {{
            border-radius: var(--border-radius-medium) !important;
            border: 2px solid rgba(0, 245, 212, 0.3) !important;
            padding: 0.8rem 1.2rem !important;
            font-size: 1rem !important;
            transition: var(--transition-normal) !important;
            background: rgba(255, 255, 255, 0.9) !important;
            font-family: var(--font-secondary) !important;
        }}

        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {{
            border-color: var(--finsolve-teal) !important;
            box-shadow: 0 0 20px rgba(0, 245, 212, 0.3) !important;
            background: var(--finsolve-white) !important;
        }}

        /* Login Container */
        .login-container {{
            background: rgba(255, 255, 255, 0.98);
            padding: 3rem;
            border-radius: var(--border-radius-xl);
            box-shadow: var(--shadow-heavy);
            backdrop-filter: blur(15px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            max-width: 600px;
            margin: 2rem auto;
        }}

        /* Status Indicators */
        .status-indicator {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.4rem 0.8rem;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
        }}

        .status-online {{
            background: rgba(76, 175, 80, 0.1);
            color: var(--finsolve-success);
            border: 1px solid var(--finsolve-success);
        }}

        .status-processing {{
            background: rgba(255, 152, 0, 0.1);
            color: var(--finsolve-warning);
            border: 1px solid var(--finsolve-warning);
        }}

        .status-offline {{
            background: rgba(244, 67, 54, 0.1);
            color: var(--finsolve-error);
            border: 1px solid var(--finsolve-error);
        }}

        /* Enhanced Welcome Message */
        .welcome-container {{
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.98) 0%, rgba(248, 249, 250, 0.95) 100%);
            padding: 3rem 2rem;
            border-radius: var(--border-radius-xl);
            margin: 0 0 2rem 0;
            border: 3px solid rgba(0, 245, 212, 0.3);
            text-align: center;
            box-shadow: var(--shadow-brand);
            position: relative;
            overflow: hidden;
        }}

        .welcome-container::before {{
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(0, 245, 212, 0.05) 0%, transparent 70%);
            animation: pulse 4s ease-in-out infinite;
        }}

        @keyframes pulse {{
            0%, 100% {{ transform: scale(1); opacity: 0.5; }}
            50% {{ transform: scale(1.1); opacity: 0.8; }}
        }}

        .welcome-emoji {{
            font-size: 4rem;
            margin-bottom: 1.5rem;
            animation: bounce 2s ease-in-out infinite;
        }}

        @keyframes bounce {{
            0%, 20%, 50%, 80%, 100% {{ transform: translateY(0); }}
            40% {{ transform: translateY(-10px); }}
            60% {{ transform: translateY(-5px); }}
        }}

        .welcome-title {{
            color: var(--finsolve-deep-blue);
            margin-bottom: 1rem;
            font-size: 2.5rem;
            font-weight: 800;
            font-family: var(--font-primary);
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.1);
        }}

        .welcome-description {{
            color: var(--finsolve-dark-grey);
            margin-bottom: 2rem;
            font-size: 1.2rem;
            line-height: 1.6;
            font-weight: 500;
        }}

        .feature-tag {{
            background: var(--gradient-secondary);
            padding: 0.8rem 1.5rem;
            border-radius: 25px;
            box-shadow: var(--shadow-light);
            display: inline-block;
            margin: 0.5rem;
            transition: var(--transition-normal);
        }}

        .feature-tag:hover {{
            transform: translateY(-2px);
            box-shadow: var(--shadow-medium);
        }}

        .feature-tag span {{
            color: var(--finsolve-white);
            font-weight: 700;
            font-size: 1rem;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);
        }}

        /* Input Enhancement */
        .input-container {{
            background: linear-gradient(135deg, rgba(0, 245, 212, 0.05) 0%, rgba(13, 27, 42, 0.02) 100%);
            padding: 2rem;
            border-radius: var(--border-radius-large);
            margin-top: 2rem;
            border: 2px solid rgba(0, 245, 212, 0.2);
            box-shadow: var(--shadow-light);
        }}

        .input-label {{
            font-size: 1.2rem;
            font-weight: 600;
            color: var(--finsolve-deep-blue);
            margin-bottom: 1rem;
            display: block;
            font-family: var(--font-primary);
        }}

        /* Sidebar Enhancement */
        .css-1d391kg {{
            background: rgba(255, 255, 255, 0.98) !important;
            backdrop-filter: blur(10px) !important;
            border-right: 2px solid rgba(0, 245, 212, 0.2) !important;
        }}

        .sidebar-section {{
            background: var(--finsolve-card);
            padding: 1.5rem;
            border-radius: var(--border-radius-medium);
            margin: 1rem 0;
            box-shadow: var(--shadow-light);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }}

        /* Loading Animation */
        .loading-container {{
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 2rem;
        }}

        .loading-spinner {{
            width: 40px;
            height: 40px;
            border: 4px solid rgba(0, 245, 212, 0.2);
            border-left: 4px solid var(--finsolve-teal);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }}

        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}

        /* Responsive Design */
        @media (max-width: 768px) {{
            .finsolve-header {{
                padding: 1.5rem;
            }}
            
            .header-title {{
                font-size: 1.8rem;
            }}
            
            .user-message {{
                margin-left: 5%;
            }}
            
            .assistant-message {{
                margin-right: 5%;
            }}
            
            .login-container {{
                margin: 1rem;
                padding: 2rem;
            }}
            
            .welcome-title {{
                font-size: 2rem;
            }}
        }}

        /* Accessibility Improvements */
        .sr-only {{
            position: absolute;
            width: 1px;
            height: 1px;
            padding: 0;
            margin: -1px;
            overflow: hidden;
            clip: rect(0, 0, 0, 0);
            white-space: nowrap;
            border: 0;
        }}

        /* Focus States */
        button:focus,
        input:focus,
        textarea:focus {{
            outline: 2px solid var(--finsolve-teal) !important;
            outline-offset: 2px !important;
        }}

        /* High Contrast Mode Support */
        @media (prefers-contrast: high) {{
            :root {{
                --finsolve-teal: #00D4AA;
                --finsolve-deep-blue: #000000;
            }}
        }}

        /* Reduced Motion Support */
        @media (prefers-reduced-motion: reduce) {{
            * {{
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }}
        }}
    </style>
    """

# ============================
# UTILITY CLASSES
# ============================

class APIClient:
    """Enhanced API client with retry logic and error handling."""
    
    def __init__(self):
        self.base_url = API_CONFIG["base_url"]
        self.timeout = API_CONFIG["timeout"]
        self.retry_attempts = API_CONFIG["retry_attempts"]
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[requests.Response]:
        """Make HTTP request with retry logic."""
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(self.retry_attempts):
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    timeout=self.timeout,
                    **kwargs
                )
                return response
            except requests.exceptions.RequestException as e:
                if attempt == self.retry_attempts - 1:
                    logger.error(f"API request failed after {self.retry_attempts} attempts: {e}")
                    return None
                time.sleep(0.5 * (attempt + 1))
        
        return None
    
    def post(self, endpoint: str, **kwargs) -> Optional[requests.Response]:
        """Make POST request."""
        return self._make_request("POST", endpoint, **kwargs)
    
    def get(self, endpoint: str, **kwargs) -> Optional[requests.Response]:
        """Make GET request."""
        return self._make_request("GET", endpoint, **kwargs)

class SessionManager:
    """Enhanced session state management."""
    
    @staticmethod
    def initialize():
        """Initialize comprehensive session state."""
        defaults = {
            "authenticated": False,
            "user_info": None,
            "access_token": None,
            "chat_history": [],
            "current_session_id": str(uuid.uuid4()),
            "sessions": [],
            "typing_indicator": False,
            "last_activity": time.time(),
            "theme": "professional",
            "chat_stats": {"total_messages": 0, "avg_response_time": 0, "avg_confidence": 0.85},
            "user_preferences": {"auto_scroll": True, "sound_enabled": False, "compact_mode": False},
            "system_status": "online",
            "loading": False,
            "error_message": None
        }

        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value
    
    @staticmethod
    def clear():
        """Clear session state."""
        for key in list(st.session_state.keys()):
            del st.session_state[key]
    
    @staticmethod
    def update_activity():
        """Update last activity timestamp."""
        st.session_state.last_activity = time.time()

class MessageRenderer:
    """Enhanced message rendering with improved UX."""
    
    @staticmethod
    def clean_content(content: str) -> str:
        """Clean and sanitize message content."""
        if not content:
            return ""
        
        # Remove problematic HTML tags
        content = re.sub(r'<span[^>]*>', '', content)
        content = re.sub(r'</span>', '', content)
        content = re.sub(r'<div[^>]*>', '', content)
        content = re.sub(r'</div>', '', content)
        
        # Clean up HTML entities
        content = html.unescape(content)
        
        return content.strip()
    
    @staticmethod
    def get_confidence_class(confidence: float) -> str:
        """Get CSS class for confidence level."""
        if confidence >= 0.8:
            return "confidence-badge"
        elif confidence >= 0.6:
            return "confidence-badge confidence-medium"
        else:
            return "confidence-badge confidence-low"
    
    @staticmethod
    def format_timestamp(timestamp: str) -> str:
        """Format timestamp for display."""
        try:
            dt = datetime.fromisoformat(timestamp)
            return dt.strftime("%H:%M")
        except:
            return datetime.now().strftime("%H:%M")

# ============================
# MAIN APPLICATION CLASS
# ============================

class FinSolveAIAssistant:
    """
    Enhanced FinSolve AI Assistant Application
    Enterprise-grade chat interface with improved UI/UX and accessibility
    """

    def __init__(self):
        """Initialize the application."""
        SessionManager.initialize()
        self.api_client = APIClient()
        self.message_renderer = MessageRenderer()
        
        # Apply enhanced styling
        st.markdown(get_enhanced_css(), unsafe_allow_html=True)
    
    def get_logo_base64(self) -> str:
        """Get FinSolve logo as base64 string with fallback."""
        try:
            logo_path = Path(__file__).parent.parent.parent / "finsolve.png"
            if logo_path.exists():
                with open(logo_path, "rb") as f:
                    return base64.b64encode(f.read()).decode()
        except Exception as e:
            logger.warning(f"Could not load logo: {e}")
        return ""
    
    def display_header(self, title: str, subtitle: str):
        """Display enhanced application header."""
        logo_base64 = self.get_logo_base64()
        
        st.markdown(f"""
        <div class="finsolve-header">
            <div style="display: flex; align-items: center; justify-content: center; gap: 1.5rem; position: relative; z-index: 1;">
                <div class="header-logo">
                    {f'<img src="data:image/png;base64,{logo_base64}" style="width: 100%; height: 100%; object-fit: contain;" alt="FinSolve">' if logo_base64 else '<span style="color: var(--finsolve-deep-blue); font-weight: 800; font-size: 2rem;">FS</span>'}
                </div>
                <div style="text-align: center;">
                    <h1 class="header-title">{title}</h1>
                    <p class="header-subtitle">{subtitle}</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def display_system_status(self):
        """Display enhanced system status indicators."""
        col1, col2, col3, col4 = st.columns(4)
        
        status_metrics = [
            {"icon": "●", "value": "Online", "label": "System Status", "color": "var(--finsolve-success)"},
            {"icon": "⚡", "value": "99.9%", "label": "Uptime", "color": "var(--finsolve-info)"},
            {"icon": "🚀", "value": "< 2s", "label": "Response Time", "color": "var(--finsolve-warning)"},
            {"icon": "🔒", "value": "Secure", "label": "Security", "color": "var(--finsolve-success)"}
        ]
        
        for col, metric in zip([col1, col2, col3, col4], status_metrics):
            with col:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value" style="color: {metric['color']};">
                        {metric['icon']} {metric['value']}
                    </div>
                    <div class="metric-label">{metric['label']}</div>
                </div>
                """, unsafe_allow_html=True)
    
    def display_demo_credentials(self):
        """Display demo credentials with enhanced styling."""
        st.markdown("### 🎯 Demo Access")
        st.markdown("*Choose your role for instant access*")

        demo_users = [
            {"username": "admin", "password": "Admin123!", "role": "C-Level Executive", "icon": "👑"},
            {"username": "peter.pandey", "password": "Engineering123!", "role": "AI Engineer", "icon": "⚙️"},
            {"username": "jane.smith", "password": "HRpass123!", "role": "HR Manager", "icon": "👥"},
            {"username": "mike.johnson", "password": "Finance123!", "role": "Finance Analyst", "icon": "💰"},
            {"username": "sarah.wilson", "password": "Marketing123!", "role": "Marketing Manager", "icon": "📈"},
            {"username": "john.doe", "password": "Employee123!", "role": "Employee", "icon": "👤"}
        ]

        cols = st.columns(2)
        for i, user in enumerate(demo_users):
            with cols[i % 2]:
                if st.button(
                    f"{user['icon']} {user['role']}",
                    key=f"demo_{user['username']}",
                    use_container_width=True,
                    help=f"Login as {user['role']}"
                ):
                    self.authenticate_user(user['username'], user['password'])
    
    def display_features_preview(self):
        """Display enhanced features preview."""
        st.markdown("---")
        st.markdown("### ✨ Platform Capabilities")

        features = [
            {"icon": "🤖", "title": "AI-Powered Analytics", "desc": "Advanced ML models for insights"},
            {"icon": "🔐", "title": "Enterprise Security", "desc": "Role-based access & encryption"},
            {"icon": "📊", "title": "Real-time Dashboards", "desc": "Live performance metrics"},
            {"icon": "⚡", "title": "Lightning Performance", "desc": "Sub-second response times"}
        ]

        cols = st.columns(len(features))
        for i, feature in enumerate(features):
            with cols[i]:
                st.markdown(f"""
                <div class="finsolve-card" style="text-align: center; height: 100%;">
                    <div style="font-size: 2.5rem; margin-bottom: 1rem;">{feature['icon']}</div>
                    <div style="font-weight: 700; color: var(--finsolve-deep-blue); margin-bottom: 0.5rem; font-size: 1.1rem;">{feature['title']}</div>
                    <div style="font-size: 0.9rem; color: var(--finsolve-dark-grey); line-height: 1.4;">{feature['desc']}</div>
                </div>
                """, unsafe_allow_html=True)
    
    def authenticate_user(self, username: str, password: str):
        """Enhanced user authentication with better UX."""
        try:
            st.session_state.loading = True
            
            with st.spinner("🔐 Authenticating securely..."):
                response = self.api_client.post(
                    "/auth/login",
                    json={"username": username, "password": password}
                )
                
                if response and response.status_code == 200:
                    data = response.json()
                    st.session_state.authenticated = True
                    st.session_state.access_token = data["access_token"]
                    st.session_state.user_info = data["user"]
                    st.session_state.error_message = None
                    
                    st.success(f"✅ Welcome, {data['user']['full_name']}!")
                    time.sleep(1)  # Brief pause for UX
                    st.rerun()
                else:
                    error_msg = "Invalid credentials. Please try again."
                    if response:
                        try:
                            error_data = response.json()
                            error_msg = error_data.get('detail', error_msg)
                        except:
                            pass
                    
                    st.session_state.error_message = error_msg
                    st.error(f"❌ {error_msg}")
                    
        except Exception as e:
            error_msg = f"Connection error: Please check your network and try again."
            st.session_state.error_message = error_msg
            st.error(f"🔌 {error_msg}")
            logger.error(f"Authentication error: {e}")
        finally:
            st.session_state.loading = False
    
    def logout(self):
        """Enhanced logout with confirmation."""
        try:
            if st.session_state.access_token:
                headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
                self.api_client.post("/auth/logout", headers=headers)
            
            SessionManager.clear()
            st.success("👋 Logged out successfully!")
            time.sleep(1)
            st.rerun()
            
        except Exception as e:
            logger.error(f"Logout error: {e}")
            SessionManager.clear()
            st.rerun()
    
    def get_headers(self) -> Dict[str, str]:
        """Get authorization headers."""
        return {"Authorization": f"Bearer {st.session_state.access_token}"}
    
    def send_message(self, message: str) -> bool:
        """Enhanced message sending with dashboard detection and improved UX."""
        if not message.strip():
            return False

        # Check for dashboard requests
        message_lower = message.lower()
        dashboard_keywords = {
            'executive': ['executive dashboard', 'executive summary', 'executive overview', 'show me executive', 'kpi'],
            'financial': ['financial overview', 'financial dashboard', 'financial performance', 'show me financial', 'revenue', 'profit'],
            'departmental': ['departmental overview', 'department dashboard', 'staff by department', 'employee breakdown', 'organizational'],
            'general': ['company overview', 'company dashboard', 'general dashboard']
        }

        for dashboard_type, keywords in dashboard_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                st.session_state.show_dashboard = dashboard_type
                return True

        try:
            st.session_state.loading = True
            SessionManager.update_activity()
            
            with st.spinner("🤖 Processing your request..."):
                response = self.api_client.post(
                    "/chat/message",
                    json={
                        "content": message,
                        "session_id": st.session_state.current_session_id
                    },
                    headers=self.get_headers()
                )
                
                if response and response.status_code == 200:
                    data = response.json()
                    
                    # Add user message
                    st.session_state.chat_history.append({
                        "content": message,
                        "message_type": "user",
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    # Process AI response
                    confidence = data.get("confidence_score", 0.0)
                    content = data["content"]
                    
                    # Add assistant response
                    st.session_state.chat_history.append({
                        "content": content,
                        "message_type": "assistant",
                        "timestamp": data.get("timestamp", datetime.now().isoformat()),
                        "retrieved_documents": data.get("retrieved_documents", []),
                        "confidence_score": confidence,
                        "processing_time": data.get("processing_time"),
                        "visualization": data.get("visualization")
                    })
                    
                    # Update stats
                    st.session_state.chat_stats["total_messages"] = len(st.session_state.chat_history)
                    
                    return True
                else:
                    error_msg = "Failed to send message. Please try again."
                    if response:
                        try:
                            error_data = response.json()
                            error_msg = error_data.get('detail', error_msg)
                        except:
                            pass
                    
                    st.error(f"❌ {error_msg}")
                    return False
                    
        except Exception as e:
            st.error(f"🔌 Connection error: {str(e)}")
            logger.error(f"Message sending error: {e}")
            return False
        finally:
            st.session_state.loading = False
    
    def display_chat_message(self, message: Dict[str, Any]):
        """Display enhanced chat message with improved styling."""
        is_user = message["message_type"] == "user"
        timestamp = self.message_renderer.format_timestamp(message.get("timestamp", ""))
        clean_content = self.message_renderer.clean_content(message["content"])
        
        if is_user:
            st.markdown(f"""
            <div class="chat-message">
                <div class="user-message">
                    <div class="message-header">
                        <strong>👤 You</strong>
                        <span style="opacity: 0.8;">{timestamp}</span>
                    </div>
                    <div class="message-content">{clean_content}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            confidence = message.get("confidence_score", 0.0)
            processing_time = message.get("processing_time")
            sources = message.get("retrieved_documents", [])
            
            confidence_class = self.message_renderer.get_confidence_class(confidence)
            confidence_emoji = "🟢" if confidence > 0.8 else "🟡" if confidence > 0.6 else "🔴"
            
            st.markdown(f"""
            <div class="chat-message">
                <div class="assistant-message">
                    <div class="message-header">
                        <div style="display: flex; align-items: center; gap: 0.5rem;">
                            <strong style="color: var(--finsolve-deep-blue);">🤖 FinSolve AI</strong>
                            <span class="{confidence_class}">
                                {confidence_emoji} {confidence:.1%}
                            </span>
                        </div>
                        <span style="color: var(--finsolve-dark-grey);">{timestamp}</span>
                    </div>
                    <div class="message-content">{clean_content}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Display visualization if available
            visualization = message.get("visualization")
            if visualization:
                self.display_visualization(visualization)
            
            # Display metadata
            if sources or processing_time:
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    if sources:
                        with st.expander(f"📚 Sources ({len(sources)})", expanded=False):
                            for i, source in enumerate(sources, 1):
                                st.markdown(f"**{i}.** `{source}`")
                
                with col2:
                    if processing_time:
                        st.caption(f"⚡ {processing_time:.1f}s")
    
    def display_dashboard(self, dashboard_type: str, user_role: str):
        """Display interactive dashboard based on type and user role"""
        if dashboard_type == "executive":
            self.display_executive_dashboard()
        elif dashboard_type == "financial":
            self.display_financial_dashboard()
        elif dashboard_type == "departmental":
            self.display_departmental_dashboard()
        else:
            self.display_general_dashboard()

    def display_executive_dashboard(self):
        """Display comprehensive executive dashboard"""
        st.markdown("## 📊 Executive Dashboard")

        # Key Metrics Row
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="📈 Total Revenue (2024)",
                value="$9.5B",
                delta="23.8% vs Q1"
            )

        with col2:
            st.metric(
                label="👥 Total Employees",
                value="57",
                delta="13 departments"
            )

        with col3:
            st.metric(
                label="💰 Gross Margin",
                value="64%",
                delta="+6% vs Q1"
            )

        with col4:
            st.metric(
                label="🎯 Customer Retention",
                value="95%",
                delta="+2% YoY"
            )

        # Charts Row
        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            # Quarterly Revenue Chart
            quarters = ['Q1 2024', 'Q2 2024', 'Q3 2024', 'Q4 2024']
            revenue = [2.1, 2.3, 2.5, 2.6]

            fig_revenue = go.Figure()
            fig_revenue.add_trace(go.Scatter(
                x=quarters, y=revenue,
                mode='lines+markers',
                name='Revenue (Billions)',
                line=dict(color='#0D1B2A', width=4),
                marker=dict(size=10, color='#00F5D4')
            ))

            fig_revenue.update_layout(
                title='Quarterly Revenue Growth',
                xaxis_title='Quarter',
                yaxis_title='Revenue (Billions USD)',
                height=300,
                font=dict(family="Roboto", size=12),
                title_font=dict(family="Poppins", size=16, color='#0D1B2A')
            )

            st.plotly_chart(fig_revenue, use_container_width=True)

        with chart_col2:
            # Department Distribution
            departments = ['Engineering', 'Marketing', 'Sales', 'Customer Support', 'Finance', 'Others']
            employees = [14, 6, 6, 5, 4, 22]

            fig_dept = go.Figure(data=[go.Pie(
                labels=departments,
                values=employees,
                hole=0.4,
                marker_colors=['#0D1B2A', '#00F5D4', '#4CAF50', '#FF9800', '#9C27B0', '#A9A9A9']
            )])

            fig_dept.update_layout(
                title='Staff Distribution by Department',
                height=300,
                font=dict(family="Roboto", size=12),
                title_font=dict(family="Poppins", size=16, color='#0D1B2A')
            )

            st.plotly_chart(fig_dept, use_container_width=True)

        # Performance Indicators
        st.markdown("### 🎯 Key Performance Indicators")

        kpi_col1, kpi_col2, kpi_col3 = st.columns(3)

        with kpi_col1:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
                        padding: 1rem; border-radius: 12px; text-align: center; color: white;">
                <h3 style="margin: 0; font-size: 1.5rem;">Customer Satisfaction</h3>
                <p style="margin: 0.5rem 0 0 0; font-size: 2rem; font-weight: bold;">4.7/5</p>
            </div>
            """, unsafe_allow_html=True)

        with kpi_col2:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
                        padding: 1rem; border-radius: 12px; text-align: center; color: white;">
                <h3 style="margin: 0; font-size: 1.5rem;">System Uptime</h3>
                <p style="margin: 0.5rem 0 0 0; font-size: 2rem; font-weight: bold;">99.99%</p>
            </div>
            """, unsafe_allow_html=True)

        with kpi_col3:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%);
                        padding: 1rem; border-radius: 12px; text-align: center; color: white;">
                <h3 style="margin: 0; font-size: 1.5rem;">Market Growth</h3>
                <p style="margin: 0.5rem 0 0 0; font-size: 2rem; font-weight: bold;">+30%</p>
            </div>
            """, unsafe_allow_html=True)

    def display_financial_dashboard(self):
        """Display comprehensive financial dashboard"""
        st.markdown("## 💰 Financial Performance Dashboard")

        # Financial Metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="💵 Q4 Revenue",
                value="$2.6B",
                delta="$0.5B vs Q1"
            )

        with col2:
            st.metric(
                label="📊 Operating Margin",
                value="26%",
                delta="+6% vs Q1"
            )

        with col3:
            st.metric(
                label="💎 Net Profit Margin",
                value="19%",
                delta="+4% vs Q1"
            )

        with col4:
            st.metric(
                label="💰 EBIT",
                value="$674M",
                delta="+60% vs Q1"
            )

        # Financial Charts
        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            # Revenue vs Profit
            quarters = ['Q1 2024', 'Q2 2024', 'Q3 2024', 'Q4 2024']
            revenue = [2.1, 2.3, 2.5, 2.6]
            profit = [0.315, 0.391, 0.45, 0.494]  # 15%, 17%, 18%, 19% margins

            fig_financial = make_subplots(specs=[[{"secondary_y": True}]])

            fig_financial.add_trace(
                go.Bar(x=quarters, y=revenue, name="Revenue (Billions)",
                      marker_color='#0D1B2A', opacity=0.8),
                secondary_y=False,
            )

            fig_financial.add_trace(
                go.Scatter(x=quarters, y=profit, mode='lines+markers',
                          name="Net Profit (Billions)", line=dict(color='#00F5D4', width=4),
                          marker=dict(size=8)),
                secondary_y=True,
            )

            fig_financial.update_xaxes(title_text="Quarter")
            fig_financial.update_yaxes(title_text="Revenue (Billions USD)", secondary_y=False)
            fig_financial.update_yaxes(title_text="Net Profit (Billions USD)", secondary_y=True)

            fig_financial.update_layout(
                title='Revenue vs Net Profit Trend',
                height=350,
                font=dict(family="Roboto", size=12),
                title_font=dict(family="Poppins", size=16, color='#0D1B2A')
            )

            st.plotly_chart(fig_financial, use_container_width=True)

        with chart_col2:
            # Margin Improvement
            margins = ['Gross Margin', 'Operating Margin', 'Net Profit Margin']
            q1_margins = [58, 20, 15]
            q4_margins = [64, 26, 19]

            fig_margins = go.Figure()

            fig_margins.add_trace(go.Bar(
                name='Q1 2024',
                x=margins,
                y=q1_margins,
                marker_color='#A9A9A9'
            ))

            fig_margins.add_trace(go.Bar(
                name='Q4 2024',
                x=margins,
                y=q4_margins,
                marker_color='#00F5D4'
            ))

            fig_margins.update_layout(
                title='Margin Improvement (Q1 vs Q4)',
                xaxis_title='Margin Type',
                yaxis_title='Percentage (%)',
                height=350,
                barmode='group',
                font=dict(family="Roboto", size=12),
                title_font=dict(family="Poppins", size=16, color='#0D1B2A')
            )

            st.plotly_chart(fig_margins, use_container_width=True)

        # Financial Health Indicators
        st.markdown("### 💎 Financial Health Indicators")

        health_col1, health_col2, health_col3, health_col4 = st.columns(4)

        with health_col1:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
                        padding: 1rem; border-radius: 12px; text-align: center; color: white;">
                <h4 style="margin: 0;">Cash Reserves</h4>
                <p style="margin: 0.5rem 0 0 0; font-size: 1.5rem; font-weight: bold;">$1.2B</p>
            </div>
            """, unsafe_allow_html=True)

        with health_col2:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
                        padding: 1rem; border-radius: 12px; text-align: center; color: white;">
                <h4 style="margin: 0;">Debt-to-Equity</h4>
                <p style="margin: 0.5rem 0 0 0; font-size: 1.5rem; font-weight: bold;">0.3</p>
            </div>
            """, unsafe_allow_html=True)

        with health_col3:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%);
                        padding: 1rem; border-radius: 12px; text-align: center; color: white;">
                <h4 style="margin: 0;">ROI</h4>
                <p style="margin: 0.5rem 0 0 0; font-size: 1.5rem; font-weight: bold;">150%</p>
            </div>
            """, unsafe_allow_html=True)

        with health_col4:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #9C27B0 0%, #7B1FA2 100%);
                        padding: 1rem; border-radius: 12px; text-align: center; color: white;">
                <h4 style="margin: 0;">ARPU Growth</h4>
                <p style="margin: 0.5rem 0 0 0; font-size: 1.5rem; font-weight: bold;">+9.5%</p>
            </div>
            """, unsafe_allow_html=True)

    def display_departmental_dashboard(self):
        """Display departmental overview dashboard"""
        st.markdown("## 🏢 Departmental Overview Dashboard")

        # Department metrics
        departments_data = {
            'Engineering': {'employees': 14, 'budget': '$2.1M', 'projects': 8},
            'Marketing': {'employees': 6, 'budget': '$1.2M', 'projects': 12},
            'Sales': {'employees': 6, 'budget': '$0.8M', 'projects': 15},
            'Customer Support': {'employees': 5, 'budget': '$0.6M', 'projects': 3},
            'Finance': {'employees': 4, 'budget': '$0.5M', 'projects': 5},
            'HR': {'employees': 3, 'budget': '$0.4M', 'projects': 4},
            'IT Security': {'employees': 5, 'budget': '$0.9M', 'projects': 6},
            'Data Analytics': {'employees': 3, 'budget': '$0.7M', 'projects': 7},
            'R&D': {'employees': 2, 'budget': '$1.5M', 'projects': 4},
            'QA': {'employees': 2, 'budget': '$0.3M', 'projects': 10},
            'Operations': {'employees': 2, 'budget': '$0.4M', 'projects': 6},
            'Legal': {'employees': 3, 'budget': '$0.5M', 'projects': 2},
            'Executive': {'employees': 2, 'budget': '$0.8M', 'projects': 3}
        }

        # Create department cards
        cols = st.columns(3)
        for i, (dept, data) in enumerate(departments_data.items()):
            with cols[i % 3]:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, rgba(0, 245, 212, 0.1) 0%, rgba(13, 27, 42, 0.05) 100%);
                            padding: 1rem; border-radius: 12px; margin-bottom: 1rem;
                            border: 2px solid rgba(0, 245, 212, 0.3);">
                    <h4 style="margin: 0 0 0.5rem 0; color: #0D1B2A;">{dept}</h4>
                    <p style="margin: 0.2rem 0; color: #666;"><strong>👥 Staff:</strong> {data['employees']}</p>
                    <p style="margin: 0.2rem 0; color: #666;"><strong>💰 Budget:</strong> {data['budget']}</p>
                    <p style="margin: 0.2rem 0; color: #666;"><strong>📋 Projects:</strong> {data['projects']}</p>
                </div>
                """, unsafe_allow_html=True)

        # Department comparison charts
        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            # Staff distribution
            dept_names = list(departments_data.keys())
            staff_counts = [data['employees'] for data in departments_data.values()]

            fig_staff = go.Figure(data=[go.Bar(
                x=dept_names,
                y=staff_counts,
                marker_color='#00F5D4',
                text=staff_counts,
                textposition='auto'
            )])

            fig_staff.update_layout(
                title='Staff Distribution by Department',
                xaxis_title='Department',
                yaxis_title='Number of Employees',
                height=400,
                font=dict(family="Roboto", size=10),
                title_font=dict(family="Poppins", size=16, color='#0D1B2A')
            )

            fig_staff.update_xaxes(tickangle=45)

            st.plotly_chart(fig_staff, use_container_width=True)

        with chart_col2:
            # Top departments by size
            sorted_depts = sorted(departments_data.items(), key=lambda x: x[1]['employees'], reverse=True)[:6]
            top_dept_names = [dept[0] for dept in sorted_depts]
            top_staff_counts = [dept[1]['employees'] for dept in sorted_depts]

            fig_top = go.Figure(data=[go.Pie(
                labels=top_dept_names,
                values=top_staff_counts,
                hole=0.4,
                marker_colors=['#0D1B2A', '#00F5D4', '#4CAF50', '#FF9800', '#9C27B0', '#2196F3']
            )])

            fig_top.update_layout(
                title='Top 6 Departments by Staff Size',
                height=400,
                font=dict(family="Roboto", size=12),
                title_font=dict(family="Poppins", size=16, color='#0D1B2A')
            )

            st.plotly_chart(fig_top, use_container_width=True)

    def display_general_dashboard(self):
        """Display general company dashboard"""
        st.markdown("## 🏢 Company Overview Dashboard")

        # Company metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="🏢 Founded",
                value="2018",
                delta="6 years strong"
            )

        with col2:
            st.metric(
                label="🌍 Markets",
                value="15+",
                delta="Global presence"
            )

        with col3:
            st.metric(
                label="🏆 Awards",
                value="12",
                delta="Industry recognition"
            )

        with col4:
            st.metric(
                label="📈 Growth Rate",
                value="45%",
                delta="YoY expansion"
            )

        # Company highlights
        st.markdown("### 🌟 Company Highlights")

        highlight_col1, highlight_col2 = st.columns(2)

        with highlight_col1:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #0D1B2A 0%, #1a2332 100%);
                        padding: 2rem; border-radius: 16px; color: white; margin-bottom: 1rem;">
                <h3 style="margin: 0 0 1rem 0; color: #00F5D4;">🚀 Mission</h3>
                <p style="margin: 0; line-height: 1.6;">
                    Revolutionizing financial technology through innovative solutions that
                    streamline operations, enhance security, and optimize user experiences
                    across banking, investment, and payment platforms.
                </p>
            </div>
            """, unsafe_allow_html=True)

        with highlight_col2:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #00F5D4 0%, #00d4b8 100%);
                        padding: 2rem; border-radius: 16px; color: #0D1B2A; margin-bottom: 1rem;">
                <h3 style="margin: 0 0 1rem 0;">🎯 Vision</h3>
                <p style="margin: 0; line-height: 1.6; font-weight: 500;">
                    To be the leading global FinTech company that empowers businesses
                    and individuals with cutting-edge financial solutions, driving
                    economic growth and financial inclusion worldwide.
                </p>
            </div>
            """, unsafe_allow_html=True)

    def show_inquiry_form(self):
        """Display email inquiry form in a modal-like interface"""
        st.session_state.show_inquiry_form = True

    def display_inquiry_form(self):
        """Display the email inquiry form"""
        st.markdown("## 📧 Send Inquiry to Expert")
        st.markdown("*Route your question to the right department for expert assistance*")

        with st.form("inquiry_form"):
            # Department selection
            department = st.selectbox(
                "🏢 Select Department",
                ["Finance", "HR", "Engineering", "Marketing", "General Support"],
                help="Choose the most relevant department for your inquiry"
            )

            # Inquiry type
            inquiry_type = st.selectbox(
                "📋 Inquiry Type",
                ["Question", "Technical Support", "Feature Request", "Bug Report", "General Feedback"],
                help="Select the type of inquiry"
            )

            # Priority level
            priority = st.selectbox(
                "⚡ Priority Level",
                ["Low", "Medium", "High", "Urgent"],
                index=1,
                help="Select the urgency of your inquiry"
            )

            # Subject
            subject = st.text_input(
                "📝 Subject",
                placeholder="Brief description of your inquiry",
                help="Provide a clear, concise subject line"
            )

            # Message
            message = st.text_area(
                "💬 Message",
                placeholder="Describe your inquiry in detail...",
                height=150,
                help="Provide as much detail as possible to help us assist you better"
            )

            # Contact preference
            contact_preference = st.selectbox(
                "📞 Preferred Contact Method",
                ["Email", "Phone", "Both"],
                help="How would you like us to respond?"
            )

            # Submit button
            col1, col2 = st.columns(2)

            with col1:
                submit_button = st.form_submit_button(
                    "📨 Send Inquiry",
                    use_container_width=True,
                    type="primary"
                )

            with col2:
                cancel_button = st.form_submit_button(
                    "❌ Cancel",
                    use_container_width=True
                )

            if cancel_button:
                st.session_state.show_inquiry_form = False
                st.rerun()

            if submit_button:
                if subject and message:
                    success = self.send_inquiry_email(
                        department=department,
                        inquiry_type=inquiry_type,
                        priority=priority,
                        subject=subject,
                        message=message,
                        contact_preference=contact_preference
                    )

                    if success:
                        st.success("✅ Inquiry sent successfully! You'll receive a confirmation email shortly.")
                        st.info("📧 Expected response time: Within 48 hours")
                        st.session_state.show_inquiry_form = False
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error("❌ Failed to send inquiry. Please try again or contact us directly.")
                else:
                    st.error("⚠️ Please fill in both subject and message fields.")

    def send_inquiry_email(self, department: str, inquiry_type: str, priority: str,
                          subject: str, message: str, contact_preference: str) -> bool:
        """Send inquiry email to the appropriate department"""
        try:
            # Check if email service is available
            if email_service is None:
                logger.error("Email service not available")
                return False

            # Get user info
            user_info = st.session_state.get('user_info', {})
            user_name = user_info.get('full_name', 'Unknown User')
            user_email = user_info.get('email', 'unknown@example.com')
            user_role = user_info.get('role', 'Employee')

            # Department email mapping (in production, these would be actual department emails)
            department_emails = {
                "Finance": "keyegon@gmail.com",  # Finance Director
                "HR": "keyegon@gmail.com",       # HR Manager
                "Engineering": "keyegon@gmail.com",  # Engineering Lead
                "Marketing": "keyegon@gmail.com",    # Marketing Manager
                "General Support": "keyegon@gmail.com"  # General Support
            }

            recipient_email = department_emails.get(department, "keyegon@gmail.com")

            # Create inquiry data
            inquiry_data = {
                "inquiry_id": f"INQ-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                "department": department,
                "inquiry_type": inquiry_type,
                "priority": priority,
                "subject": subject,
                "message": message,
                "contact_preference": contact_preference,
                "user_name": user_name,
                "user_email": user_email,
                "user_role": user_role,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "system": "FinSolve AI Assistant"
            }

            # Send notification to department
            department_success = email_service.send_notification(
                recipient=recipient_email,
                notification_type="info",
                data=inquiry_data
            )

            # Send confirmation to user
            user_success = email_service.send_email(
                to_emails=[user_email],
                subject=f"✅ Inquiry Confirmation - {inquiry_data['inquiry_id']}",
                body=f"""
Dear {user_name},

Thank you for contacting FinSolve Technologies AI Assistant support.

Your inquiry has been received and assigned ID: {inquiry_data['inquiry_id']}

Inquiry Details:
- Department: {department}
- Type: {inquiry_type}
- Priority: {priority}
- Subject: {subject}

What happens next:
1. Your inquiry has been routed to our {department} team
2. You will receive a response within 48 hours
3. For urgent matters, please call our office line

Thank you for using FinSolve AI Assistant!

Best regards,
Dr. Erick K. Yegon
FinSolve Technologies AI Assistant
keyegon@gmail.com
                """,
                html_body=f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Inquiry Confirmation</title>
</head>
<body style="font-family: 'Roboto', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #0D1B2A 0%, #1a2332 100%); padding: 30px; border-radius: 12px; text-align: center; margin-bottom: 30px;">
        <h1 style="color: #00F5D4; margin: 0; font-size: 28px;">🏦 FinSolve Technologies</h1>
        <p style="color: #FFFFFF; margin: 10px 0 0 0; font-size: 18px;">Inquiry Confirmation</p>
    </div>

    <div style="background: #f8f9fa; padding: 25px; border-radius: 12px; margin-bottom: 20px;">
        <h2 style="color: #0D1B2A; margin-top: 0;">Dear {user_name},</h2>
        <p>Thank you for contacting <strong>FinSolve Technologies AI Assistant</strong> support.</p>

        <div style="background: #e8f5e8; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <h3 style="color: #00F5D4; margin-top: 0;">✅ Inquiry Received</h3>
            <p><strong>Inquiry ID:</strong> {inquiry_data['inquiry_id']}</p>
        </div>

        <h3 style="color: #0D1B2A;">📋 Inquiry Details:</h3>
        <ul style="background: #f1f1f1; padding: 15px; border-radius: 6px;">
            <li><strong>Department:</strong> {department}</li>
            <li><strong>Type:</strong> {inquiry_type}</li>
            <li><strong>Priority:</strong> {priority}</li>
            <li><strong>Subject:</strong> {subject}</li>
        </ul>

        <h3 style="color: #00F5D4;">🚀 What happens next:</h3>
        <ol>
            <li>Your inquiry has been routed to our <strong>{department}</strong> team</li>
            <li>You will receive a response within <strong>48 hours</strong></li>
            <li>For urgent matters, please call our office line</li>
        </ol>
    </div>

    <div style="background: #0D1B2A; padding: 20px; border-radius: 8px; text-align: center; color: #FFFFFF;">
        <p style="margin: 0; font-size: 16px;">Thank you for using <strong>FinSolve AI Assistant!</strong></p>
        <hr style="border: none; border-top: 1px solid #00F5D4; margin: 15px 0;">
        <p style="margin: 0; color: #00F5D4;">
            <strong>Dr. Erick K. Yegon</strong><br>
            FinSolve Technologies AI Assistant<br>
            <a href="mailto:keyegon@gmail.com" style="color: #00F5D4;">keyegon@gmail.com</a>
        </p>
    </div>
</body>
</html>
                """
            )

            return department_success and user_success

        except Exception as e:
            logger.error(f"Failed to send inquiry email: {str(e)}")
            return False

    def display_visualization(self, visualization: Dict[str, Any]):
        """Display enhanced visualizations with professional presentation."""
        try:
            chart_data = visualization.get("chart")
            explanation = visualization.get("explanation", "")
            
            if chart_data is None:
                return
            
            st.markdown("""
            <div class="finsolve-card" style="margin: 1.5rem 0;">
            """, unsafe_allow_html=True)
            
            # Handle different chart types
            if isinstance(chart_data, dict):
                chart_type = chart_data.get("type", "unknown")
                data = chart_data.get("data")
                
                if chart_type == "plotly" and data:
                    try:
                        fig = go.Figure(json.loads(data))
                        
                        # Apply FinSolve styling to chart
                        fig.update_layout(
                            font_family=FINSOLVE_BRAND["fonts"]["secondary"],
                            font_color=FINSOLVE_BRAND["colors"]["deep_blue"],
                            plot_bgcolor="rgba(0,0,0,0)",
                            paper_bgcolor="rgba(0,0,0,0)",
                        )
                        
                        st.plotly_chart(fig, use_container_width=True, config={
                            'displayModeBar': True,
                            'displaylogo': False,
                            'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d'],
                            'toImageButtonOptions': {
                                'format': 'png',
                                'filename': 'finsolve_chart',
                                'height': 500,
                                'width': 800,
                                'scale': 2
                            }
                        })
                        
                    except Exception as e:
                        logger.error(f"Chart rendering error: {e}")
                        st.info("📊 Chart visualization temporarily unavailable")
                
                elif chart_type == "dataframe" and data:
                    st.markdown("#### 📋 Data Analysis")
                    df = pd.DataFrame(data)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                
                elif chart_type == "metrics" and data:
                    st.markdown("#### 📊 Key Metrics")
                    self.display_metrics_dashboard(data)
            
            # Display explanation
            if explanation:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, rgba(0, 245, 212, 0.08) 0%, rgba(13, 27, 42, 0.05) 100%);
                            padding: 1.5rem; border-radius: var(--border-radius-medium); margin: 1rem 0;
                            border-left: 4px solid var(--finsolve-teal);">
                    <div style="font-size: 1rem; color: var(--finsolve-dark-grey); line-height: 1.6; font-weight: 500;">
                        {explanation}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
            
        except Exception as e:
            logger.error(f"Visualization error: {e}")
            st.info("📊 Processing visualization...")
    
    def display_metrics_dashboard(self, metrics: Dict[str, Any]):
        """Display enhanced metrics dashboard."""
        if not metrics:
            return
        
        # Create responsive columns
        num_metrics = len(metrics)
        if num_metrics <= 4:
            cols = st.columns(num_metrics)
            for col, (key, value) in zip(cols, metrics.items()):
                with col:
                    st.metric(label=key, value=value)
        else:
            # Split into rows for better display
            rows = [list(metrics.items())[i:i+4] for i in range(0, len(metrics), 4)]
            for row in rows:
                cols = st.columns(len(row))
                for col, (key, value) in zip(cols, row):
                    with col:
                        st.metric(label=key, value=value)
    
    def display_welcome_message(self):
        """Display enhanced welcome message."""
        user = st.session_state.user_info
        role_suggestions = {
            "c_level": "strategic insights, executive summaries, and company performance metrics",
            "hr": "employee analytics, performance data, and HR policy information",
            "finance": "financial reports, budget analysis, and expense tracking",
            "marketing": "campaign performance, customer insights, and market analytics",
            "engineering": "technical documentation, system metrics, and development insights",
            "employee": "company policies, procedures, and general information"
        }
        
        suggestion = role_suggestions.get(user['role'].lower(), "comprehensive business insights")
        
        st.markdown(f"""
        <div class="welcome-container">
            <div class="welcome-emoji">🤖</div>
            <h2 class="welcome-title">Ready to Assist You!</h2>
            <p class="welcome-description">
                I'm your <strong style="color: var(--finsolve-deep-blue); background: var(--gradient-secondary);
                padding: 0.2rem 0.6rem; border-radius: 8px; color: white;">FinSolve AI Expert</strong>, 
                specialized in {suggestion}.
            </p>
            <div style="display: flex; justify-content: center; gap: 1rem; flex-wrap: wrap; margin-top: 2rem;">
                <div class="feature-tag">
                    <span>📊 Advanced Analytics</span>
                </div>
                <div class="feature-tag">
                    <span>💰 Financial Intelligence</span>
                </div>
                <div class="feature-tag">
                    <span>👥 HR Insights</span>
                </div>
                <div class="feature-tag">
                    <span>🚀 Real-time Data</span>
                </div>
            </div>
            <p style="color: var(--finsolve-dark-grey); font-size: 1.1rem; margin-top: 2rem; font-weight: 600;">
                💡 Start by typing a question or using the quick actions sidebar!
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    def display_user_analytics(self):
        """Display enhanced user session analytics."""
        total_messages = len(st.session_state.chat_history)
        user_messages = len([m for m in st.session_state.chat_history if m["message_type"] == "user"])
        ai_messages = total_messages - user_messages
        avg_confidence = st.session_state.chat_stats.get("avg_confidence", 0.85)
        
        st.markdown(f"""
        <div class="finsolve-card" style="background: rgba(255, 255, 255, 0.95); text-align: center;">
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 1rem;">
                <div class="metric-card">
                    <div class="metric-value">{total_messages}</div>
                    <div class="metric-label">Total Messages</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{user_messages}</div>
                    <div class="metric-label">Questions</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{ai_messages}</div>
                    <div class="metric-label">AI Responses</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" style="color: var(--finsolve-success);">{avg_confidence:.0%}</div>
                    <div class="metric-label">Avg Confidence</div>
                </div>
            </div>
            <div class="status-indicator status-online" style="margin-top: 1rem;">
                ● Session Active • ID: {st.session_state.current_session_id[:8]}...
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def display_quick_actions_sidebar(self):
        """Display enhanced quick actions in sidebar."""
        st.markdown("### ⚡ Quick Actions")
        
        user_role = st.session_state.user_info.get('role', 'employee').lower()
        
        # Role-specific quick actions
        role_actions = {
            "c_level": [
                {"icon": "📊", "label": "Executive Dashboard", "query": "Show me executive summary and KPIs"},
                {"icon": "💰", "label": "Financial Overview", "query": "What's our current financial performance?"},
                {"icon": "🎯", "label": "Strategic Goals", "query": "How are we performing against strategic objectives?"},
                {"icon": "👥", "label": "Team Performance", "query": "Show me team performance metrics"}
            ],
            "hr": [
                {"icon": "👥", "label": "Employee Count", "query": "How many employees by department?"},
                {"icon": "📈", "label": "Performance Data", "query": "Show me employee performance metrics"},
                {"icon": "🎓", "label": "Training Status", "query": "What's our training completion status?"},
                {"icon": "📋", "label": "HR Policies", "query": "What are our main HR policies?"}
            ],
            "finance": [
                {"icon": "💰", "label": "Revenue Analysis", "query": "Show me quarterly revenue analysis"},
                {"icon": "📊", "label": "Expense Report", "query": "What are our major expense categories?"},
                {"icon": "💳", "label": "Budget Status", "query": "How are we tracking against budget?"},
                {"icon": "📈", "label": "Financial Trends", "query": "Show me financial trends and forecasts"}
            ]
        }
        
        # Default actions for all roles
        default_actions = [
            {"icon": "🔍", "label": "Company Overview", "query": "Give me a company overview"},
            {"icon": "📋", "label": "Policies", "query": "What are our main company policies?"},
            {"icon": "💡", "label": "Help", "query": "What can you help me with?"},
            {"icon": "📊", "label": "Analytics", "query": "Show me key performance metrics"}
        ]
        
        actions = role_actions.get(user_role, default_actions)
        
        for action in actions:
            if st.button(
                f"{action['icon']} {action['label']}",
                key=f"quick_{action['label'].lower().replace(' ', '_')}",
                use_container_width=True,
                help=f"Show: {action['label']}"
            ):
                # Check if this is a dashboard request
                label_lower = action['label'].lower()
                if 'dashboard' in label_lower or 'overview' in label_lower:
                    # Store dashboard request in session state
                    if 'executive' in label_lower:
                        st.session_state.show_dashboard = 'executive'
                    elif 'financial' in label_lower:
                        st.session_state.show_dashboard = 'financial'
                    elif 'team' in label_lower or 'department' in label_lower:
                        st.session_state.show_dashboard = 'departmental'
                    else:
                        st.session_state.show_dashboard = 'general'
                    st.rerun()
                else:
                    # Regular message for non-dashboard actions
                    if self.send_message(action['query']):
                        st.rerun()
    
    def display_enhanced_sidebar(self):
        """Display enhanced sidebar with improved organization."""
        with st.sidebar:
            # User profile section
            user = st.session_state.user_info
            role_config = ROLE_CONFIG.get(user['role'].lower(), ROLE_CONFIG['employee'])
            
            st.markdown(f"""
            <div class="sidebar-section">
                <div style="text-align: center;">
                    <div style="font-size: 3.5rem; margin-bottom: 1rem;">{role_config['icon']}</div>
                    <h3 style="margin: 0; color: var(--finsolve-deep-blue); font-family: var(--font-primary);">{user['full_name']}</h3>
                    <div style="background: {role_config['color']}; color: white; padding: 0.4rem 1rem;
                                border-radius: 20px; font-size: 0.9rem; font-weight: 600;
                                display: inline-block; margin: 0.8rem 0; box-shadow: var(--shadow-light);">
                        {user['role'].replace('_', ' ').title()}
                    </div>
                    <p style="margin: 0.5rem 0; color: var(--finsolve-dark-grey); font-size: 0.95rem;">
                        {user.get('department', 'General')} Department
                    </p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Action buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🚪 Logout", use_container_width=True, type="secondary"):
                    self.logout()
            with col2:
                if st.button("✨ New Chat", use_container_width=True, type="primary"):
                    st.session_state.current_session_id = str(uuid.uuid4())
                    st.session_state.chat_history = []
                    st.success("New chat started!")
                    st.rerun()
            
            st.markdown("---")
            
            # Quick actions
            self.display_quick_actions_sidebar()
            
            st.markdown("---")
            
            # AI status
            st.markdown("### 🤖 AI Assistant Status")
            st.markdown(f"""
            <div class="status-indicator status-online">
                ● Online & Ready
            </div>
            <div style="margin-top: 0.8rem; font-size: 0.85rem; color: var(--finsolve-dark-grey);">
                <strong>Response:</strong> ~1.2s<br>
                <strong>Confidence:</strong> High<br>
                <strong>Updated:</strong> Just now
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Session stats
            if st.session_state.chat_history:
                st.markdown("### 📊 Session Stats")
                total = len(st.session_state.chat_history)
                user_msgs = len([m for m in st.session_state.chat_history if m["message_type"] == "user"])

                st.metric("Messages", total)
                st.metric("Questions", user_msgs)
                st.metric("Responses", total - user_msgs)

            # Email Inquiry System
            st.markdown("---")
            st.markdown("### 📧 Need Help?")
            st.markdown("*Get expert assistance from our team*")

            if st.button("📨 Send Inquiry to Expert", use_container_width=True, help="Route your question to the right department"):
                self.show_inquiry_form()

            # Contact Information
            st.markdown("### 📞 Contact Information")
            st.markdown("""
            <div style="background: linear-gradient(135deg, rgba(0, 245, 212, 0.1) 0%, rgba(13, 27, 42, 0.05) 100%);
                        padding: 1rem; border-radius: 12px; margin-bottom: 1rem;
                        border: 2px solid rgba(0, 245, 212, 0.3);">
                <p style="margin: 0.2rem 0; color: #0D1B2A;"><strong>📧 Email:</strong> keyegon@gmail.com</p>
                <p style="margin: 0.2rem 0; color: #0D1B2A;"><strong>🏢 Developer:</strong> Dr. Erick K. Yegon</p>
                <p style="margin: 0.2rem 0; color: #0D1B2A;"><strong>⏰ Response:</strong> Within 48 hours</p>
                <p style="margin: 0.2rem 0; color: #0D1B2A;"><strong>🚨 Urgent:</strong> Call office line</p>
            </div>
            """, unsafe_allow_html=True)
    
    def display_message_input(self):
        """Display enhanced message input interface."""
        st.markdown("""
        <div class="input-container">
            <label class="input-label">💬 Ask Your Question</label>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("message_form", clear_on_submit=True):
            user_input = st.text_area(
                "Message",
                placeholder="Type your question here... (e.g., 'Show quarterly performance', 'How many employees by department?', 'What are our policies?')",
                height=120,
                label_visibility="collapsed",
                help="I can help with financial data, employee information, company policies, and strategic insights.",
                disabled=st.session_state.loading
            )
            
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                send_button = st.form_submit_button(
                    "🚀 Send Message" if not st.session_state.loading else "⏳ Processing...",
                    use_container_width=True,
                    type="primary",
                    disabled=st.session_state.loading
                )
            
            with col2:
                if st.form_submit_button("🎲 Suggest", use_container_width=True, help="Get a suggestion"):
                    suggestions = [
                        "Show me key performance indicators",
                        "What's our employee headcount?",
                        "Give me a financial overview",
                        "What are our main policies?"
                    ]
                    if self.send_message(suggestions[0]):
                        st.rerun()
            
            with col3:
                if st.form_submit_button("🗑️ Clear", use_container_width=True, help="Clear chat"):
                    st.session_state.chat_history = []
                    st.session_state.current_session_id = str(uuid.uuid4())
                    st.rerun()
            
            with col4:
                if st.form_submit_button("📊 Stats", use_container_width=True, help="Show statistics"):
                    st.info(f"Session: {len(st.session_state.chat_history)} messages")
            
            if send_button and user_input.strip() and not st.session_state.loading:
                if self.send_message(user_input.strip()):
                    st.rerun()
    
    def login_page(self):
        """Display enhanced login page with registration option."""
        # Main header
        self.display_header("FinSolve Technologies", "AI-Powered Financial Intelligence Platform")

        # System status
        self.display_system_status()

        # Tab selection for Login/Register
        tab1, tab2 = st.tabs(["🔐 Login", "👤 Register"])

        with tab1:
            self.display_login_form()

        with tab2:
            self.display_registration_form()

    def display_login_form(self):
        """Display the login form."""
        _, col2, _ = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("""
            <div class="login-container">
                <div style="text-align: center; margin-bottom: 2.5rem;">
                    <h2 style="color: var(--finsolve-deep-blue); margin-bottom: 0.8rem; font-family: var(--font-primary);">🔐 Secure Access Portal</h2>
                    <p style="color: var(--finsolve-dark-grey); margin: 0; font-size: 1.1rem;">Enter your credentials to access the AI assistant</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Error message display
            if st.session_state.get('error_message'):
                st.error(st.session_state.error_message)
            
            with st.form("login_form", clear_on_submit=False):
                st.markdown("#### 🔑 Login Credentials")
                
                username = st.text_input(
                    "Username",
                    placeholder="Enter your username",
                    help="Use demo credentials below or your assigned username",
                    disabled=st.session_state.loading
                )
                
                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Enter your password",
                    help="Secure password with minimum 8 characters",
                    disabled=st.session_state.loading
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    remember_me = st.checkbox("Remember me", help="Keep me logged in for 30 days")
                with col2:
                    submit_button = st.form_submit_button(
                        "🚀 Login" if not st.session_state.loading else "⏳ Authenticating...",
                        use_container_width=True,
                        type="primary",
                        disabled=st.session_state.loading
                    )
                
                if submit_button and not st.session_state.loading:
                    if username and password:
                        self.authenticate_user(username, password)
                    else:
                        st.error("⚠️ Please enter both username and password")
            
            # Demo credentials
            st.markdown("---")
            self.display_demo_credentials()
            
            # Features preview
            self.display_features_preview()

    def display_registration_form(self):
        """Display the user registration form."""
        _, col2, _ = st.columns([1, 2, 1])

        with col2:
            st.markdown("""
            <div class="finsolve-card" style="padding: 2rem;">
                <h2 style="text-align: center; color: var(--finsolve-deep-blue); margin-bottom: 2rem;">
                    👤 New Employee Registration
                </h2>
                <p style="text-align: center; color: var(--finsolve-dark-grey); margin-bottom: 2rem;">
                    Join the FinSolve Technologies AI Assistant platform
                </p>
            </div>
            """, unsafe_allow_html=True)

            # Registration success/error messages
            if hasattr(st.session_state, 'registration_message'):
                if st.session_state.registration_success:
                    st.success(st.session_state.registration_message)
                else:
                    st.error(st.session_state.registration_message)

            with st.form("registration_form"):
                st.markdown("### 📝 Personal Information")

                col1, col2 = st.columns(2)
                with col1:
                    first_name = st.text_input(
                        "First Name *",
                        placeholder="Enter your first name",
                        help="Your legal first name"
                    )

                with col2:
                    last_name = st.text_input(
                        "Last Name *",
                        placeholder="Enter your last name",
                        help="Your legal last name"
                    )

                email = st.text_input(
                    "Email Address *",
                    placeholder="your.name@company.com",
                    help="Your company email address (will be used as username)"
                )

                phone = st.text_input(
                    "Phone Number",
                    placeholder="+1 (555) 123-4567",
                    help="Your contact phone number (optional)"
                )

                st.markdown("### 🏢 Employment Information")

                col1, col2 = st.columns(2)
                with col1:
                    department = st.selectbox(
                        "Department *",
                        ["Engineering", "Finance", "HR", "Marketing", "Sales", "Customer Support",
                         "IT Security", "Data Analytics", "R&D", "QA", "Operations", "Legal", "Executive"],
                        help="Select your primary department"
                    )

                with col2:
                    role = st.selectbox(
                        "Role Level *",
                        ["Employee", "Manager", "Director", "C-Level Executive"],
                        help="Select your role level for access permissions"
                    )

                job_title = st.text_input(
                    "Job Title *",
                    placeholder="e.g., Senior Software Engineer",
                    help="Your official job title"
                )

                employee_id = st.text_input(
                    "Employee ID",
                    placeholder="EMP-2024-001",
                    help="Your employee ID (if available)"
                )

                manager_email = st.text_input(
                    "Manager Email",
                    placeholder="manager@company.com",
                    help="Your direct manager's email (for approval)"
                )

                st.markdown("### 🔐 Access Requirements")

                access_reason = st.text_area(
                    "Reason for Access *",
                    placeholder="Describe why you need access to the FinSolve AI Assistant...",
                    height=100,
                    help="Explain your business need for system access"
                )

                # Terms and conditions
                terms_accepted = st.checkbox(
                    "I agree to the Terms of Service and Privacy Policy *",
                    help="You must accept the terms to register"
                )

                # Submit button
                col1, col2 = st.columns(2)

                with col1:
                    register_button = st.form_submit_button(
                        "📝 Register Account" if not st.session_state.loading else "⏳ Processing...",
                        use_container_width=True,
                        type="primary",
                        disabled=st.session_state.loading
                    )

                with col2:
                    clear_button = st.form_submit_button(
                        "🗑️ Clear Form",
                        use_container_width=True
                    )

                if clear_button:
                    st.rerun()

                if register_button and not st.session_state.loading:
                    # Validate required fields
                    if not all([first_name, last_name, email, department, role, job_title, access_reason, terms_accepted]):
                        st.error("⚠️ Please fill in all required fields (*) and accept the terms.")
                    elif not self.validate_email(email):
                        st.error("⚠️ Please enter a valid email address.")
                    else:
                        # Process registration
                        self.register_user({
                            'first_name': first_name,
                            'last_name': last_name,
                            'email': email,
                            'phone': phone,
                            'department': department,
                            'role': role,
                            'job_title': job_title,
                            'employee_id': employee_id,
                            'manager_email': manager_email,
                            'access_reason': access_reason
                        })

    def validate_email(self, email: str) -> bool:
        """Validate email format."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def register_user(self, user_data: dict):
        """Register a new user and send welcome email."""
        try:
            st.session_state.loading = True

            with st.spinner("📝 Creating your account..."):
                # Call registration API
                response = self.api_client.post(
                    "/auth/register",
                    json=user_data
                )

                if response and response.status_code == 201:
                    data = response.json()

                    # Send welcome email with credentials
                    self.send_welcome_email(user_data, data.get('temporary_password'))

                    st.session_state.registration_success = True
                    st.session_state.registration_message = f"""
                    ✅ Registration successful!

                    📧 Welcome email sent to {user_data['email']} with your login credentials.

                    🔐 Please check your email for your temporary password and login instructions.

                    ⏰ Your account will be activated within 24 hours.
                    """

                    time.sleep(3)
                    st.rerun()

                else:
                    error_msg = "Registration failed. Please try again."
                    if response:
                        try:
                            error_data = response.json()
                            error_msg = error_data.get('detail', error_msg)
                        except:
                            pass

                    st.session_state.registration_success = False
                    st.session_state.registration_message = f"❌ {error_msg}"

        except Exception as e:
            st.session_state.registration_success = False
            st.session_state.registration_message = f"🔌 Connection error: {str(e)}"
            logger.error(f"Registration error: {e}")
        finally:
            st.session_state.loading = False

    def send_welcome_email(self, user_data: dict, temp_password: str):
        """Send welcome email with login credentials."""
        try:
            # Check if email service is available
            if email_service is None:
                logger.error("Email service not available")
                return

            full_name = f"{user_data['first_name']} {user_data['last_name']}"

            # Create welcome email data
            welcome_data = {
                "welcome_type": "New Employee Registration",
                "full_name": full_name,
                "email": user_data['email'],
                "department": user_data['department'],
                "role": user_data['role'],
                "job_title": user_data['job_title'],
                "temporary_password": temp_password,
                "login_url": "http://localhost:8501",
                "support_email": "keyegon@gmail.com",
                "registration_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            # Send welcome email
            email_service.send_email(
                to_emails=[user_data['email']],
                subject="🎉 Welcome to FinSolve AI Assistant - Your Account is Ready!",
                body=self.generate_welcome_email_text(welcome_data),
                html_body=self.generate_welcome_email_html(welcome_data)
            )

            # Send notification to admin
            email_service.send_notification(
                recipient="keyegon@gmail.com",
                notification_type="info",
                data={
                    "event": "New User Registration",
                    "user_name": full_name,
                    "user_email": user_data['email'],
                    "department": user_data['department'],
                    "role": user_data['role'],
                    "job_title": user_data['job_title'],
                    "access_reason": user_data['access_reason']
                }
            )

        except Exception as e:
            logger.error(f"Failed to send welcome email: {str(e)}")

    def generate_welcome_email_text(self, data: dict) -> str:
        """Generate plain text welcome email."""
        return f"""
Welcome to FinSolve Technologies AI Assistant!

Dear {data['full_name']},

Congratulations! Your account has been successfully created for the FinSolve AI Assistant platform.

Account Details:
- Name: {data['full_name']}
- Email: {data['email']}
- Department: {data['department']}
- Role: {data['role']}
- Job Title: {data['job_title']}

Login Credentials:
- Username: {data['email']}
- Temporary Password: {data['temporary_password']}
- Login URL: {data['login_url']}

Important Security Notes:
1. Please change your password after your first login
2. Keep your credentials secure and confidential
3. Your account will be activated within 24 hours
4. Contact support if you experience any issues

Getting Started:
1. Visit the login page: {data['login_url']}
2. Use your email as username
3. Enter the temporary password provided above
4. Follow the prompts to set up your new password
5. Explore the AI Assistant features for your department

For support or questions, contact:
Dr. Erick K. Yegon
Email: {data['support_email']}

Welcome to the team!

Best regards,
FinSolve Technologies AI Assistant Team
Developed by Dr. Erick K. Yegon
        """

    def generate_welcome_email_html(self, data: dict) -> str:
        """Generate HTML welcome email."""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Welcome to FinSolve AI Assistant</title>
</head>
<body style="font-family: 'Roboto', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #0D1B2A 0%, #1a2332 100%); padding: 30px; border-radius: 12px; text-align: center; margin-bottom: 30px;">
        <h1 style="color: #00F5D4; margin: 0; font-size: 28px;">🎉 Welcome to FinSolve!</h1>
        <p style="color: #FFFFFF; margin: 10px 0 0 0; font-size: 18px;">AI Assistant Platform</p>
    </div>

    <div style="background: #f8f9fa; padding: 25px; border-radius: 12px; margin-bottom: 20px;">
        <h2 style="color: #0D1B2A; margin-top: 0;">Dear {data['full_name']},</h2>
        <p>Congratulations! Your account has been successfully created for the <strong>FinSolve AI Assistant</strong> platform.</p>

        <div style="background: #e8f5e8; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <h3 style="color: #00F5D4; margin-top: 0;">👤 Account Details</h3>
            <ul style="margin: 0; padding-left: 20px;">
                <li><strong>Name:</strong> {data['full_name']}</li>
                <li><strong>Email:</strong> {data['email']}</li>
                <li><strong>Department:</strong> {data['department']}</li>
                <li><strong>Role:</strong> {data['role']}</li>
                <li><strong>Job Title:</strong> {data['job_title']}</li>
            </ul>
        </div>

        <div style="background: #fff3cd; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #ffc107;">
            <h3 style="color: #856404; margin-top: 0;">🔐 Login Credentials</h3>
            <p style="margin: 5px 0;"><strong>Username:</strong> {data['email']}</p>
            <p style="margin: 5px 0;"><strong>Temporary Password:</strong> <code style="background: #f8f9fa; padding: 2px 6px; border-radius: 4px; font-family: monospace;">{data['temporary_password']}</code></p>
            <p style="margin: 5px 0;"><strong>Login URL:</strong> <a href="{data['login_url']}" style="color: #00F5D4;">{data['login_url']}</a></p>
        </div>

        <div style="background: #d1ecf1; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #bee5eb;">
            <h3 style="color: #0c5460; margin-top: 0;">🔒 Important Security Notes</h3>
            <ol style="margin: 0; padding-left: 20px;">
                <li>Please change your password after your first login</li>
                <li>Keep your credentials secure and confidential</li>
                <li>Your account will be activated within 24 hours</li>
                <li>Contact support if you experience any issues</li>
            </ol>
        </div>

        <div style="background: linear-gradient(135deg, #00F5D4 0%, #00d4b8 100%); padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center;">
            <h3 style="margin: 0 0 10px 0; color: #0D1B2A;">🚀 Getting Started</h3>
            <ol style="margin: 0; padding-left: 20px; text-align: left; color: #0D1B2A;">
                <li>Visit the login page: <a href="{data['login_url']}" style="color: #0D1B2A; font-weight: bold;">{data['login_url']}</a></li>
                <li>Use your email as username</li>
                <li>Enter the temporary password provided above</li>
                <li>Follow the prompts to set up your new password</li>
                <li>Explore the AI Assistant features for your department</li>
            </ol>
        </div>
    </div>

    <div style="background: #0D1B2A; padding: 20px; border-radius: 8px; text-align: center; color: #FFFFFF;">
        <p style="margin: 0; font-size: 16px;">For support or questions, contact:</p>
        <p style="margin: 5px 0 0 0; color: #00F5D4;">
            <strong>Dr. Erick K. Yegon</strong><br>
            <a href="mailto:{data['support_email']}" style="color: #00F5D4;">{data['support_email']}</a>
        </p>
        <hr style="border: none; border-top: 1px solid #00F5D4; margin: 15px 0;">
        <p style="margin: 0; font-size: 14px;">
            Welcome to the team!<br>
            <strong>FinSolve Technologies AI Assistant</strong><br>
            Developed by Dr. Erick K. Yegon
        </p>
    </div>
</body>
</html>
        """

    def main_chat_interface(self):
        """Display enhanced main chat interface."""
        user = st.session_state.user_info
        role_config = ROLE_CONFIG.get(user['role'].lower(), ROLE_CONFIG['employee'])
        
        # Enhanced header with user context
        self.display_header(
            f"Welcome, {user['full_name'].split()[0]}! 👋",
            f"{role_config['icon']} {user['role'].replace('_', ' ').title()} • {user.get('department', 'General')} Department"
        )
        
        # Analytics dashboard
        if st.session_state.chat_history:
            self.display_user_analytics()
        
        # Main content area with sidebar
        main_col, _ = st.columns([3, 1])
        
        with main_col:
            # Check if inquiry form should be displayed
            if hasattr(st.session_state, 'show_inquiry_form') and st.session_state.show_inquiry_form:
                self.display_inquiry_form()
            # Check if dashboard should be displayed
            elif hasattr(st.session_state, 'show_dashboard') and st.session_state.show_dashboard:
                dashboard_type = st.session_state.show_dashboard
                user_role = st.session_state.user_info.get('role', 'employee')

                # Display the requested dashboard
                self.display_dashboard(dashboard_type, user_role)

                # Add a button to return to chat
                if st.button("💬 Return to Chat", type="secondary"):
                    del st.session_state.show_dashboard
                    st.rerun()
            else:
                # Regular chat interface
                # Chat container
                st.markdown('<div class="chat-container">', unsafe_allow_html=True)

                # Welcome message or chat history
                if not st.session_state.chat_history:
                    self.display_welcome_message()
                else:
                    for message in st.session_state.chat_history:
                        self.display_chat_message(message)

                st.markdown('</div>', unsafe_allow_html=True)

                # Message input
                self.display_message_input()
        
        # Enhanced sidebar
        self.display_enhanced_sidebar()
    
    def run(self):
        """Main application runner with enhanced error handling."""
        try:
            if not st.session_state.authenticated:
                self.login_page()
            else:
                self.main_chat_interface()
        except Exception as e:
            logger.error(f"Application error: {e}")
            st.error("🔧 Application error occurred. Please refresh the page.")
            
            # Debug info for development
            if st.secrets.get("debug_mode", False):
                st.exception(e)

# ============================
# APPLICATION ENTRY POINT
# ============================

if __name__ == "__main__":
    try:
        app = FinSolveAIAssistant()
        app.run()
    except Exception as e:
        st.error("🚫 Failed to initialize application. Please refresh the page.")
        logger.error(f"Initialization error: {e}")