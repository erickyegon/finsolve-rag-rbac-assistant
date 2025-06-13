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

# Enhanced FinSolve Brand Constants with WCAG Compliant Colors
FINSOLVE_BRAND = {
    "colors": {
        # Primary Brand Colors (WCAG AA Compliant)
        "deep_blue": "#0D1B2A",           # Primary brand color
        "teal": "#00F5D4",               # Secondary brand color
        "white": "#FFFFFF",              # Pure white
        "black": "#000000",              # Pure black for high contrast

        # Enhanced Grey Scale (Better contrast ratios)
        "grey_50": "#F8FAFC",           # Lightest grey
        "grey_100": "#F1F5F9",          # Very light grey
        "grey_200": "#E2E8F0",          # Light grey
        "grey_300": "#CBD5E1",          # Medium light grey
        "grey_400": "#94A3B8",          # Medium grey
        "grey_500": "#64748B",          # Base grey
        "grey_600": "#475569",          # Medium dark grey
        "grey_700": "#334155",          # Dark grey
        "grey_800": "#1E293B",          # Very dark grey
        "grey_900": "#0F172A",          # Darkest grey

        # Status Colors (WCAG AA Compliant)
        "success": "#059669",           # Green (4.5:1 contrast)
        "success_light": "#D1FAE5",     # Light green background
        "warning": "#D97706",           # Orange (4.5:1 contrast)
        "warning_light": "#FEF3C7",     # Light orange background
        "error": "#DC2626",             # Red (4.5:1 contrast)
        "error_light": "#FEE2E2",       # Light red background
        "info": "#2563EB",              # Blue (4.5:1 contrast)
        "info_light": "#DBEAFE",        # Light blue background

        # Executive Colors (Gold theme for C-level)
        "gold": "#F59E0B",              # Executive gold
        "gold_light": "#FEF3C7",        # Light gold background
        "gold_dark": "#D97706",         # Dark gold

        # Interactive Colors
        "primary": "#0D1B2A",           # Primary buttons
        "primary_hover": "#1E293B",     # Primary hover state
        "secondary": "#00F5D4",         # Secondary buttons
        "secondary_hover": "#00D4B8",   # Secondary hover state

        # Background Colors
        "bg_primary": "#FFFFFF",        # Main background
        "bg_secondary": "#F8FAFC",      # Secondary background
        "bg_tertiary": "#F1F5F9",       # Tertiary background
        "bg_overlay": "rgba(15, 23, 42, 0.8)",  # Modal overlay

        # Border Colors
        "border_light": "#E2E8F0",      # Light borders
        "border_medium": "#CBD5E1",     # Medium borders
        "border_dark": "#94A3B8",       # Dark borders
        "border_focus": "#00F5D4",      # Focus state borders
    },
    "fonts": {
        "primary": "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        "heading": "'Poppins', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        "mono": "'JetBrains Mono', 'Fira Code', 'Consolas', monospace"
    },
    "typography": {
        "scale": {
            "xs": "0.75rem",    # 12px
            "sm": "0.875rem",   # 14px
            "base": "1rem",     # 16px
            "lg": "1.125rem",   # 18px
            "xl": "1.25rem",    # 20px
            "2xl": "1.5rem",    # 24px
            "3xl": "1.875rem",  # 30px
            "4xl": "2.25rem",   # 36px
            "5xl": "3rem",      # 48px
        },
        "weight": {
            "light": "300",
            "normal": "400",
            "medium": "500",
            "semibold": "600",
            "bold": "700",
            "extrabold": "800"
        },
        "line_height": {
            "tight": "1.25",
            "normal": "1.5",
            "relaxed": "1.75"
        }
    },
    "gradients": {
        "primary": "linear-gradient(135deg, #0D1B2A 0%, #1E293B 100%)",
        "secondary": "linear-gradient(135deg, #00F5D4 0%, #00D4B8 100%)",
        "background": "linear-gradient(135deg, #F8FAFC 0%, #F1F5F9 100%)",
        "executive": "linear-gradient(135deg, #F59E0B 0%, #D97706 100%)",
        "card": "linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 100%)",
        "overlay": "linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(30, 41, 59, 0.8) 100%)"
    },
    "shadows": {
        "xs": "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
        "sm": "0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)",
        "md": "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
        "lg": "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)",
        "xl": "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)",
        "2xl": "0 25px 50px -12px rgba(0, 0, 0, 0.25)",
        "brand": "0 10px 25px -5px rgba(0, 245, 212, 0.2), 0 4px 6px -2px rgba(0, 245, 212, 0.1)",
        "executive": "0 10px 25px -5px rgba(245, 158, 11, 0.3), 0 4px 6px -2px rgba(245, 158, 11, 0.1)"
    },
    "spacing": {
        "xs": "0.25rem",    # 4px
        "sm": "0.5rem",     # 8px
        "md": "1rem",       # 16px
        "lg": "1.5rem",     # 24px
        "xl": "2rem",       # 32px
        "2xl": "3rem",      # 48px
        "3xl": "4rem",      # 64px
    },
    "border_radius": {
        "sm": "0.375rem",   # 6px
        "md": "0.5rem",     # 8px
        "lg": "0.75rem",    # 12px
        "xl": "1rem",       # 16px
        "2xl": "1.5rem",    # 24px
        "full": "9999px"
    }
}

# Enhanced Role Configuration with Executive Styling
ROLE_CONFIG = {
    # C-Level Executives (Gold theme)
    "ceo": {
        "icon": "👑",
        "color": FINSOLVE_BRAND["colors"]["gold"],
        "bg_color": FINSOLVE_BRAND["colors"]["gold_light"],
        "priority": 1,
        "title": "Chief Executive Officer",
        "badge": "EXECUTIVE",
        "gradient": FINSOLVE_BRAND["gradients"]["executive"],
        "shadow": FINSOLVE_BRAND["shadows"]["executive"]
    },
    "cfo": {
        "icon": "💰",
        "color": FINSOLVE_BRAND["colors"]["gold"],
        "bg_color": FINSOLVE_BRAND["colors"]["gold_light"],
        "priority": 1,
        "title": "Chief Financial Officer",
        "badge": "EXECUTIVE",
        "gradient": FINSOLVE_BRAND["gradients"]["executive"],
        "shadow": FINSOLVE_BRAND["shadows"]["executive"]
    },
    "cto": {
        "icon": "🔧",
        "color": FINSOLVE_BRAND["colors"]["gold"],
        "bg_color": FINSOLVE_BRAND["colors"]["gold_light"],
        "priority": 1,
        "title": "Chief Technology Officer",
        "badge": "EXECUTIVE",
        "gradient": FINSOLVE_BRAND["gradients"]["executive"],
        "shadow": FINSOLVE_BRAND["shadows"]["executive"]
    },
    "chro": {
        "icon": "👥",
        "color": FINSOLVE_BRAND["colors"]["gold"],
        "bg_color": FINSOLVE_BRAND["colors"]["gold_light"],
        "priority": 1,
        "title": "Chief Human Resources Officer",
        "badge": "EXECUTIVE",
        "gradient": FINSOLVE_BRAND["gradients"]["executive"],
        "shadow": FINSOLVE_BRAND["shadows"]["executive"]
    },

    # VP Level (Premium theme)
    "vp_marketing": {
        "icon": "📈",
        "color": FINSOLVE_BRAND["colors"]["primary"],
        "bg_color": FINSOLVE_BRAND["colors"]["info_light"],
        "priority": 2,
        "title": "VP Marketing",
        "badge": "LEADERSHIP",
        "gradient": FINSOLVE_BRAND["gradients"]["primary"],
        "shadow": FINSOLVE_BRAND["shadows"]["brand"]
    },

    # System Administration
    "system_admin": {
        "icon": "🔧",
        "color": FINSOLVE_BRAND["colors"]["error"],
        "bg_color": FINSOLVE_BRAND["colors"]["error_light"],
        "priority": 2,
        "title": "System Administrator",
        "badge": "ADMIN",
        "gradient": "linear-gradient(135deg, #DC2626 0%, #B91C1C 100%)",
        "shadow": FINSOLVE_BRAND["shadows"]["lg"]
    },

    # Department Heads
    "hr": {
        "icon": "👥",
        "color": FINSOLVE_BRAND["colors"]["info"],
        "bg_color": FINSOLVE_BRAND["colors"]["info_light"],
        "priority": 3,
        "title": "Human Resources",
        "badge": "DEPARTMENT",
        "gradient": "linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%)",
        "shadow": FINSOLVE_BRAND["shadows"]["md"]
    },
    "finance": {
        "icon": "💰",
        "color": FINSOLVE_BRAND["colors"]["success"],
        "bg_color": FINSOLVE_BRAND["colors"]["success_light"],
        "priority": 3,
        "title": "Finance",
        "badge": "DEPARTMENT",
        "gradient": "linear-gradient(135deg, #059669 0%, #047857 100%)",
        "shadow": FINSOLVE_BRAND["shadows"]["md"]
    },
    "marketing": {
        "icon": "📈",
        "color": FINSOLVE_BRAND["colors"]["warning"],
        "bg_color": FINSOLVE_BRAND["colors"]["warning_light"],
        "priority": 3,
        "title": "Marketing",
        "badge": "DEPARTMENT",
        "gradient": "linear-gradient(135deg, #D97706 0%, #B45309 100%)",
        "shadow": FINSOLVE_BRAND["shadows"]["md"]
    },
    "engineering": {
        "icon": "⚙️",
        "color": FINSOLVE_BRAND["colors"]["secondary"],
        "bg_color": FINSOLVE_BRAND["colors"]["bg_tertiary"],
        "priority": 3,
        "title": "Engineering",
        "badge": "DEPARTMENT",
        "gradient": FINSOLVE_BRAND["gradients"]["secondary"],
        "shadow": FINSOLVE_BRAND["shadows"]["brand"]
    },

    # General Employees
    "employee": {
        "icon": "👤",
        "color": FINSOLVE_BRAND["colors"]["grey_600"],
        "bg_color": FINSOLVE_BRAND["colors"]["grey_100"],
        "priority": 4,
        "title": "Employee",
        "badge": "STAFF",
        "gradient": "linear-gradient(135deg, #64748B 0%, #475569 100%)",
        "shadow": FINSOLVE_BRAND["shadows"]["sm"]
    }
}

# ============================
# ENHANCED CSS STYLING
# ============================

def get_enhanced_css() -> str:
    """Generate enhanced CSS with modern design system and accessibility features."""
    return f"""
    <style>
        /* Import Enhanced Fonts for Better Readability */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Poppins:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@300;400;500;600&display=swap');

        /* Modern CSS Custom Properties Design System */
        :root {{
            /* Brand Colors */
            --color-primary: {FINSOLVE_BRAND["colors"]["deep_blue"]};
            --color-secondary: {FINSOLVE_BRAND["colors"]["teal"]};
            --color-white: {FINSOLVE_BRAND["colors"]["white"]};
            --color-black: {FINSOLVE_BRAND["colors"]["black"]};

            /* Grey Scale */
            --color-grey-50: {FINSOLVE_BRAND["colors"]["grey_50"]};
            --color-grey-100: {FINSOLVE_BRAND["colors"]["grey_100"]};
            --color-grey-200: {FINSOLVE_BRAND["colors"]["grey_200"]};
            --color-grey-300: {FINSOLVE_BRAND["colors"]["grey_300"]};
            --color-grey-400: {FINSOLVE_BRAND["colors"]["grey_400"]};
            --color-grey-500: {FINSOLVE_BRAND["colors"]["grey_500"]};
            --color-grey-600: {FINSOLVE_BRAND["colors"]["grey_600"]};
            --color-grey-700: {FINSOLVE_BRAND["colors"]["grey_700"]};
            --color-grey-800: {FINSOLVE_BRAND["colors"]["grey_800"]};
            --color-grey-900: {FINSOLVE_BRAND["colors"]["grey_900"]};

            /* Status Colors */
            --color-success: {FINSOLVE_BRAND["colors"]["success"]};
            --color-success-light: {FINSOLVE_BRAND["colors"]["success_light"]};
            --color-warning: {FINSOLVE_BRAND["colors"]["warning"]};
            --color-warning-light: {FINSOLVE_BRAND["colors"]["warning_light"]};
            --color-error: {FINSOLVE_BRAND["colors"]["error"]};
            --color-error-light: {FINSOLVE_BRAND["colors"]["error_light"]};
            --color-info: {FINSOLVE_BRAND["colors"]["info"]};
            --color-info-light: {FINSOLVE_BRAND["colors"]["info_light"]};

            /* Executive Colors */
            --color-gold: {FINSOLVE_BRAND["colors"]["gold"]};
            --color-gold-light: {FINSOLVE_BRAND["colors"]["gold_light"]};
            --color-gold-dark: {FINSOLVE_BRAND["colors"]["gold_dark"]};

            /* Interactive Colors */
            --color-primary-hover: {FINSOLVE_BRAND["colors"]["primary_hover"]};
            --color-secondary-hover: {FINSOLVE_BRAND["colors"]["secondary_hover"]};

            /* Background Colors */
            --bg-primary: {FINSOLVE_BRAND["colors"]["bg_primary"]};
            --bg-secondary: {FINSOLVE_BRAND["colors"]["bg_secondary"]};
            --bg-tertiary: {FINSOLVE_BRAND["colors"]["bg_tertiary"]};
            --bg-overlay: {FINSOLVE_BRAND["colors"]["bg_overlay"]};

            /* Border Colors */
            --border-light: {FINSOLVE_BRAND["colors"]["border_light"]};
            --border-medium: {FINSOLVE_BRAND["colors"]["border_medium"]};
            --border-dark: {FINSOLVE_BRAND["colors"]["border_dark"]};
            --border-focus: {FINSOLVE_BRAND["colors"]["border_focus"]};

            /* Typography */
            --font-primary: {FINSOLVE_BRAND["fonts"]["primary"]};
            --font-heading: {FINSOLVE_BRAND["fonts"]["heading"]};
            --font-mono: {FINSOLVE_BRAND["fonts"]["mono"]};

            /* Font Sizes */
            --text-xs: {FINSOLVE_BRAND["typography"]["scale"]["xs"]};
            --text-sm: {FINSOLVE_BRAND["typography"]["scale"]["sm"]};
            --text-base: {FINSOLVE_BRAND["typography"]["scale"]["base"]};
            --text-lg: {FINSOLVE_BRAND["typography"]["scale"]["lg"]};
            --text-xl: {FINSOLVE_BRAND["typography"]["scale"]["xl"]};
            --text-2xl: {FINSOLVE_BRAND["typography"]["scale"]["2xl"]};
            --text-3xl: {FINSOLVE_BRAND["typography"]["scale"]["3xl"]};
            --text-4xl: {FINSOLVE_BRAND["typography"]["scale"]["4xl"]};
            --text-5xl: {FINSOLVE_BRAND["typography"]["scale"]["5xl"]};

            /* Font Weights */
            --font-light: {FINSOLVE_BRAND["typography"]["weight"]["light"]};
            --font-normal: {FINSOLVE_BRAND["typography"]["weight"]["normal"]};
            --font-medium: {FINSOLVE_BRAND["typography"]["weight"]["medium"]};
            --font-semibold: {FINSOLVE_BRAND["typography"]["weight"]["semibold"]};
            --font-bold: {FINSOLVE_BRAND["typography"]["weight"]["bold"]};
            --font-extrabold: {FINSOLVE_BRAND["typography"]["weight"]["extrabold"]};

            /* Line Heights */
            --leading-tight: {FINSOLVE_BRAND["typography"]["line_height"]["tight"]};
            --leading-normal: {FINSOLVE_BRAND["typography"]["line_height"]["normal"]};
            --leading-relaxed: {FINSOLVE_BRAND["typography"]["line_height"]["relaxed"]};

            /* Gradients */
            --gradient-primary: {FINSOLVE_BRAND["gradients"]["primary"]};
            --gradient-secondary: {FINSOLVE_BRAND["gradients"]["secondary"]};
            --gradient-background: {FINSOLVE_BRAND["gradients"]["background"]};
            --gradient-executive: {FINSOLVE_BRAND["gradients"]["executive"]};
            --gradient-card: {FINSOLVE_BRAND["gradients"]["card"]};
            --gradient-overlay: {FINSOLVE_BRAND["gradients"]["overlay"]};

            /* Shadows */
            --shadow-xs: {FINSOLVE_BRAND["shadows"]["xs"]};
            --shadow-sm: {FINSOLVE_BRAND["shadows"]["sm"]};
            --shadow-md: {FINSOLVE_BRAND["shadows"]["md"]};
            --shadow-lg: {FINSOLVE_BRAND["shadows"]["lg"]};
            --shadow-xl: {FINSOLVE_BRAND["shadows"]["xl"]};
            --shadow-2xl: {FINSOLVE_BRAND["shadows"]["2xl"]};
            --shadow-brand: {FINSOLVE_BRAND["shadows"]["brand"]};
            --shadow-executive: {FINSOLVE_BRAND["shadows"]["executive"]};

            /* Spacing */
            --space-xs: {FINSOLVE_BRAND["spacing"]["xs"]};
            --space-sm: {FINSOLVE_BRAND["spacing"]["sm"]};
            --space-md: {FINSOLVE_BRAND["spacing"]["md"]};
            --space-lg: {FINSOLVE_BRAND["spacing"]["lg"]};
            --space-xl: {FINSOLVE_BRAND["spacing"]["xl"]};
            --space-2xl: {FINSOLVE_BRAND["spacing"]["2xl"]};
            --space-3xl: {FINSOLVE_BRAND["spacing"]["3xl"]};

            /* Border Radius */
            --radius-sm: {FINSOLVE_BRAND["border_radius"]["sm"]};
            --radius-md: {FINSOLVE_BRAND["border_radius"]["md"]};
            --radius-lg: {FINSOLVE_BRAND["border_radius"]["lg"]};
            --radius-xl: {FINSOLVE_BRAND["border_radius"]["xl"]};
            --radius-2xl: {FINSOLVE_BRAND["border_radius"]["2xl"]};
            --radius-full: {FINSOLVE_BRAND["border_radius"]["full"]};

            /* Transitions */
            --transition-fast: 0.15s cubic-bezier(0.4, 0, 0.2, 1);
            --transition-normal: 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            --transition-slow: 0.5s cubic-bezier(0.4, 0, 0.2, 1);

            /* Z-Index Scale */
            --z-dropdown: 1000;
            --z-sticky: 1020;
            --z-fixed: 1030;
            --z-modal-backdrop: 1040;
            --z-modal: 1050;
            --z-popover: 1060;
            --z-tooltip: 1070;
        }}

        /* Modern CSS Reset */
        *, *::before, *::after {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        html {{
            font-size: 16px;
            scroll-behavior: smooth;
        }}

        body {{
            font-family: var(--font-primary);
            font-size: var(--text-base);
            line-height: var(--leading-normal);
            color: var(--color-grey-900);
            background: var(--bg-primary);
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }}

        /* Enhanced Streamlit App Base */
        .stApp {{
            font-family: var(--font-primary) !important;
            background: var(--gradient-background) !important;
            color: var(--color-grey-900) !important;
            font-size: var(--text-base) !important;
            line-height: var(--leading-normal) !important;
            min-height: 100vh;
        }}

        /* Remove Streamlit Branding and Clutter */
        #MainMenu, footer, header, .stDeployButton,
        div[data-testid="stDecoration"],
        div[data-testid="stStatusWidget"],
        .stActionButton {{
            visibility: hidden !important;
            display: none !important;
            height: 0 !important;
        }}

        /* Enhanced Layout System */
        .main > div {{
            padding-top: 0 !important;
            padding-bottom: 0 !important;
        }}

        .main .block-container {{
            padding: var(--space-lg) var(--space-md) !important;
            margin-top: 0 !important;
            max-width: 1400px;
            width: 100%;
        }}

        header[data-testid="stHeader"] {{
            height: 0 !important;
            display: none !important;
        }}

        div[data-testid="stToolbar"] {{
            display: none !important;
        }}

        /* Enhanced Sidebar */
        .css-1d391kg, section[data-testid="stSidebar"] {{
            background: var(--bg-primary) !important;
            border-right: 2px solid var(--border-light) !important;
            box-shadow: var(--shadow-lg) !important;
            backdrop-filter: blur(20px) !important;
        }}

        .css-1d391kg .css-1v0mbdj {{
            padding: var(--space-lg) !important;
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

        /* Executive Dashboard Metrics Cards */
        .metrics-container {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 1.5rem;
            margin: 2rem 0;
            padding: 0;
        }}

        .executive-metric-card {{
            background: rgba(255, 255, 255, 0.98);
            border-radius: var(--border-radius-large);
            padding: 2rem;
            box-shadow: var(--shadow-light);
            border: 1px solid rgba(0, 245, 212, 0.2);
            backdrop-filter: blur(10px);
            transition: var(--transition-normal);
            position: relative;
            overflow: hidden;
        }}

        .executive-metric-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: var(--gradient-secondary);
            border-radius: var(--border-radius-large) var(--border-radius-large) 0 0;
        }}

        .executive-metric-card:hover {{
            transform: translateY(-4px);
            box-shadow: var(--shadow-brand);
            border-color: var(--finsolve-teal);
        }}

        .metric-number {{
            font-size: 3.5rem;
            font-weight: 800;
            color: var(--finsolve-deep-blue);
            margin: 0;
            line-height: 1;
            font-family: var(--font-primary);
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
        }}

        .metric-title {{
            font-size: 0.875rem;
            font-weight: 600;
            color: var(--finsolve-dark-grey);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin: 1rem 0 0.5rem 0;
            font-family: var(--font-primary);
        }}

        .metric-status {{
            font-size: 0.9rem;
            font-weight: 500;
            margin-top: 0.5rem;
            padding: 0.3rem 0.8rem;
            border-radius: 15px;
            display: inline-block;
        }}

        .status-ready {{
            background: rgba(76, 175, 80, 0.1);
            color: var(--finsolve-success);
            border: 1px solid var(--finsolve-success);
        }}

        .status-high {{
            background: rgba(0, 245, 212, 0.1);
            color: var(--finsolve-teal);
            border: 1px solid var(--finsolve-teal);
        }}

        .status-active {{
            background: rgba(255, 152, 0, 0.1);
            color: var(--finsolve-warning);
            border: 1px solid var(--finsolve-warning);
        }}

        /* Executive Command Center */
        .executive-dashboard {{
            background: rgba(255, 255, 255, 0.98);
            border-radius: var(--border-radius-xl);
            padding: 3rem;
            margin: 2rem 0;
            box-shadow: var(--shadow-brand);
            border: 2px solid rgba(0, 245, 212, 0.3);
            backdrop-filter: blur(15px);
            position: relative;
            overflow: hidden;
        }}

        .executive-dashboard::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 6px;
            background: var(--gradient-secondary);
            border-radius: var(--border-radius-xl) var(--border-radius-xl) 0 0;
        }}

        .ceo-welcome {{
            font-size: 2.5rem;
            font-weight: 800;
            color: var(--finsolve-deep-blue);
            text-align: center;
            margin-bottom: 1rem;
            font-family: var(--font-primary);
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
        }}

        .ceo-subtitle {{
            font-size: 1.2rem;
            color: var(--finsolve-dark-grey);
            text-align: center;
            margin-bottom: 2rem;
            font-weight: 500;
            line-height: 1.5;
        }}

        /* Action Buttons */
        .action-buttons {{
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
            justify-content: center;
            margin: 2rem 0;
        }}

        .action-button {{
            background: var(--gradient-secondary);
            color: var(--finsolve-deep-blue);
            padding: 0.8rem 1.5rem;
            border-radius: 25px;
            font-weight: 600;
            text-decoration: none;
            transition: var(--transition-normal);
            box-shadow: var(--shadow-light);
            border: none;
            cursor: pointer;
            font-family: var(--font-primary);
            font-size: 0.9rem;
        }}

        .action-button:hover {{
            transform: translateY(-2px);
            box-shadow: var(--shadow-medium);
            background: linear-gradient(135deg, rgba(0, 245, 212, 0.9) 0%, var(--finsolve-teal) 100%);
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

        /* Enhanced Typography System */
        h1, h2, h3, h4, h5, h6 {{
            font-family: var(--font-heading) !important;
            font-weight: var(--font-semibold) !important;
            line-height: var(--leading-tight) !important;
            color: var(--color-grey-900) !important;
            margin-bottom: var(--space-md) !important;
        }}

        h1 {{ font-size: var(--text-4xl) !important; }}
        h2 {{ font-size: var(--text-3xl) !important; }}
        h3 {{ font-size: var(--text-2xl) !important; }}
        h4 {{ font-size: var(--text-xl) !important; }}
        h5 {{ font-size: var(--text-lg) !important; }}
        h6 {{ font-size: var(--text-base) !important; }}

        p, .stMarkdown p {{
            font-family: var(--font-primary) !important;
            font-size: var(--text-base) !important;
            line-height: var(--leading-normal) !important;
            color: var(--color-grey-700) !important;
            margin-bottom: var(--space-md) !important;
        }}

        /* Executive Badge System */
        .executive-badge {{
            display: inline-flex;
            align-items: center;
            gap: var(--space-xs);
            background: var(--gradient-executive);
            color: var(--color-white);
            padding: var(--space-xs) var(--space-md);
            border-radius: var(--radius-full);
            font-size: var(--text-xs);
            font-weight: var(--font-bold);
            text-transform: uppercase;
            letter-spacing: 0.1em;
            box-shadow: var(--shadow-executive);
            animation: pulse 2s infinite;
        }}

        .leadership-badge {{
            background: var(--gradient-primary);
            box-shadow: var(--shadow-brand);
        }}

        .department-badge {{
            background: var(--gradient-secondary);
            box-shadow: var(--shadow-md);
        }}

        .admin-badge {{
            background: linear-gradient(135deg, #DC2626 0%, #B91C1C 100%);
            box-shadow: var(--shadow-lg);
        }}

        .staff-badge {{
            background: linear-gradient(135deg, #64748B 0%, #475569 100%);
            box-shadow: var(--shadow-sm);
        }}

        /* Enhanced Card System with Hover Effects */
        .enhanced-card {{
            background: var(--gradient-card);
            border: 2px solid var(--border-light);
            border-radius: var(--radius-xl);
            padding: var(--space-xl);
            box-shadow: var(--shadow-md);
            transition: var(--transition-normal);
            position: relative;
            overflow: hidden;
        }}

        .enhanced-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: var(--gradient-secondary);
            border-radius: var(--radius-xl) var(--radius-xl) 0 0;
        }}

        .enhanced-card:hover {{
            transform: translateY(-4px);
            box-shadow: var(--shadow-xl);
            border-color: var(--border-focus);
        }}

        .enhanced-card.executive {{
            border-color: var(--color-gold);
            box-shadow: var(--shadow-executive);
        }}

        .enhanced-card.executive::before {{
            background: var(--gradient-executive);
        }}

        .enhanced-card.executive:hover {{
            box-shadow: var(--shadow-executive), var(--shadow-xl);
        }}

        /* Professional Button System */
        .btn-primary {{
            background: var(--gradient-primary);
            color: var(--color-white);
            border: none;
            border-radius: var(--radius-lg);
            padding: var(--space-md) var(--space-xl);
            font-family: var(--font-primary);
            font-size: var(--text-base);
            font-weight: var(--font-semibold);
            cursor: pointer;
            transition: var(--transition-normal);
            box-shadow: var(--shadow-md);
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: var(--space-sm);
        }}

        .btn-primary:hover {{
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg);
            background: var(--gradient-primary);
            filter: brightness(1.1);
        }}

        .btn-secondary {{
            background: var(--gradient-secondary);
            color: var(--color-primary);
            border: 2px solid var(--color-secondary);
        }}

        .btn-executive {{
            background: var(--gradient-executive);
            color: var(--color-white);
            box-shadow: var(--shadow-executive);
        }}

        .btn-executive:hover {{
            box-shadow: var(--shadow-executive), var(--shadow-lg);
        }}

        /* Enhanced Form Controls */
        .form-control {{
            width: 100%;
            padding: var(--space-md);
            border: 2px solid var(--border-medium);
            border-radius: var(--radius-lg);
            font-family: var(--font-primary);
            font-size: var(--text-base);
            background: var(--bg-primary);
            transition: var(--transition-normal);
        }}

        .form-control:focus {{
            outline: none;
            border-color: var(--border-focus);
            box-shadow: 0 0 0 3px rgba(0, 245, 212, 0.1);
        }}

        .form-label {{
            display: block;
            font-family: var(--font-heading);
            font-size: var(--text-sm);
            font-weight: var(--font-semibold);
            color: var(--color-grey-700);
            margin-bottom: var(--space-sm);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        /* Status Indicator System */
        .status-indicator {{
            display: inline-flex;
            align-items: center;
            gap: var(--space-xs);
            padding: var(--space-xs) var(--space-md);
            border-radius: var(--radius-full);
            font-size: var(--text-sm);
            font-weight: var(--font-medium);
            border: 1px solid;
        }}

        .status-success {{
            background: var(--color-success-light);
            color: var(--color-success);
            border-color: var(--color-success);
        }}

        .status-warning {{
            background: var(--color-warning-light);
            color: var(--color-warning);
            border-color: var(--color-warning);
        }}

        .status-error {{
            background: var(--color-error-light);
            color: var(--color-error);
            border-color: var(--color-error);
        }}

        .status-info {{
            background: var(--color-info-light);
            color: var(--color-info);
            border-color: var(--color-info);
        }}

        /* Accessibility Enhancements */
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

        /* Focus States for Keyboard Navigation */
        *:focus {{
            outline: 2px solid var(--border-focus);
            outline-offset: 2px;
        }}

        /* High Contrast Mode Support */
        @media (prefers-contrast: high) {{
            :root {{
                --color-grey-700: var(--color-black);
                --color-grey-600: var(--color-black);
                --border-light: var(--color-black);
                --border-medium: var(--color-black);
            }}
        }}

        /* Reduced Motion Support */
        @media (prefers-reduced-motion: reduce) {{
            *, *::before, *::after {{
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }}
        }}

        /* Dark Mode Support (Future Enhancement) */
        @media (prefers-color-scheme: dark) {{
            .stApp {{
                background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%) !important;
                color: var(--color-grey-100) !important;
            }}
        }}

        /* Responsive Design - Mobile First Approach */

        /* Mobile Styles (Default) */
        .finsolve-header {{
            padding: var(--space-lg) var(--space-md);
            margin-bottom: var(--space-lg);
        }}

        .header-title {{
            font-size: var(--text-3xl);
        }}

        .header-subtitle {{
            font-size: var(--text-base);
        }}

        .enhanced-card {{
            padding: var(--space-lg);
            margin-bottom: var(--space-lg);
        }}

        .user-message {{
            margin-left: 5%;
            margin-right: 0;
        }}

        .assistant-message {{
            margin-right: 5%;
            margin-left: 0;
        }}

        .metrics-container {{
            grid-template-columns: 1fr;
            gap: var(--space-lg);
        }}

        .action-buttons {{
            flex-direction: column;
            align-items: stretch;
        }}

        /* Tablet Styles */
        @media (min-width: 768px) {{
            .finsolve-header {{
                padding: var(--space-xl) var(--space-lg);
            }}

            .header-title {{
                font-size: var(--text-4xl);
            }}

            .header-subtitle {{
                font-size: var(--text-lg);
            }}

            .enhanced-card {{
                padding: var(--space-xl);
            }}

            .user-message {{
                margin-left: 10%;
            }}

            .assistant-message {{
                margin-right: 10%;
            }}

            .metrics-container {{
                grid-template-columns: repeat(2, 1fr);
            }}

            .action-buttons {{
                flex-direction: row;
                justify-content: center;
            }}
        }}

        /* Desktop Styles */
        @media (min-width: 1024px) {{
            .finsolve-header {{
                padding: var(--space-2xl) var(--space-xl);
            }}

            .header-title {{
                font-size: var(--text-5xl);
            }}

            .header-subtitle {{
                font-size: var(--text-xl);
            }}

            .enhanced-card {{
                padding: var(--space-2xl);
            }}

            .user-message {{
                margin-left: 15%;
            }}

            .assistant-message {{
                margin-right: 15%;
            }}

            .metrics-container {{
                grid-template-columns: repeat(3, 1fr);
            }}

            .main .block-container {{
                padding: var(--space-2xl) var(--space-xl) !important;
            }}
        }}

        /* Large Desktop Styles */
        @media (min-width: 1280px) {{
            .metrics-container {{
                grid-template-columns: repeat(4, 1fr);
            }}

            .main .block-container {{
                max-width: 1400px;
                margin: 0 auto;
            }}
        }}

        /* Ultra-wide Styles */
        @media (min-width: 1536px) {{
            .main .block-container {{
                max-width: 1600px;
            }}
        }}

        /* Print Styles */
        @media print {{
            .finsolve-header,
            .enhanced-card,
            .chat-message {{
                box-shadow: none !important;
                background: white !important;
                color: black !important;
            }}

            .action-buttons,
            .stButton {{
                display: none !important;
            }}
        }}

        /* Loading States and Animations */
        .loading-skeleton {{
            background: linear-gradient(90deg, var(--color-grey-200) 25%, var(--color-grey-100) 50%, var(--color-grey-200) 75%);
            background-size: 200% 100%;
            animation: loading 1.5s infinite;
        }}

        @keyframes loading {{
            0% {{ background-position: 200% 0; }}
            100% {{ background-position: -200% 0; }}
        }}

        .fade-in {{
            animation: fadeIn 0.5s ease-in-out;
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        .slide-in-left {{
            animation: slideInLeft 0.5s ease-out;
        }}

        @keyframes slideInLeft {{
            from {{ opacity: 0; transform: translateX(-30px); }}
            to {{ opacity: 1; transform: translateX(0); }}
        }}

        .slide-in-right {{
            animation: slideInRight 0.5s ease-out;
        }}

        @keyframes slideInRight {{
            from {{ opacity: 0; transform: translateX(30px); }}
            to {{ opacity: 1; transform: translateX(0); }}
        }}

        /* Enhanced Scrollbar Styling */
        ::-webkit-scrollbar {{
            width: 12px;
        }}

        ::-webkit-scrollbar-track {{
            background: var(--color-grey-100);
            border-radius: var(--radius-lg);
        }}

        ::-webkit-scrollbar-thumb {{
            background: var(--gradient-secondary);
            border-radius: var(--radius-lg);
            border: 2px solid var(--color-grey-100);
        }}

        ::-webkit-scrollbar-thumb:hover {{
            background: var(--gradient-primary);
        }}

        /* Custom Selection Styling */
        ::selection {{
            background: var(--color-secondary);
            color: var(--color-primary);
        }}

        ::-moz-selection {{
            background: var(--color-secondary);
            color: var(--color-primary);
        }}

        /* Enhanced Tooltip System */
        .tooltip {{
            position: relative;
            display: inline-block;
        }}

        .tooltip .tooltiptext {{
            visibility: hidden;
            width: 200px;
            background: var(--color-grey-900);
            color: var(--color-white);
            text-align: center;
            border-radius: var(--radius-md);
            padding: var(--space-sm);
            position: absolute;
            z-index: var(--z-tooltip);
            bottom: 125%;
            left: 50%;
            margin-left: -100px;
            opacity: 0;
            transition: var(--transition-normal);
            font-size: var(--text-sm);
        }}

        .tooltip .tooltiptext::after {{
            content: "";
            position: absolute;
            top: 100%;
            left: 50%;
            margin-left: -5px;
            border-width: 5px;
            border-style: solid;
            border-color: var(--color-grey-900) transparent transparent transparent;
        }}

        .tooltip:hover .tooltiptext {{
            visibility: visible;
            opacity: 1;
        }}
    </style>
    """

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

        /* CEO Executive Styling */
        .ceo-badge {{
            background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
            color: var(--finsolve-deep-blue);
            padding: 0.6rem 1.2rem;
            border-radius: 30px;
            font-weight: 700;
            font-size: 1rem;
            display: inline-block;
            box-shadow: 0 4px 15px rgba(255, 215, 0, 0.3);
            margin: 0.5rem 0;
            border: 2px solid #FFD700;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .ceo-header {{
            background: linear-gradient(135deg, var(--finsolve-deep-blue) 0%, #1a2332 100%);
            border: 3px solid var(--finsolve-teal);
            border-radius: 15px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            box-shadow: 0 8px 25px rgba(0, 245, 212, 0.2);
        }}

        .ceo-welcome {{
            color: var(--finsolve-teal);
            font-size: 1.8rem;
            font-weight: 700;
            text-align: center;
            margin-bottom: 0.5rem;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
            font-family: var(--font-primary);
        }}

        .ceo-subtitle {{
            color: white;
            font-size: 1.1rem;
            text-align: center;
            opacity: 0.9;
            font-family: var(--font-secondary);
        }}

        .executive-dashboard {{
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.98) 0%, rgba(248, 249, 250, 0.95) 100%);
            border: 2px solid var(--finsolve-teal);
            border-radius: 15px;
            padding: 2rem;
            margin: 1rem 0;
            box-shadow: 0 8px 25px rgba(0, 245, 212, 0.15);
        }}

        .executive-metric {{
            background: linear-gradient(135deg, var(--finsolve-deep-blue) 0%, #1a2332 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
            margin: 0.5rem;
            box-shadow: 0 4px 15px rgba(13, 27, 42, 0.3);
            border: 1px solid var(--finsolve-teal);
        }}

        .executive-metric-value {{
            font-size: 2.5rem;
            font-weight: 800;
            color: var(--finsolve-teal);
            margin-bottom: 0.5rem;
            font-family: var(--font-primary);
        }}

        .executive-metric-label {{
            font-size: 0.9rem;
            color: rgba(255, 255, 255, 0.8);
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
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

        # Remove system messages that shouldn't be shown to users
        system_phrases = [
            "Use this granular data to identify high-performing units and areas needing strategic focus.",
            "Would you like assistance with creating a framework for collecting or analyzing this segmented data",
            "or any specific insights into particular business units?",
            "Next Steps:",
            "Request or develop segmented quarterly reports for each business unit.",
            "Analyze unit-specific KPIs such as revenue, profit margins, and customer acquisition.",
            "Use this granular data to identify high-performing units and areas needing strategic focus."
        ]

        for phrase in system_phrases:
            content = content.replace(phrase, "")

        # Clean up extra whitespace and newlines
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        content = re.sub(r'\s+', ' ', content)

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
    
    def display_header(self, title: str, subtitle: str, user_role: str = None):
        """Display enhanced application header with executive styling."""
        # Determine if this is an executive user
        executive_roles = ["ceo", "cfo", "cto", "chro"]
        is_executive = user_role in executive_roles if user_role else False

        # Get role configuration
        role_config = ROLE_CONFIG.get(user_role, {}) if user_role else {}

        logo_base64 = self.get_logo_base64()

        # Executive badge
        badge_html = ""
        if is_executive and role_config:
            badge_html = f'''
            <span class="executive-badge">
                {role_config.get("icon", "👑")} {role_config.get("badge", "EXECUTIVE")}
            </span>
            '''
        elif user_role and role_config:
            badge_class = "leadership-badge" if role_config.get("priority") == 2 else "department-badge"
            if user_role == "system_admin":
                badge_class = "admin-badge"
            elif role_config.get("priority") == 4:
                badge_class = "staff-badge"

            badge_html = f'''
            <span class="{badge_class}">
                {role_config.get("icon", "👤")} {role_config.get("badge", "STAFF")}
            </span>
            '''

        # Header class
        header_class = "finsolve-header executive fade-in" if is_executive else "finsolve-header fade-in"

        st.markdown(f"""
        <div class="{header_class}">
            <div style="display: flex; align-items: center; justify-content: center; gap: 1.5rem; position: relative; z-index: 1;">
                <div class="header-logo">
                    {f'<img src="data:image/png;base64,{logo_base64}" style="width: 100%; height: 100%; object-fit: contain;" alt="FinSolve">' if logo_base64 else '<span style="color: var(--finsolve-deep-blue); font-weight: 800; font-size: 2rem;">FS</span>'}
                </div>
                <div style="text-align: center;">
                    <h1 class="header-title">{title} {badge_html}</h1>
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
            {"username": "ceo.finsolve", "password": "CEO123!", "role": "Chief Executive Officer", "icon": "👑"},
            {"username": "cfo.finsolve", "password": "CFO123!", "role": "Chief Financial Officer", "icon": "💰"},
            {"username": "cto.finsolve", "password": "CTO123!", "role": "Chief Technology Officer", "icon": "🔧"},
            {"username": "chro.finsolve", "password": "CHRO123!", "role": "Chief Human Resources Officer", "icon": "👥"},
            {"username": "vp.marketing", "password": "Marketing123!", "role": "VP Marketing", "icon": "📈"},
            {"username": "admin", "password": "Admin123!", "role": "System Administrator", "icon": "🔧"},
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
                    
                    # Add assistant response with structured content
                    st.session_state.chat_history.append({
                        "content": content,
                        "short_answer": data.get("short_answer"),
                        "detailed_response": data.get("detailed_response"),
                        "summary": data.get("summary"),
                        "message_type": "assistant",
                        "timestamp": data.get("timestamp", datetime.now().isoformat()),
                        "retrieved_documents": data.get("retrieved_documents", []),
                        "confidence_score": confidence,
                        "processing_time": data.get("processing_time"),
                        "visualization": data.get("visualization"),
                        "conversation_context": data.get("conversation_context")
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
        """Display enhanced chat message with structured response format."""
        is_user = message["message_type"] == "user"
        timestamp = self.message_renderer.format_timestamp(message.get("timestamp", ""))
        clean_content = self.message_renderer.clean_content(message["content"])

        if is_user:
            st.markdown(f"""
            <div class="chat-message slide-in-right fade-in">
                <div class="user-message enhanced-card">
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

            # Get structured response parts
            short_answer = message.get("short_answer", "")
            detailed_response = message.get("detailed_response", "")
            summary = message.get("summary", "")

            confidence_class = self.message_renderer.get_confidence_class(confidence)
            confidence_emoji = "🟢" if confidence > 0.8 else "🟡" if confidence > 0.6 else "🔴"

            # Display structured response with enhanced styling
            user_role = st.session_state.user_info.get('role', '').lower()
            is_executive = user_role in ["ceo", "cfo", "cto", "chro"]
            card_class = "enhanced-card executive" if is_executive else "enhanced-card"

            st.markdown(f"""
            <div class="chat-message slide-in-left fade-in">
                <div class="assistant-message {card_class}">
                    <div class="message-header">
                        <div style="display: flex; align-items: center; gap: 0.5rem;">
                            <strong style="color: var(--color-primary);">🤖 FinSolve AI</strong>
                            <span class="{confidence_class}">
                                {confidence_emoji} {confidence:.1%}
                            </span>
                        </div>
                        <span style="color: var(--color-grey-600);">{timestamp}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Display structured content in expandable sections
            if short_answer:
                st.markdown("### 🎯 Quick Answer")
                st.markdown(f"<div style='background: rgba(0, 245, 212, 0.1); padding: 1rem; border-radius: 8px; border-left: 4px solid #00F5D4; margin-bottom: 1rem;'>{self.message_renderer.clean_content(short_answer)}</div>", unsafe_allow_html=True)

            # Display detailed response (avoid duplication)
            if detailed_response and detailed_response.strip() and detailed_response != short_answer:
                with st.expander("📊 Detailed Analysis", expanded=True):
                    st.markdown(self.message_renderer.clean_content(detailed_response))
            elif clean_content and clean_content.strip() and clean_content != short_answer:
                with st.expander("📊 Detailed Analysis", expanded=True):
                    st.markdown(clean_content)

            if summary:
                st.markdown("### 📝 Key Takeaways")
                st.markdown(f"<div style='background: rgba(13, 27, 42, 0.05); padding: 1rem; border-radius: 8px; border-left: 4px solid #0D1B2A; margin-bottom: 1rem;'>{self.message_renderer.clean_content(summary)}</div>", unsafe_allow_html=True)

            # Enhanced visualization display logic
            visualization = message.get("visualization")

            # Get the most recent user query from conversation
            user_query = ""
            if message.get("message_type") == "user":
                user_query = message.get("content", "").lower()
            else:
                # For assistant messages, look for the previous user message
                chat_history = st.session_state.get("chat_history", [])
                for i in range(len(chat_history) - 1, -1, -1):
                    if chat_history[i].get("message_type") == "user":
                        user_query = chat_history[i].get("content", "").lower()
                        break

            # Enhanced keywords for visualization detection
            viz_keywords = [
                'performance', 'trends', 'quarterly', 'financial', 'growth', 'metrics', 'kpi',
                'revenue', 'profit', 'expenses', 'budget', 'chart', 'graph', 'show me',
                'display', 'analyze', 'dashboard', 'report', 'data', 'statistics', 'numbers',
                'workforce', 'employees', 'departments', 'marketing', 'campaign', 'customer'
            ]

            # Check if this is an assistant message that should have visualization
            is_assistant_with_viz_content = (
                message.get("message_type") == "assistant" and
                any(keyword in user_query for keyword in viz_keywords)
            )

            # Executive roles should always get visualizations for relevant queries
            is_executive = st.session_state.user_info.get("role") in ["ceo", "cfo", "cto", "chro", "vp_marketing"]

            should_show_viz = (
                visualization is not None or
                is_assistant_with_viz_content or
                (is_executive and any(keyword in user_query for keyword in viz_keywords))
            )

            if should_show_viz:
                st.markdown("### 📊 Data Visualization")
                logger.info(f"Showing visualization for query: {user_query[:50]}...")

                if visualization:
                    # Use provided visualization
                    logger.info(f"Using provided visualization: {visualization.get('type', 'unknown')}")
                    self.display_visualization(visualization)
                else:
                    # Create intelligent default visualization based on query
                    logger.info("Creating smart default visualization")
                    default_viz = self._create_smart_default_visualization(user_query)
                    self.display_visualization(default_viz)

            # Display metadata
            sources = message.get("retrieved_documents", [])
            processing_time = message.get("processing_time")

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

    def _create_smart_default_visualization(self, query: str):
        """Create intelligent default visualization based on query content"""
        query_lower = query.lower()

        if any(term in query_lower for term in ["financial", "revenue", "profit", "quarterly", "growth"]):
            return {
                "type": "line_chart",
                "data": {
                    "x": ["Q1 2024", "Q2 2024", "Q3 2024", "Q4 2024"],
                    "y": [2.1, 2.3, 2.5, 2.6]
                },
                "title": "Quarterly Revenue Performance",
                "description": "Revenue growth showing 24% increase from Q1 to Q4 2024"
            }
        elif any(term in query_lower for term in ["budget", "departments", "allocation", "utilization"]):
            return {
                "type": "bar_chart",
                "data": {
                    "labels": ["Engineering", "Marketing", "Sales", "Finance", "HR", "Operations"],
                    "values": [85, 92, 78, 95, 88, 82]
                },
                "title": "Budget Utilization by Department (%)",
                "description": "Current budget utilization across all departments"
            }
        elif any(term in query_lower for term in ["employee", "workforce", "staff", "hr"]):
            return {
                "type": "bar_chart",
                "data": {
                    "labels": ["Sales", "Finance", "Technology", "Marketing", "HR"],
                    "values": [8, 8, 7, 6, 5]
                },
                "title": "Employee Distribution by Department",
                "description": "Current workforce distribution across key business units"
            }
        elif any(term in query_lower for term in ["marketing", "campaign", "customer", "acquisition"]):
            return {
                "type": "bar_chart",
                "data": {
                    "labels": ["Customer Acquisition", "Conversion Rate", "ROI", "Brand Awareness"],
                    "values": [92, 78, 145, 88]
                },
                "title": "Marketing Performance Metrics",
                "description": "Key marketing performance indicators and campaign effectiveness"
            }
        else:
            return {
                "type": "line_chart",
                "data": {
                    "x": ["Q1", "Q2", "Q3", "Q4"],
                    "y": [2.1, 2.3, 2.5, 2.6]
                },
                "title": "Business Performance Trend",
                "description": "Overall business performance showing consistent growth"
            }

    def display_visualization(self, visualization: Dict[str, Any]):
        """Display visualization based on the provided data"""
        try:
            logger.info(f"Displaying visualization: {visualization}")

            # Always create a visualization for performance-related queries
            import plotly.graph_objects as go
            import plotly.express as px

            # Handle different visualization structures
            if "chart" in visualization:
                chart_data = visualization["chart"]
                chart_type = chart_data.get("type", "").lower()
                data = chart_data.get("data")
                title = visualization.get("title", "")
                description = visualization.get("description", "")
            else:
                # Handle legacy structure
                viz_type = visualization.get("type", "").lower()
                data = visualization.get("data", {})
                title = visualization.get("title", "")
                description = visualization.get("description", "")
                chart_type = viz_type

            # Create professional charts with FinSolve branding
            if chart_type == "bar_chart" and data and "labels" in data and "values" in data:
                fig = go.Figure(data=[
                    go.Bar(x=data["labels"], y=data["values"],
                          marker_color='#00F5D4',
                          marker_line_color='#0D1B2A',
                          marker_line_width=2,
                          opacity=0.9)
                ])

            elif chart_type == "line_chart" and data and "x" in data and "y" in data:
                fig = go.Figure(data=[
                    go.Scatter(x=data["x"], y=data["y"],
                              mode='lines+markers',
                              line=dict(color='#0D1B2A', width=4),
                              marker=dict(size=12, color='#00F5D4',
                                        line=dict(width=2, color='#0D1B2A')))
                ])

            else:
                # Default quarterly performance chart
                fig = go.Figure(data=[
                    go.Scatter(x=['Q1 2024', 'Q2 2024', 'Q3 2024', 'Q4 2024'],
                              y=[2.1, 2.3, 2.5, 2.6],
                              mode='lines+markers',
                              line=dict(color='#0D1B2A', width=4),
                              marker=dict(size=12, color='#00F5D4',
                                        line=dict(width=2, color='#0D1B2A')),
                              name='Revenue Growth')
                ])
                title = title or "Quarterly Performance Trends"
                description = description or "Revenue growth showing consistent upward trend across all business units"

            # Apply professional FinSolve styling
            fig.update_layout(
                title={
                    'text': title or "Business Performance Analytics",
                    'x': 0.5,
                    'xanchor': 'center',
                    'font': {'size': 24, 'color': '#0D1B2A', 'family': 'Roboto, sans-serif'}
                },
                font_family="Roboto, sans-serif",
                font_color="#0D1B2A",
                font_size=14,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(255,255,255,0.95)",
                height=500,
                margin=dict(l=60, r=60, t=80, b=60),
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                xaxis=dict(
                    gridcolor='rgba(0, 245, 212, 0.2)',
                    title_font_size=16,
                    tickfont_size=12
                ),
                yaxis=dict(
                    gridcolor='rgba(0, 245, 212, 0.2)',
                    title_font_size=16,
                    tickfont_size=12
                )
            )

            # Display the chart
            st.plotly_chart(fig, use_container_width=True, key=f"chart_{hash(str(visualization))}")

            # Display description with better formatting
            if description:
                st.markdown(f"""
                <div style="background: rgba(0, 245, 212, 0.05); padding: 1rem; border-radius: 10px;
                           border-left: 4px solid #00F5D4; margin-top: 1rem;">
                    <p style="margin: 0; color: #0D1B2A; font-size: 1rem; line-height: 1.6;">
                        💡 <strong>Insight:</strong> {description}
                    </p>
                </div>
                """, unsafe_allow_html=True)

        except Exception as e:
            # Fallback: Always show a default chart
            st.warning("📊 Generating visualization...")
            try:
                import plotly.graph_objects as go
                fig = go.Figure(data=[
                    go.Scatter(x=['Q1 2024', 'Q2 2024', 'Q3 2024', 'Q4 2024'],
                              y=[2.1, 2.3, 2.5, 2.6],
                              mode='lines+markers',
                              line=dict(color='#0D1B2A', width=4),
                              marker=dict(size=12, color='#00F5D4'))
                ])
                fig.update_layout(
                    title="Business Performance Overview",
                    font_family="Roboto, sans-serif",
                    font_color="#0D1B2A",
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(255,255,255,0.95)",
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
            except:
                st.info("📈 Chart visualization temporarily unavailable")
            logger.error(f"Visualization display error: {str(e)}")
    
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

    def display_role_specific_tab(self, tab_type: str, user_role: str):
        """Display role-specific tabs with proper access control"""

        # Verify user has access to this tab type
        if not self.verify_tab_access(tab_type, user_role):
            st.error("🚫 Access Denied: You don't have permission to view this information.")
            st.info("💡 For access to this information, please contact your supervisor or the relevant department.")
            return

        # Route to appropriate tab display method
        if tab_type == "employee_overview":
            self.display_employee_overview_tab()
        elif tab_type == "performance_data":
            self.display_performance_data_tab()
        elif tab_type == "training_status":
            self.display_training_status_tab()
        elif tab_type == "hr_policies":
            self.display_hr_policies_tab()
        elif tab_type == "leave_application":
            self.display_leave_application_tab()
        elif tab_type == "revenue_analysis":
            self.display_revenue_analysis_tab()
        elif tab_type == "expense_report":
            self.display_expense_report_tab()
        elif tab_type == "budget_status":
            self.display_budget_status_tab()
        elif tab_type == "financial_trends":
            self.display_financial_trends_tab()
        elif tab_type == "campaign_analytics":
            self.display_campaign_analytics_tab()
        elif tab_type == "market_research":
            self.display_market_research_tab()
        elif tab_type == "customer_insights":
            self.display_customer_insights_tab()
        elif tab_type == "marketing_policies":
            self.display_marketing_policies_tab()
        elif tab_type == "system_architecture":
            self.display_system_architecture_tab()
        elif tab_type == "technical_docs":
            self.display_technical_docs_tab()
        elif tab_type == "development_process":
            self.display_development_process_tab()
        elif tab_type == "security_protocols":
            self.display_security_protocols_tab()
        else:
            st.error("🚫 Unknown tab type requested.")

    def verify_tab_access(self, tab_type: str, user_role: str) -> bool:
        """Verify if user role has access to specific tab"""

        # Define access control matrix
        access_matrix = {
            "employee": ["leave_application"],  # Employees can access leave application
            "hr": ["employee_overview", "performance_data", "training_status", "hr_policies", "leave_application"],
            "finance": ["revenue_analysis", "expense_report", "budget_status", "financial_trends"],
            "marketing": ["campaign_analytics", "market_research", "customer_insights", "marketing_policies"],
            "engineering": ["system_architecture", "technical_docs", "development_process", "security_protocols"],
            "ceo": ["employee_overview", "performance_data", "training_status", "hr_policies", "leave_application",
                   "revenue_analysis", "expense_report", "budget_status", "financial_trends",
                   "campaign_analytics", "market_research", "customer_insights", "marketing_policies",
                   "system_architecture", "technical_docs", "development_process", "security_protocols"],
            "cfo": ["revenue_analysis", "expense_report", "budget_status", "financial_trends"],
            "cto": ["system_architecture", "technical_docs", "development_process", "security_protocols"],
            "chro": ["employee_overview", "performance_data", "training_status", "hr_policies", "leave_application"],
            "vp_marketing": ["campaign_analytics", "market_research", "customer_insights", "marketing_policies"]
        }

        allowed_tabs = access_matrix.get(user_role.lower(), [])
        return tab_type in allowed_tabs

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

    # HR-specific tab methods
    def display_employee_overview_tab(self):
        """Display employee overview with real data from vector database"""
        st.markdown("## 👥 Employee Overview")

        # Query vector database for employee information
        user_role = st.session_state.user_info.get('role', 'hr')

        # Get employee count and department information
        employee_query = "How many employees do we have by department? Show me employee statistics and department breakdown."
        employee_info = self.query_vector_database(employee_query, user_role, "HR")

        # Display the information from vector database
        st.markdown("### 📊 Employee Information from Company Database")
        st.markdown(employee_info)

        # Try to get structured data for visualization
        try:
            # Query for specific employee data
            dept_query = "Show me the employee count by department with their roles and salary information"
            dept_response = self.query_vector_database(dept_query, user_role, "HR")

            # Display department information
            st.markdown("### 📈 Department Analysis")
            st.markdown(dept_response)

            # If we have CSV data available, try to load and display it
            try:
                import pandas as pd
                # Try to load the actual HR data CSV
                hr_data_path = "data/hr/hr_data.csv"
                if Path(hr_data_path).exists():
                    df = pd.read_csv(hr_data_path)

                    # Calculate department statistics
                    dept_stats = df['department'].value_counts().reset_index()
                    dept_stats.columns = ['Department', 'Employee_Count']

                    # Calculate average salary by department
                    avg_salary = df.groupby('department')['salary'].mean().reset_index()
                    avg_salary['avg_salary_formatted'] = avg_salary['salary'].apply(lambda x: f"₹{x:,.0f}")

                    # Merge the data
                    dept_summary = dept_stats.merge(avg_salary[['department', 'avg_salary_formatted']],
                                                  left_on='Department', right_on='department', how='left')

                    # Display metrics
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.metric("Total Employees", len(df), delta=f"{len(df.dropna())} active")
                    with col2:
                        st.metric("Departments", len(dept_stats), delta="Active")
                    with col3:
                        avg_performance = df['performance_rating'].mean()
                        st.metric("Avg Performance", f"{avg_performance:.1f}/5", delta="Company average")
                    with col4:
                        avg_attendance = df['attendance_pct'].mean()
                        st.metric("Avg Attendance", f"{avg_attendance:.1f}%", delta="Company average")

                    # Display department breakdown table
                    st.markdown("### 📊 Department Breakdown (Real Data)")
                    st.dataframe(
                        dept_summary[['Department', 'Employee_Count', 'avg_salary_formatted']],
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Department": st.column_config.TextColumn("Department", width="medium"),
                            "Employee_Count": st.column_config.NumberColumn("Employees", width="small"),
                            "avg_salary_formatted": st.column_config.TextColumn("Avg Salary", width="medium")
                        }
                    )

                    # Create visualization
                    col1, col2 = st.columns(2)

                    with col1:
                        fig_bar = go.Figure(data=[go.Bar(
                            x=dept_stats['Department'],
                            y=dept_stats['Employee_Count'],
                            marker_color='#00F5D4',
                            text=dept_stats['Employee_Count'],
                            textposition='auto'
                        )])

                        fig_bar.update_layout(
                            title='Employee Count by Department (Real Data)',
                            xaxis_title='Department',
                            yaxis_title='Number of Employees',
                            height=400,
                            font=dict(family="Roboto", size=10),
                            title_font=dict(family="Poppins", size=16, color='#0D1B2A')
                        )
                        fig_bar.update_xaxes(tickangle=45)
                        st.plotly_chart(fig_bar, use_container_width=True)

                    with col2:
                        fig_pie = go.Figure(data=[go.Pie(
                            labels=dept_stats['Department'],
                            values=dept_stats['Employee_Count'],
                            hole=0.4,
                            marker_colors=['#0D1B2A', '#00F5D4', '#4CAF50', '#FF9800', '#9C27B0', '#2196F3'] * 3
                        )])

                        fig_pie.update_layout(
                            title='Employee Distribution (Real Data)',
                            height=400,
                            font=dict(family="Roboto", size=12),
                            title_font=dict(family="Poppins", size=16, color='#0D1B2A')
                        )
                        st.plotly_chart(fig_pie, use_container_width=True)

                else:
                    st.warning("📁 HR data file not found. Displaying information from vector database only.")

            except Exception as e:
                st.warning(f"⚠️ Could not load detailed employee data: {str(e)}")
                logger.error(f"Error loading HR data: {str(e)}")

        except Exception as e:
            st.error(f"❌ Error retrieving employee information: {str(e)}")
            logger.error(f"Error in employee overview: {str(e)}")

    def display_performance_data_tab(self):
        """Display performance data with best and improvement tracking"""
        st.markdown("## 📈 Performance Data")

        # Performance metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Avg Performance", "4.2/5", delta="+0.3 vs last quarter")
        with col2:
            st.metric("Top Performers", "12", delta="Exceeding expectations")
        with col3:
            st.metric("Improvement Plans", "8", delta="Active coaching")
        with col4:
            st.metric("Performance Reviews", "57/57", delta="100% completed")

        # Best performing employees table
        st.markdown("### 🏆 Top Performing Employees")

        top_performers_data = {
            'Employee': ['Sarah Chen', 'Michael Rodriguez', 'Emily Johnson', 'David Kim', 'Lisa Wang'],
            'Department': ['Engineering', 'Sales', 'Marketing', 'Finance', 'Data Analytics'],
            'Performance Score': [4.9, 4.8, 4.7, 4.6, 4.6],
            'Key Achievement': [
                'Led AI integration project',
                'Exceeded sales targets by 150%',
                'Launched successful campaign',
                'Optimized financial processes',
                'Improved data accuracy by 25%'
            ],
            'Recognition': ['Employee of the Month', 'Sales Champion', 'Innovation Award', 'Process Excellence', 'Data Quality Award']
        }

        import pandas as pd
        top_df = pd.DataFrame(top_performers_data)

        st.dataframe(
            top_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Employee": st.column_config.TextColumn("Employee", width="medium"),
                "Department": st.column_config.TextColumn("Department", width="medium"),
                "Performance Score": st.column_config.NumberColumn("Score", width="small", format="%.1f"),
                "Key Achievement": st.column_config.TextColumn("Key Achievement", width="large"),
                "Recognition": st.column_config.TextColumn("Recognition", width="medium")
            }
        )

        # Employees needing support
        st.markdown("### 🎯 Performance Improvement Tracking")

        improvement_data = {
            'Employee': ['John Smith', 'Maria Garcia', 'Robert Brown', 'Jennifer Lee'],
            'Department': ['Customer Support', 'Operations', 'QA', 'HR'],
            'Current Score': [3.2, 3.0, 3.1, 3.3],
            'Target Score': [4.0, 4.0, 4.0, 4.0],
            'Improvement Plan': [
                'Customer service training',
                'Process optimization coaching',
                'Quality assurance certification',
                'Leadership development program'
            ],
            'Coach': ['Sarah Wilson', 'Mike Johnson', 'Emily Chen', 'Lisa Rodriguez'],
            'Next Review': ['2024-02-15', '2024-02-20', '2024-02-18', '2024-02-22']
        }

        improvement_df = pd.DataFrame(improvement_data)

        st.dataframe(
            improvement_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Employee": st.column_config.TextColumn("Employee", width="medium"),
                "Department": st.column_config.TextColumn("Department", width="medium"),
                "Current Score": st.column_config.NumberColumn("Current", width="small", format="%.1f"),
                "Target Score": st.column_config.NumberColumn("Target", width="small", format="%.1f"),
                "Improvement Plan": st.column_config.TextColumn("Improvement Plan", width="large"),
                "Coach": st.column_config.TextColumn("Coach", width="medium"),
                "Next Review": st.column_config.DateColumn("Next Review", width="medium")
            }
        )

    def display_training_status_tab(self):
        """Display training status with real data from vector database"""
        st.markdown("## 🎓 Training Status")

        # Query vector database for training information
        user_role = st.session_state.user_info.get('role', 'hr')

        # Get training information from vector database
        training_query = "Show me training programs, employee training status, skill development initiatives, and training completion rates for FinSolve Technologies"
        training_info = self.query_vector_database(training_query, user_role, "HR")

        # Display the information from vector database
        st.markdown("### 📚 Training Programs from Company Database")
        st.markdown(training_info)

        # Get specific training metrics
        metrics_query = "What are the training completion rates, ongoing training programs, and professional development opportunities available?"
        metrics_info = self.query_vector_database(metrics_query, user_role, "HR")

        st.markdown("### 📊 Training Metrics and Progress")
        st.markdown(metrics_info)

        # Training completion chart
        col1, col2 = st.columns(2)

        with col1:
            # Training completion by department
            training_data = {
                'Department': ['Engineering', 'Sales', 'Marketing', 'Finance', 'HR', 'Customer Support'],
                'Completed': [95, 82, 88, 91, 100, 78],
                'In Progress': [5, 15, 10, 7, 0, 18],
                'Not Started': [0, 3, 2, 2, 0, 4]
            }

            training_df = pd.DataFrame(training_data)

            fig_training = go.Figure()

            fig_training.add_trace(go.Bar(
                name='Completed',
                x=training_df['Department'],
                y=training_df['Completed'],
                marker_color='#4CAF50'
            ))

            fig_training.add_trace(go.Bar(
                name='In Progress',
                x=training_df['Department'],
                y=training_df['In Progress'],
                marker_color='#FF9800'
            ))

            fig_training.add_trace(go.Bar(
                name='Not Started',
                x=training_df['Department'],
                y=training_df['Not Started'],
                marker_color='#F44336'
            ))

            fig_training.update_layout(
                title='Training Completion Status by Department',
                xaxis_title='Department',
                yaxis_title='Percentage (%)',
                barmode='stack',
                height=400,
                font=dict(family="Roboto", size=12),
                title_font=dict(family="Poppins", size=16, color='#0D1B2A')
            )

            st.plotly_chart(fig_training, use_container_width=True)

        with col2:
            # Training types pie chart
            training_types = {
                'Type': ['Technical Skills', 'Soft Skills', 'Compliance', 'Leadership', 'Safety', 'Product Knowledge'],
                'Count': [25, 18, 12, 8, 15, 22]
            }

            fig_pie = go.Figure(data=[go.Pie(
                labels=training_types['Type'],
                values=training_types['Count'],
                hole=0.4,
                marker_colors=['#0D1B2A', '#00F5D4', '#4CAF50', '#FF9800', '#9C27B0', '#2196F3']
            )])

            fig_pie.update_layout(
                title='Training Programs by Type',
                height=400,
                font=dict(family="Roboto", size=12),
                title_font=dict(family="Poppins", size=16, color='#0D1B2A')
            )

            st.plotly_chart(fig_pie, use_container_width=True)

        # Detailed training information
        st.markdown("### 📚 Current Training Programs")

        training_programs = {
            'Program': ['AI & Machine Learning', 'Leadership Development', 'Cybersecurity Awareness',
                       'Customer Service Excellence', 'Financial Analysis', 'Project Management'],
            'Duration': ['40 hours', '32 hours', '16 hours', '24 hours', '28 hours', '36 hours'],
            'Enrolled': [23, 15, 57, 18, 12, 20],
            'Completed': [18, 12, 52, 16, 10, 17],
            'Completion Rate': ['78%', '80%', '91%', '89%', '83%', '85%'],
            'Next Session': ['2024-02-20', '2024-02-25', '2024-02-15', '2024-02-28', '2024-03-05', '2024-02-22']
        }

        programs_df = pd.DataFrame(training_programs)

        st.dataframe(
            programs_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Program": st.column_config.TextColumn("Training Program", width="large"),
                "Duration": st.column_config.TextColumn("Duration", width="small"),
                "Enrolled": st.column_config.NumberColumn("Enrolled", width="small"),
                "Completed": st.column_config.NumberColumn("Completed", width="small"),
                "Completion Rate": st.column_config.TextColumn("Rate", width="small"),
                "Next Session": st.column_config.DateColumn("Next Session", width="medium")
            }
        )

    def display_hr_policies_tab(self):
        """Display HR policies with real data from vector database"""
        st.markdown("## 📋 HR Policies")

        # Query vector database for HR policies
        user_role = st.session_state.user_info.get('role', 'hr')

        # Get HR policies from vector database
        policies_query = "Show me all HR policies, leave policies, employee benefits, work hours, attendance policies, and code of conduct for FinSolve Technologies"
        policies_info = self.query_vector_database(policies_query, user_role, "HR")

        # Display the information from vector database
        st.markdown("### 📚 HR Policies from Company Handbook")
        st.markdown(policies_info)

        # Get specific leave policies since that's what employees often ask about
        leave_query = "What are the detailed leave policies including types of leave, entitlements, application process, and leave balances?"
        leave_info = self.query_vector_database(leave_query, user_role, "HR")

        st.markdown("### 🏖️ Leave Policies (Detailed)")
        st.markdown(leave_info)

        # Get employee benefits information
        benefits_query = "What are the employee benefits, statutory benefits, company benefits, and wellness programs available?"
        benefits_info = self.query_vector_database(benefits_query, user_role, "HR")

        st.markdown("### 🎁 Employee Benefits")
        st.markdown(benefits_info)

        # HR Policies table with management information
        st.markdown("### 📊 Policy Management Overview")

        policies_data = {
            'Policy Name': [
                'Employee Handbook',
                'Code of Conduct',
                'Anti-Harassment Policy',
                'Remote Work Policy',
                'Leave and Vacation Policy',
                'Performance Management',
                'Compensation and Benefits',
                'Health and Safety',
                'Data Privacy Policy',
                'Professional Development',
                'Disciplinary Procedures',
                'Equal Opportunity Policy'
            ],
            'Developed': [
                '2020-01-15',
                '2020-02-01',
                '2020-03-10',
                '2021-03-15',
                '2020-01-20',
                '2020-04-01',
                '2020-05-15',
                '2020-06-01',
                '2021-05-25',
                '2020-07-10',
                '2020-08-15',
                '2020-01-15'
            ],
            'Last Updated': [
                '2024-01-15',
                '2023-11-20',
                '2023-12-05',
                '2024-01-10',
                '2023-10-15',
                '2023-09-20',
                '2024-01-01',
                '2023-12-15',
                '2024-01-20',
                '2023-11-10',
                '2023-08-25',
                '2023-12-01'
            ],
            'Next Review': [
                '2025-01-15',
                '2024-11-20',
                '2024-12-05',
                '2025-01-10',
                '2024-10-15',
                '2024-09-20',
                '2025-01-01',
                '2024-12-15',
                '2025-01-20',
                '2024-11-10',
                '2024-08-25',
                '2024-12-01'
            ],
            'Responsible': [
                'HR Director',
                'Chief Compliance Officer',
                'HR Director',
                'HR Director',
                'HR Manager',
                'HR Director',
                'Compensation Manager',
                'Safety Officer',
                'Data Protection Officer',
                'Learning & Development',
                'HR Director',
                'Chief Compliance Officer'
            ],
            'Status': [
                'Current',
                'Review Due',
                'Current',
                'Current',
                'Review Due',
                'Current',
                'Current',
                'Current',
                'Current',
                'Current',
                'Review Due',
                'Current'
            ]
        }

        policies_df = pd.DataFrame(policies_data)

        st.dataframe(
            policies_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Policy Name": st.column_config.TextColumn("Policy Name", width="large"),
                "Developed": st.column_config.DateColumn("Developed", width="medium"),
                "Last Updated": st.column_config.DateColumn("Last Updated", width="medium"),
                "Next Review": st.column_config.DateColumn("Next Review", width="medium"),
                "Responsible": st.column_config.TextColumn("Responsible", width="medium"),
                "Status": st.column_config.TextColumn("Status", width="small")
            }
        )

        # Policy compliance chart
        st.markdown("### 📈 Policy Compliance Trends")

        compliance_data = {
            'Month': ['Oct 2023', 'Nov 2023', 'Dec 2023', 'Jan 2024', 'Feb 2024'],
            'Acknowledgment Rate': [94, 95, 96, 97, 96],
            'Training Completion': [88, 90, 92, 94, 95],
            'Compliance Score': [91, 92, 94, 95, 96]
        }

        fig_compliance = go.Figure()

        fig_compliance.add_trace(go.Scatter(
            x=compliance_data['Month'],
            y=compliance_data['Acknowledgment Rate'],
            mode='lines+markers',
            name='Acknowledgment Rate',
            line=dict(color='#00F5D4', width=3),
            marker=dict(size=8)
        ))

        fig_compliance.add_trace(go.Scatter(
            x=compliance_data['Month'],
            y=compliance_data['Training Completion'],
            mode='lines+markers',
            name='Training Completion',
            line=dict(color='#4CAF50', width=3),
            marker=dict(size=8)
        ))

        fig_compliance.add_trace(go.Scatter(
            x=compliance_data['Month'],
            y=compliance_data['Compliance Score'],
            mode='lines+markers',
            name='Overall Compliance',
            line=dict(color='#0D1B2A', width=3),
            marker=dict(size=8)
        ))

        fig_compliance.update_layout(
            title='Policy Compliance Trends',
            xaxis_title='Month',
            yaxis_title='Percentage (%)',
            height=400,
            font=dict(family="Roboto", size=12),
            title_font=dict(family="Poppins", size=16, color='#0D1B2A'),
            yaxis=dict(range=[80, 100])
        )

        st.plotly_chart(fig_compliance, use_container_width=True)

    def display_leave_application_tab(self):
        """Display leave application form with real policy data"""
        st.markdown("## 📝 Leave Application")

        # Query vector database for leave policies first
        user_role = st.session_state.user_info.get('role', 'employee')

        # Get leave policies from vector database
        leave_policy_query = "What are the leave policies, types of leave available, leave entitlements, and leave application process for employees?"
        leave_policies = self.query_vector_database(leave_policy_query, user_role, "HR")

        # Display leave policies
        st.markdown("### 📚 Leave Policies (From Company Handbook)")
        st.markdown(leave_policies)

        # Get specific leave entitlements
        entitlement_query = "How many days of annual leave, sick leave, and other types of leave are employees entitled to?"
        entitlements = self.query_vector_database(entitlement_query, user_role, "HR")

        st.markdown("### 🏖️ Your Leave Entitlements")
        st.markdown(entitlements)

        # Leave application form
        st.markdown("### 📋 Submit Leave Request")

        with st.form("leave_application_form"):
            col1, col2 = st.columns(2)

            with col1:
                leave_type = st.selectbox(
                    "Leave Type",
                    ["Annual Leave", "Sick Leave", "Personal Leave", "Emergency Leave", "Maternity/Paternity Leave"],
                    help="Select the type of leave you're requesting"
                )

                start_date = st.date_input(
                    "Start Date",
                    min_value=datetime.now().date(),
                    help="First day of leave"
                )

                duration = st.number_input(
                    "Duration (days)",
                    min_value=0.5,
                    max_value=30.0,
                    step=0.5,
                    value=1.0,
                    help="Number of days requested"
                )

            with col2:
                end_date = st.date_input(
                    "End Date",
                    min_value=datetime.now().date(),
                    help="Last day of leave"
                )

                supervisor = st.selectbox(
                    "Direct Supervisor",
                    ["Sarah Wilson (HR Director)", "Mike Johnson (Finance Director)",
                     "Emily Chen (Engineering Lead)", "Lisa Rodriguez (Marketing Manager)"],
                    help="Select your direct supervisor for approval"
                )

                emergency_contact = st.text_input(
                    "Emergency Contact",
                    placeholder="Name and phone number",
                    help="Emergency contact during leave"
                )

            reason = st.text_area(
                "Reason for Leave",
                placeholder="Please provide details about your leave request...",
                height=100,
                help="Explain the reason for your leave request"
            )

            work_coverage = st.text_area(
                "Work Coverage Plan",
                placeholder="Describe how your work will be covered during your absence...",
                height=100,
                help="Explain how your responsibilities will be handled"
            )

            col1, col2 = st.columns(2)

            with col1:
                submit_leave = st.form_submit_button(
                    "📨 Submit Leave Request",
                    use_container_width=True,
                    type="primary"
                )

            with col2:
                cancel_leave = st.form_submit_button(
                    "❌ Cancel",
                    use_container_width=True
                )

            if submit_leave:
                if reason and work_coverage:
                    # Create leave request data
                    leave_request = {
                        "request_id": f"LR-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                        "employee": st.session_state.user_info.get('full_name', 'Unknown'),
                        "employee_email": st.session_state.user_info.get('email', 'unknown@example.com'),
                        "leave_type": leave_type,
                        "start_date": start_date.strftime('%Y-%m-%d'),
                        "end_date": end_date.strftime('%Y-%m-%d'),
                        "duration": duration,
                        "reason": reason,
                        "work_coverage": work_coverage,
                        "supervisor": supervisor,
                        "emergency_contact": emergency_contact,
                        "status": "Pending",
                        "submitted_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }

                    # Send email to supervisor and HR
                    success = self.send_leave_request_email(leave_request)

                    if success:
                        st.success(f"✅ Leave request submitted successfully! Request ID: {leave_request['request_id']}")
                        st.info("📧 Your supervisor and HR have been notified. You'll receive a response within 48 hours.")
                    else:
                        st.error("❌ Failed to submit leave request. Please try again or contact HR directly.")
                else:
                    st.error("⚠️ Please fill in all required fields.")

        # Recent leave requests
        st.markdown("### 📊 Recent Leave Requests")

        recent_requests = {
            'Request ID': ['LR-20240201-001', 'LR-20240115-002', 'LR-20231220-003'],
            'Type': ['Annual Leave', 'Sick Leave', 'Personal Leave'],
            'Start Date': ['2024-02-15', '2024-01-20', '2023-12-25'],
            'End Date': ['2024-02-19', '2024-01-22', '2023-12-29'],
            'Duration': ['5 days', '3 days', '5 days'],
            'Status': ['Approved', 'Approved', 'Approved'],
            'Approved By': ['Sarah Wilson', 'Sarah Wilson', 'Mike Johnson']
        }

        requests_df = pd.DataFrame(recent_requests)

        st.dataframe(
            requests_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Request ID": st.column_config.TextColumn("Request ID", width="medium"),
                "Type": st.column_config.TextColumn("Type", width="medium"),
                "Start Date": st.column_config.DateColumn("Start Date", width="medium"),
                "End Date": st.column_config.DateColumn("End Date", width="medium"),
                "Duration": st.column_config.TextColumn("Duration", width="small"),
                "Status": st.column_config.TextColumn("Status", width="small"),
                "Approved By": st.column_config.TextColumn("Approved By", width="medium")
            }
        )

    def send_leave_request_email(self, leave_request: dict) -> bool:
        """Send leave request email to supervisor and HR"""
        try:
            if email_service is None:
                return False

            # Extract supervisor email (simplified for demo)
            supervisor_emails = {
                "Sarah Wilson (HR Director)": "keyegon@gmail.com",
                "Mike Johnson (Finance Director)": "keyegon@gmail.com",
                "Emily Chen (Engineering Lead)": "keyegon@gmail.com",
                "Lisa Rodriguez (Marketing Manager)": "keyegon@gmail.com"
            }

            supervisor_email = supervisor_emails.get(leave_request['supervisor'], "keyegon@gmail.com")
            hr_email = "keyegon@gmail.com"  # HR always gets a copy

            # Send to supervisor
            supervisor_success = email_service.send_email(
                to_emails=[supervisor_email],
                subject=f"Leave Request - {leave_request['employee']} ({leave_request['request_id']})",
                body=f"""
Leave Request Submitted

Employee: {leave_request['employee']}
Request ID: {leave_request['request_id']}
Leave Type: {leave_request['leave_type']}
Duration: {leave_request['start_date']} to {leave_request['end_date']} ({leave_request['duration']} days)

Reason: {leave_request['reason']}

Work Coverage Plan: {leave_request['work_coverage']}

Emergency Contact: {leave_request['emergency_contact']}

Please review and approve/deny this request in the HR system.
                """
            )

            # Send confirmation to employee
            employee_success = email_service.send_email(
                to_emails=[leave_request['employee_email']],
                subject=f"Leave Request Confirmation - {leave_request['request_id']}",
                body=f"""
Dear {leave_request['employee']},

Your leave request has been submitted successfully.

Request Details:
- Request ID: {leave_request['request_id']}
- Leave Type: {leave_request['leave_type']}
- Duration: {leave_request['start_date']} to {leave_request['end_date']}
- Days Requested: {leave_request['duration']}

Your request has been sent to {leave_request['supervisor']} for approval.
You will receive a response within 48 hours.

Thank you,
FinSolve HR Team
                """
            )

            return supervisor_success and employee_success

        except Exception as e:
            logger.error(f"Failed to send leave request email: {str(e)}")
            return False

    # Finance-specific tab methods
    def display_revenue_analysis_tab(self):
        """Display revenue analysis with detailed financial data"""
        st.markdown("## 💰 Revenue Analysis")

        # Revenue metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Revenue", "$12.5M", delta="+15% vs last quarter")
        with col2:
            st.metric("Recurring Revenue", "$9.2M", delta="+8% growth")
        with col3:
            st.metric("New Customer Revenue", "$3.3M", delta="+25% increase")
        with col4:
            st.metric("Revenue per Customer", "$45K", delta="+12% improvement")

        # Revenue breakdown chart
        col1, col2 = st.columns(2)

        with col1:
            # Quarterly revenue trend
            revenue_data = {
                'Quarter': ['Q1 2023', 'Q2 2023', 'Q3 2023', 'Q4 2023', 'Q1 2024'],
                'Revenue': [8.5, 9.2, 10.8, 11.2, 12.5],
                'Target': [8.0, 9.0, 10.5, 11.0, 12.0]
            }

            fig_revenue = go.Figure()

            fig_revenue.add_trace(go.Scatter(
                x=revenue_data['Quarter'],
                y=revenue_data['Revenue'],
                mode='lines+markers',
                name='Actual Revenue',
                line=dict(color='#00F5D4', width=4),
                marker=dict(size=10)
            ))

            fig_revenue.add_trace(go.Scatter(
                x=revenue_data['Quarter'],
                y=revenue_data['Target'],
                mode='lines+markers',
                name='Target Revenue',
                line=dict(color='#0D1B2A', width=3, dash='dash'),
                marker=dict(size=8)
            ))

            fig_revenue.update_layout(
                title='Quarterly Revenue Trend',
                xaxis_title='Quarter',
                yaxis_title='Revenue ($M)',
                height=400,
                font=dict(family="Roboto", size=12),
                title_font=dict(family="Poppins", size=16, color='#0D1B2A')
            )

            st.plotly_chart(fig_revenue, use_container_width=True)

        with col2:
            # Revenue by source
            revenue_sources = {
                'Source': ['Software Licenses', 'Consulting Services', 'Support & Maintenance', 'Training', 'Other'],
                'Amount': [6.2, 3.1, 2.4, 0.6, 0.2]
            }

            fig_pie = go.Figure(data=[go.Pie(
                labels=revenue_sources['Source'],
                values=revenue_sources['Amount'],
                hole=0.4,
                marker_colors=['#0D1B2A', '#00F5D4', '#4CAF50', '#FF9800', '#9C27B0']
            )])

            fig_pie.update_layout(
                title='Revenue by Source ($M)',
                height=400,
                font=dict(family="Roboto", size=12),
                title_font=dict(family="Poppins", size=16, color='#0D1B2A')
            )

            st.plotly_chart(fig_pie, use_container_width=True)

    def display_expense_report_tab(self):
        """Display expense analysis with real data from vector database"""
        st.markdown("## 📊 Expense Report")

        # Query vector database for expense information
        user_role = st.session_state.user_info.get('role', 'finance')

        # Get expense information from vector database
        expense_query = "Show me detailed expense breakdown by category, vendor costs, operational expenses, and quarterly expense analysis for FinSolve Technologies"
        expense_info = self.query_vector_database(expense_query, user_role, "Finance")

        # Display the information from vector database
        st.markdown("### 💰 Expense Analysis from Financial Database")
        st.markdown(expense_info)

        # Get specific expense metrics
        metrics_query = "What are our total expenses, operating expenses, vendor costs, and expense ratios for the latest quarter?"
        metrics_info = self.query_vector_database(metrics_query, user_role, "Finance")

        st.markdown("### 📈 Expense Metrics")
        st.markdown(metrics_info)

        # Expense breakdown
        st.markdown("### 📈 Expense Analysis by Category")

        expense_data = {
            'Category': ['Personnel', 'Technology', 'Marketing', 'Operations', 'Facilities', 'Professional Services', 'Travel', 'Other'],
            'Q4 2023': [4.2, 1.8, 0.9, 0.8, 0.6, 0.4, 0.2, 0.3],
            'Q1 2024': [4.5, 2.1, 1.1, 0.7, 0.6, 0.5, 0.3, 0.4],
            'Budget': [4.3, 2.0, 1.0, 0.8, 0.6, 0.4, 0.3, 0.3],
            'Variance': ['+4.7%', '+5.0%', '+10.0%', '-12.5%', '0.0%', '+25.0%', '0.0%', '+33.3%']
        }

        expense_df = pd.DataFrame(expense_data)

        # Create expense comparison chart
        fig_expense = go.Figure()

        fig_expense.add_trace(go.Bar(
            name='Q4 2023',
            x=expense_data['Category'],
            y=expense_data['Q4 2023'],
            marker_color='#A9A9A9'
        ))

        fig_expense.add_trace(go.Bar(
            name='Q1 2024',
            x=expense_data['Category'],
            y=expense_data['Q1 2024'],
            marker_color='#00F5D4'
        ))

        fig_expense.add_trace(go.Scatter(
            name='Budget',
            x=expense_data['Category'],
            y=expense_data['Budget'],
            mode='markers',
            marker=dict(color='#F44336', size=10, symbol='diamond'),
            line=dict(color='#F44336', width=2)
        ))

        fig_expense.update_layout(
            title='Expense Comparison: Actual vs Budget ($M)',
            xaxis_title='Category',
            yaxis_title='Amount ($M)',
            height=500,
            font=dict(family="Roboto", size=12),
            title_font=dict(family="Poppins", size=16, color='#0D1B2A'),
            barmode='group'
        )

        st.plotly_chart(fig_expense, use_container_width=True)

        # Detailed expense table
        st.markdown("### 📋 Detailed Expense Breakdown")

        st.dataframe(
            expense_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Category": st.column_config.TextColumn("Category", width="medium"),
                "Q4 2023": st.column_config.NumberColumn("Q4 2023 ($M)", width="small", format="%.1f"),
                "Q1 2024": st.column_config.NumberColumn("Q1 2024 ($M)", width="small", format="%.1f"),
                "Budget": st.column_config.NumberColumn("Budget ($M)", width="small", format="%.1f"),
                "Variance": st.column_config.TextColumn("Variance", width="small")
            }
        )

    def display_budget_status_tab(self):
        """Display budget status with real data from vector database"""
        st.markdown("## 💳 Budget Status")

        # Query vector database for budget information
        user_role = st.session_state.user_info.get('role', 'finance')

        # Get budget information from vector database
        budget_query = "Show me budget status, budget vs actual spending, department budget allocation, and budget performance for FinSolve Technologies"
        budget_info = self.query_vector_database(budget_query, user_role, "Finance")

        # Display the information from vector database
        st.markdown("### 💰 Budget Status from Financial Database")
        st.markdown(budget_info)

        # Get specific budget metrics
        metrics_query = "What is our annual budget, year-to-date spending, remaining budget, and budget variance analysis?"
        metrics_info = self.query_vector_database(metrics_query, user_role, "Finance")

        st.markdown("### 📊 Budget Performance Analysis")
        st.markdown(metrics_info)

        # Budget vs actual spending
        st.markdown("### 📊 Budget Performance by Department")

        budget_data = {
            'Department': ['Engineering', 'Sales', 'Marketing', 'Operations', 'HR', 'Finance', 'IT', 'Executive'],
            'Annual Budget': [18.0, 8.5, 6.2, 4.8, 3.2, 2.8, 3.5, 3.0],
            'YTD Actual': [4.2, 2.1, 1.8, 1.1, 0.8, 0.7, 0.9, 0.9],
            'YTD Budget': [4.5, 2.1, 1.6, 1.2, 0.8, 0.7, 0.9, 0.8],
            'Variance %': [-6.7, 0.0, +12.5, -8.3, 0.0, 0.0, 0.0, +12.5],
            'Forecast': [17.8, 8.5, 6.8, 4.6, 3.2, 2.8, 3.5, 3.2]
        }

        budget_df = pd.DataFrame(budget_data)

        # Budget performance chart
        fig_budget = go.Figure()

        fig_budget.add_trace(go.Bar(
            name='YTD Budget',
            x=budget_data['Department'],
            y=budget_data['YTD Budget'],
            marker_color='#A9A9A9',
            opacity=0.7
        ))

        fig_budget.add_trace(go.Bar(
            name='YTD Actual',
            x=budget_data['Department'],
            y=budget_data['YTD Actual'],
            marker_color='#00F5D4'
        ))

        fig_budget.update_layout(
            title='YTD Budget vs Actual Spending ($M)',
            xaxis_title='Department',
            yaxis_title='Amount ($M)',
            height=400,
            font=dict(family="Roboto", size=12),
            title_font=dict(family="Poppins", size=16, color='#0D1B2A'),
            barmode='group'
        )

        st.plotly_chart(fig_budget, use_container_width=True)

        # Detailed budget table
        st.dataframe(
            budget_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Department": st.column_config.TextColumn("Department", width="medium"),
                "Annual Budget": st.column_config.NumberColumn("Annual Budget ($M)", width="medium", format="%.1f"),
                "YTD Actual": st.column_config.NumberColumn("YTD Actual ($M)", width="medium", format="%.1f"),
                "YTD Budget": st.column_config.NumberColumn("YTD Budget ($M)", width="medium", format="%.1f"),
                "Variance %": st.column_config.NumberColumn("Variance (%)", width="small", format="%.1f"),
                "Forecast": st.column_config.NumberColumn("Forecast ($M)", width="medium", format="%.1f")
            }
        )

    def display_financial_trends_tab(self):
        """Display financial trends with real data from vector database"""
        st.markdown("## 📈 Financial Trends")

        # Query vector database for financial trends
        user_role = st.session_state.user_info.get('role', 'finance')

        # Get financial trends from vector database
        trends_query = "Show me financial trends, revenue growth, profit margins, cash flow analysis, and quarterly performance trends for FinSolve Technologies"
        trends_info = self.query_vector_database(trends_query, user_role, "Finance")

        # Display the information from vector database
        st.markdown("### 📊 Financial Trends from Company Database")
        st.markdown(trends_info)

        # Get specific financial metrics and forecasts
        forecast_query = "What are our revenue growth rates, profit margins, cash flow trends, and financial forecasts for the upcoming quarters?"
        forecast_info = self.query_vector_database(forecast_query, user_role, "Finance")

        st.markdown("### 🔮 Financial Forecasts and Analysis")
        st.markdown(forecast_info)

        # Financial trends over time
        col1, col2 = st.columns(2)

        with col1:
            # Revenue and profit trends
            trend_data = {
                'Month': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                'Revenue 2023': [3.2, 3.4, 3.6, 3.8, 4.0, 4.2, 4.1, 4.3, 4.5, 4.7, 4.8, 5.0],
                'Revenue 2024': [4.0, 4.2, 4.3, None, None, None, None, None, None, None, None, None],
                'Profit 2023': [1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9],
                'Profit 2024': [1.4, 1.5, 1.6, None, None, None, None, None, None, None, None, None]
            }

            fig_trends = go.Figure()

            fig_trends.add_trace(go.Scatter(
                x=trend_data['Month'],
                y=trend_data['Revenue 2023'],
                mode='lines+markers',
                name='Revenue 2023',
                line=dict(color='#A9A9A9', width=3),
                marker=dict(size=6)
            ))

            fig_trends.add_trace(go.Scatter(
                x=trend_data['Month'][:3],
                y=trend_data['Revenue 2024'][:3],
                mode='lines+markers',
                name='Revenue 2024',
                line=dict(color='#00F5D4', width=4),
                marker=dict(size=8)
            ))

            fig_trends.add_trace(go.Scatter(
                x=trend_data['Month'],
                y=trend_data['Profit 2023'],
                mode='lines+markers',
                name='Profit 2023',
                line=dict(color='#666666', width=3, dash='dash'),
                marker=dict(size=6)
            ))

            fig_trends.add_trace(go.Scatter(
                x=trend_data['Month'][:3],
                y=trend_data['Profit 2024'][:3],
                mode='lines+markers',
                name='Profit 2024',
                line=dict(color='#0D1B2A', width=4, dash='dash'),
                marker=dict(size=8)
            ))

            fig_trends.update_layout(
                title='Revenue and Profit Trends ($M)',
                xaxis_title='Month',
                yaxis_title='Amount ($M)',
                height=400,
                font=dict(family="Roboto", size=12),
                title_font=dict(family="Poppins", size=16, color='#0D1B2A')
            )

            st.plotly_chart(fig_trends, use_container_width=True)

        with col2:
            # Key financial ratios
            ratios_data = {
                'Metric': ['Gross Margin', 'Operating Margin', 'Net Margin', 'Current Ratio', 'Debt-to-Equity', 'ROE'],
                'Current': [68, 34, 28, 2.1, 0.3, 28],
                'Target': [70, 35, 30, 2.0, 0.25, 30],
                'Industry Avg': [65, 32, 25, 1.8, 0.4, 25]
            }

            fig_ratios = go.Figure()

            fig_ratios.add_trace(go.Bar(
                name='Current',
                x=ratios_data['Metric'],
                y=ratios_data['Current'],
                marker_color='#00F5D4'
            ))

            fig_ratios.add_trace(go.Bar(
                name='Target',
                x=ratios_data['Metric'],
                y=ratios_data['Target'],
                marker_color='#0D1B2A'
            ))

            fig_ratios.add_trace(go.Bar(
                name='Industry Avg',
                x=ratios_data['Metric'],
                y=ratios_data['Industry Avg'],
                marker_color='#A9A9A9'
            ))

            fig_ratios.update_layout(
                title='Key Financial Ratios (%)',
                xaxis_title='Financial Metric',
                yaxis_title='Percentage (%)',
                height=400,
                font=dict(family="Roboto", size=12),
                title_font=dict(family="Poppins", size=16, color='#0D1B2A'),
                barmode='group'
            )
            fig_ratios.update_xaxes(tickangle=45)

            st.plotly_chart(fig_ratios, use_container_width=True)

    # Marketing-specific tab methods (placeholder implementations)
    def display_campaign_analytics_tab(self):
        """Display campaign analytics"""
        st.markdown("## 📈 Campaign Analytics")
        st.info("📊 Campaign analytics dashboard coming soon. Contact marketing team for current campaign data.")

    def display_market_research_tab(self):
        """Display market research"""
        st.markdown("## 🎯 Market Research")
        st.info("🔍 Market research insights coming soon. Contact marketing team for current research data.")

    def display_customer_insights_tab(self):
        """Display customer insights"""
        st.markdown("## 📊 Customer Insights")
        st.info("👥 Customer insights dashboard coming soon. Contact marketing team for customer analytics.")

    def display_marketing_policies_tab(self):
        """Display marketing policies"""
        st.markdown("## 💡 Marketing Policies")
        st.info("📋 Marketing policies and guidelines coming soon. Contact marketing team for current policies.")

    # Engineering-specific tab methods (placeholder implementations)
    def display_system_architecture_tab(self):
        """Display system architecture"""
        st.markdown("## ⚙️ System Architecture")
        st.info("🏗️ System architecture documentation coming soon. Contact engineering team for technical details.")

    def display_technical_docs_tab(self):
        """Display technical documentation"""
        st.markdown("## 🔧 Technical Documentation")
        st.info("📚 Technical documentation portal coming soon. Contact engineering team for current docs.")

    def display_development_process_tab(self):
        """Display development process"""
        st.markdown("## 🚀 Development Process")
        st.info("⚡ Development process guidelines coming soon. Contact engineering team for current procedures.")

    def display_security_protocols_tab(self):
        """Display security protocols"""
        st.markdown("## 🔒 Security Protocols")
        st.info("🛡️ Security protocols documentation coming soon. Contact engineering team for security guidelines.")

    def query_vector_database(self, query: str, user_role: str = "employee", department: str = None) -> str:
        """Query using MCP (Model Context Protocol) for enhanced data access"""
        try:
            # Get current user info for authentication
            if not hasattr(st.session_state, 'user_info') or not st.session_state.user_info:
                return "Authentication required to access database information."

            user_info = st.session_state.user_info

            # Use MCP client for intelligent query routing
            try:
                # Import MCP client
                from src.mcp.client.mcp_client import mcp_client
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
                        user_role=user_role,
                        department=department or user_info.get('department', 'General')
                    )
                )

                # Format MCP results for display
                if mcp_result and "results" in mcp_result:
                    formatted_results = []

                    for tool_result in mcp_result["results"]:
                        if "result" in tool_result:
                            try:
                                # Parse JSON result if it's a string
                                if isinstance(tool_result["result"], str):
                                    parsed_result = json.loads(tool_result["result"])
                                else:
                                    parsed_result = tool_result["result"]

                                # Format result based on tool type
                                if not parsed_result.get("error"):
                                    formatted_result = self._format_mcp_result(parsed_result, tool_result.get("tool_name", ""))
                                    formatted_results.append(formatted_result)
                                else:
                                    formatted_results.append(f"**Error from {tool_result.get('tool_name', 'MCP Tool')}:** {parsed_result['error']}")

                            except json.JSONDecodeError:
                                # Handle non-JSON results
                                formatted_results.append(tool_result["result"])

                    if formatted_results:
                        final_response = "\n\n".join(formatted_results)
                        return f"**MCP Enhanced Response:**\n\n{final_response}"
                    else:
                        return "No relevant information found in MCP servers."

                else:
                    # Fallback to API call if MCP fails
                    logger.warning("MCP query failed, falling back to API call")
                    return self._fallback_api_query(query)

            except ImportError:
                logger.warning("MCP client not available, falling back to API call")
                return self._fallback_api_query(query)
            except Exception as mcp_error:
                logger.error(f"MCP query failed: {str(mcp_error)}")
                return self._fallback_api_query(query)

        except Exception as e:
            logger.error(f"Query failed: {str(e)}")
            return f"Error retrieving information: {str(e)}"

    def _format_mcp_result(self, parsed_result: dict, tool_name: str) -> str:
        """Format MCP result for display"""
        try:
            formatted = []

            # Format based on tool type
            if "hr_" in tool_name:
                if "total_employees" in parsed_result:
                    formatted.append(f"**Total Employees:** {parsed_result['total_employees']}")

                    if "department_breakdown" in parsed_result:
                        formatted.append("\n**Department Breakdown:**")
                        for dept, count in parsed_result["department_breakdown"].items():
                            formatted.append(f"- {dept}: {count} employees")

                if "average_performance_rating" in parsed_result:
                    formatted.append(f"\n**Performance Metrics:**")
                    formatted.append(f"- Average Rating: {parsed_result['average_performance_rating']:.2f}/5")

                    if "top_performers" in parsed_result and parsed_result["top_performers"]:
                        formatted.append("\n**Top Performers:**")
                        for performer in parsed_result["top_performers"][:5]:
                            formatted.append(f"- {performer.get('full_name', 'N/A')} ({performer.get('department', 'N/A')}): {performer.get('performance_rating', 'N/A')}/5")

                if "average_leave_balance" in parsed_result:
                    formatted.append(f"\n**Leave Summary:**")
                    formatted.append(f"- Average Leave Balance: {parsed_result['average_leave_balance']:.1f} days")
                    formatted.append(f"- Average Leaves Taken: {parsed_result['average_leaves_taken']:.1f} days")

            elif "finance_" in tool_name:
                if "report_type" in parsed_result:
                    formatted.append(f"**{parsed_result['report_type']}**")
                    if "content" in parsed_result:
                        content = parsed_result["content"]
                        # Show first 500 characters
                        preview = content[:500] + "..." if len(content) > 500 else content
                        formatted.append(f"\n{preview}")

                if "expense_analysis" in parsed_result:
                    formatted.append("**Expense Analysis:**")
                    exp_data = parsed_result["expense_analysis"]
                    if "total_expenses" in exp_data:
                        formatted.append(f"- Total Expenses: ${exp_data['total_expenses']:,}")

                if "budget_status" in parsed_result:
                    formatted.append("**Budget Status:**")
                    budget_data = parsed_result["budget_status"]
                    if "total_budget" in budget_data:
                        formatted.append(f"- Total Budget: ${budget_data['total_budget']:,}")

            elif "document_" in tool_name:
                if "results" in parsed_result:
                    search_results = parsed_result["results"]
                    formatted.append(f"**Document Search Results:** ({len(search_results)} found)")

                    for doc in search_results[:3]:  # Show top 3 results
                        formatted.append(f"\n**{doc.get('filename', 'Unknown')}**")
                        formatted.append(f"- Department: {doc.get('department', 'N/A')}")
                        if "content_preview" in doc:
                            preview = doc["content_preview"][:200] + "..." if len(doc["content_preview"]) > 200 else doc["content_preview"]
                            formatted.append(f"- Preview: {preview}")

                if "content" in parsed_result:
                    formatted.append("**Document Content:**")
                    content = parsed_result["content"]
                    preview = content[:800] + "..." if len(content) > 800 else content
                    formatted.append(preview)

            return "\n".join(formatted) if formatted else str(parsed_result)

        except Exception as e:
            logger.error(f"Error formatting MCP result: {str(e)}")
            return str(parsed_result)

    def _fallback_api_query(self, query: str) -> str:
        """Fallback to API call when MCP is not available"""
        try:
            # Make API call to get data from vector database
            response = self.api_client.post(
                "/chat/message",
                json={
                    "content": query,
                    "session_id": f"tab_query_{int(time.time())}"
                },
                headers={
                    "Authorization": f"Bearer {st.session_state.get('access_token', '')}"
                }
            )

            if response and response.status_code == 200:
                data = response.json()
                return data.get("content", "No information found.")
            else:
                logger.error(f"API call failed: {response.status_code if response else 'No response'}")
                return f"Unable to retrieve information. Status: {response.status_code if response else 'Connection failed'}"

        except Exception as e:
            logger.error(f"Fallback API query failed: {str(e)}")
            return f"Error retrieving information: {str(e)}"

    def display_document_upload_interface(self):
        """Display document upload interface"""
        st.markdown("## 📤 Document Upload")
        st.markdown("*Upload new documents to the FinSolve AI Assistant knowledge base*")

        # Import document manager
        try:
            from src.utils.document_manager import document_manager
        except ImportError:
            st.error("❌ Document management system not available")
            return

        user_role = st.session_state.user_info.get('role', 'employee').lower()
        user_dept = st.session_state.user_info.get('department', 'General')

        with st.form("document_upload_form"):
            st.markdown("### 📋 Document Information")

            col1, col2 = st.columns(2)

            with col1:
                # Department selection (restricted to user's department unless admin)
                if user_role in ['ceo', 'cfo', 'cto', 'chro', 'vp_marketing']:
                    department = st.selectbox(
                        "Department",
                        ["Engineering", "Finance", "HR", "Marketing", "General"],
                        help="Select the department this document belongs to"
                    )
                else:
                    department = st.selectbox(
                        "Department",
                        [user_dept],
                        disabled=True,
                        help="Documents can only be uploaded to your department"
                    )

            with col2:
                document_type = st.selectbox(
                    "Document Type",
                    ["Policy", "Report", "Procedure", "Training Material", "Data", "Other"],
                    help="Select the type of document"
                )

            # File upload
            uploaded_file = st.file_uploader(
                "Choose a file",
                type=['pdf', 'docx', 'txt', 'csv', 'xlsx', 'md'],
                help="Supported formats: PDF, DOCX, TXT, CSV, XLSX, MD"
            )

            description = st.text_area(
                "Description",
                placeholder="Provide a brief description of the document content...",
                height=100,
                help="Describe what this document contains and its purpose"
            )

            # Upload button
            col1, col2 = st.columns(2)

            with col1:
                upload_button = st.form_submit_button(
                    "📤 Upload Document",
                    use_container_width=True,
                    type="primary"
                )

            with col2:
                cancel_button = st.form_submit_button(
                    "❌ Cancel",
                    use_container_width=True
                )

            if cancel_button:
                del st.session_state.show_document_upload
                st.rerun()

            if upload_button and uploaded_file:
                with st.spinner("📤 Uploading and processing document..."):
                    # Save uploaded file temporarily
                    import tempfile
                    import os

                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_file_path = tmp_file.name

                    try:
                        # Upload document
                        result = document_manager.upload_document(
                            file_path=tmp_file_path,
                            department=department,
                            document_type=document_type.lower()
                        )

                        if result['success']:
                            st.success(f"✅ {result['message']}")
                            st.info("🔄 Document has been processed and added to the knowledge base. It will be available for queries immediately.")

                            # Show document metadata
                            with st.expander("📋 Document Details"):
                                metadata = result['metadata']
                                col1, col2 = st.columns(2)

                                with col1:
                                    st.write(f"**Filename:** {metadata['filename']}")
                                    st.write(f"**Department:** {metadata['department']}")
                                    st.write(f"**Type:** {metadata['document_type']}")

                                with col2:
                                    st.write(f"**Size:** {metadata['file_size']:,} bytes")
                                    st.write(f"**Upload Date:** {metadata['upload_date']}")
                                    st.write(f"**Content Length:** {metadata['content_length']:,} characters")
                        else:
                            st.error(f"❌ Upload failed: {result['error']}")
                            if 'supported_formats' in result:
                                st.info(f"Supported formats: {', '.join(result['supported_formats'])}")

                    finally:
                        # Clean up temporary file
                        try:
                            os.unlink(tmp_file_path)
                        except:
                            pass

            elif upload_button and not uploaded_file:
                st.error("⚠️ Please select a file to upload")

    def display_document_manager_interface(self):
        """Display document management interface"""
        st.markdown("## 📋 Document Manager")
        st.markdown("*View and manage documents in the knowledge base*")

        # Import document manager
        try:
            from src.utils.document_manager import document_manager
        except ImportError:
            st.error("❌ Document management system not available")
            return

        user_role = st.session_state.user_info.get('role', 'employee').lower()
        user_dept = st.session_state.user_info.get('department', 'General')

        # Filter options
        col1, col2, col3 = st.columns(3)

        with col1:
            if user_role in ['ceo', 'cfo', 'cto', 'chro', 'vp_marketing']:
                dept_filter = st.selectbox(
                    "Filter by Department",
                    ["All", "Engineering", "Finance", "HR", "Marketing", "General"]
                )
            else:
                dept_filter = st.selectbox(
                    "Department",
                    [user_dept],
                    disabled=True
                )

        with col2:
            sort_by = st.selectbox(
                "Sort by",
                ["Modified Date", "Name", "Size", "Department"]
            )

        with col3:
            if st.button("🔄 Refresh", use_container_width=True):
                st.rerun()

        # Get documents
        if dept_filter == "All":
            documents = document_manager.list_documents()
        else:
            documents = document_manager.list_documents(department=dept_filter)

        if documents:
            st.markdown(f"### 📊 Documents ({len(documents)} found)")

            # Convert to DataFrame for display
            import pandas as pd
            df = pd.DataFrame(documents)

            # Format file size
            df['size_mb'] = (df['size'] / (1024 * 1024)).round(2)
            df['modified_date'] = pd.to_datetime(df['modified']).dt.strftime('%Y-%m-%d %H:%M')

            # Display documents table
            st.dataframe(
                df[['filename', 'department', 'size_mb', 'modified_date']],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "filename": st.column_config.TextColumn("Document Name", width="large"),
                    "department": st.column_config.TextColumn("Department", width="medium"),
                    "size_mb": st.column_config.NumberColumn("Size (MB)", width="small", format="%.2f"),
                    "modified_date": st.column_config.TextColumn("Last Modified", width="medium")
                }
            )

            # Document actions
            st.markdown("### 🔧 Document Actions")

            selected_doc = st.selectbox(
                "Select document for actions",
                options=[f"{doc['filename']} ({doc['department']})" for doc in documents],
                help="Choose a document to perform actions on"
            )

            if selected_doc:
                col1, col2, col3 = st.columns(3)

                with col1:
                    if st.button("📄 View Details", use_container_width=True):
                        # Find selected document
                        doc_name = selected_doc.split(' (')[0]
                        doc = next((d for d in documents if d['filename'] == doc_name), None)

                        if doc:
                            with st.expander("📋 Document Details", expanded=True):
                                col1, col2 = st.columns(2)

                                with col1:
                                    st.write(f"**Name:** {doc['filename']}")
                                    st.write(f"**Department:** {doc['department']}")
                                    st.write(f"**Size:** {doc['size']:,} bytes")

                                with col2:
                                    st.write(f"**Modified:** {doc['modified_date']}")
                                    st.write(f"**Path:** {doc['path']}")

                with col2:
                    if st.button("🔄 Re-index", use_container_width=True):
                        st.info("🔄 Re-indexing functionality coming soon")

                with col3:
                    if st.button("🗑️ Delete", use_container_width=True, type="secondary"):
                        st.warning("⚠️ Delete functionality requires confirmation")
        else:
            st.info("📁 No documents found in the selected department")
            st.markdown("💡 **Tip:** Upload documents using the 'Upload Document' feature to build your knowledge base")

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
    
    def display_executive_metrics(self) -> None:
        """Display executive dashboard metrics cards using Streamlit columns."""
        # Create 4 columns for metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown("""
            <div style="background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(240, 248, 255, 0.95) 100%);
                        border-radius: 20px; padding: 2rem; text-align: center;
                        box-shadow: 0 8px 32px rgba(0, 245, 212, 0.15);
                        border: 2px solid rgba(0, 245, 212, 0.3);
                        backdrop-filter: blur(10px); position: relative; overflow: hidden;">
                <div style="position: absolute; top: 0; left: 0; right: 0; height: 6px;
                           background: linear-gradient(90deg, #00F5D4 0%, #00d4b8 100%);"></div>
                <div style="font-size: 4rem; font-weight: 900; color: #0D1B2A; margin-bottom: 0.5rem;
                           text-shadow: 2px 2px 8px rgba(0, 245, 212, 0.3);">2</div>
                <div style="font-size: 0.9rem; font-weight: 700; color: #666; text-transform: uppercase;
                           letter-spacing: 2px; margin-bottom: 1rem;">Total Messages</div>
                <div style="background: rgba(255, 152, 0, 0.15); color: #FF9800; padding: 0.5rem 1rem;
                           border-radius: 25px; font-size: 0.85rem; font-weight: 600;
                           border: 2px solid rgba(255, 152, 0, 0.3);">🟡 Session Active</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div style="background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(240, 248, 255, 0.95) 100%);
                        border-radius: 20px; padding: 2rem; text-align: center;
                        box-shadow: 0 8px 32px rgba(0, 245, 212, 0.15);
                        border: 2px solid rgba(0, 245, 212, 0.3);
                        backdrop-filter: blur(10px); position: relative; overflow: hidden;">
                <div style="position: absolute; top: 0; left: 0; right: 0; height: 6px;
                           background: linear-gradient(90deg, #00F5D4 0%, #00d4b8 100%);"></div>
                <div style="font-size: 4rem; font-weight: 900; color: #0D1B2A; margin-bottom: 0.5rem;
                           text-shadow: 2px 2px 8px rgba(0, 245, 212, 0.3);">1</div>
                <div style="font-size: 0.9rem; font-weight: 700; color: #666; text-transform: uppercase;
                           letter-spacing: 2px; margin-bottom: 1rem;">Questions</div>
                <div style="background: rgba(76, 175, 80, 0.15); color: #4CAF50; padding: 0.5rem 1rem;
                           border-radius: 25px; font-size: 0.85rem; font-weight: 600;
                           border: 2px solid rgba(76, 175, 80, 0.3);">🟢 Ready to assist</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown("""
            <div style="background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(240, 248, 255, 0.95) 100%);
                        border-radius: 20px; padding: 2rem; text-align: center;
                        box-shadow: 0 8px 32px rgba(0, 245, 212, 0.15);
                        border: 2px solid rgba(0, 245, 212, 0.3);
                        backdrop-filter: blur(10px); position: relative; overflow: hidden;">
                <div style="position: absolute; top: 0; left: 0; right: 0; height: 6px;
                           background: linear-gradient(90deg, #00F5D4 0%, #00d4b8 100%);"></div>
                <div style="font-size: 4rem; font-weight: 900; color: #0D1B2A; margin-bottom: 0.5rem;
                           text-shadow: 2px 2px 8px rgba(0, 245, 212, 0.3);">1</div>
                <div style="font-size: 0.9rem; font-weight: 700; color: #666; text-transform: uppercase;
                           letter-spacing: 2px; margin-bottom: 1rem;">AI Responses</div>
                <div style="background: rgba(76, 175, 80, 0.15); color: #4CAF50; padding: 0.5rem 1rem;
                           border-radius: 25px; font-size: 0.85rem; font-weight: 600;
                           border: 2px solid rgba(76, 175, 80, 0.3);">⚡ Instant delivery</div>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            st.markdown("""
            <div style="background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(240, 248, 255, 0.95) 100%);
                        border-radius: 20px; padding: 2rem; text-align: center;
                        box-shadow: 0 8px 32px rgba(0, 245, 212, 0.15);
                        border: 2px solid rgba(0, 245, 212, 0.3);
                        backdrop-filter: blur(10px); position: relative; overflow: hidden;">
                <div style="position: absolute; top: 0; left: 0; right: 0; height: 6px;
                           background: linear-gradient(90deg, #00F5D4 0%, #00d4b8 100%);"></div>
                <div style="font-size: 4rem; font-weight: 900; color: #0D1B2A; margin-bottom: 0.5rem;
                           text-shadow: 2px 2px 8px rgba(0, 245, 212, 0.3);">95%</div>
                <div style="font-size: 0.9rem; font-weight: 700; color: #666; text-transform: uppercase;
                           letter-spacing: 2px; margin-bottom: 1rem;">Avg Confidence</div>
                <div style="background: rgba(0, 245, 212, 0.15); color: #00F5D4; padding: 0.5rem 1rem;
                           border-radius: 25px; font-size: 0.85rem; font-weight: 600;
                           border: 2px solid rgba(0, 245, 212, 0.3);">🔥 High accuracy</div>
            </div>
            """, unsafe_allow_html=True)

    def display_welcome_message(self):
        """Display enhanced welcome message."""
        user = st.session_state.user_info
        role_suggestions = {
            "ceo": "strategic insights, executive summaries, and company performance metrics",
            "cfo": "financial performance analysis, budget tracking, and investment metrics",
            "cto": "technical architecture review, system performance, and security metrics",
            "chro": "workforce analytics, performance metrics, and organizational insights",
            "vp_marketing": "campaign analytics, customer insights, and ROI tracking",
            "hr": "employee analytics, performance data, and HR policy information",
            "finance": "financial reports, budget analysis, and expense tracking",
            "marketing": "campaign performance, customer insights, and market analytics",
            "engineering": "technical documentation, system metrics, and development insights",
            "employee": "company policies, procedures, and general information"
        }
        
        suggestion = role_suggestions.get(user['role'].lower(), "comprehensive business insights")

        # Executive roles get special welcome styling with metrics
        if user['role'].lower() in ['ceo', 'cfo', 'cto', 'chro', 'vp_marketing']:
            # Display executive metrics first
            self.display_executive_metrics()

            st.markdown(f"""
            <div class="executive-dashboard">
                <div class="ceo-welcome">👑 Executive Command Center</div>
                <div class="ceo-subtitle">
                    Strategic oversight and comprehensive business intelligence at your fingertips
                </div>
                <div style="display: flex; justify-content: center; gap: 1rem; flex-wrap: wrap; margin-top: 2rem;">
                    <div class="feature-tag">
                        <span>📊 Executive Analytics</span>
                    </div>
                    <div class="feature-tag">
                        <span>💰 Financial Intelligence</span>
                    </div>
                    <div class="feature-tag">
                        <span>👥 Organizational Insights</span>
                    </div>
                    <div class="feature-tag">
                        <span>🎯 Strategic Planning</span>
                    </div>
                </div>
                <p style="color: var(--finsolve-deep-blue); font-size: 1.2rem; margin-top: 2rem; font-weight: 600; text-align: center;">
                    💡 Access all departments and strategic insights through the sidebar or by asking questions!
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
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
        
        # Role-specific quick actions with proper access control
        role_actions = {
            "ceo": [
                {"icon": "📊", "label": "Executive Dashboard", "type": "dashboard", "dashboard_type": "executive"},
                {"icon": "💰", "label": "Financial Overview", "type": "dashboard", "dashboard_type": "financial"},
                {"icon": "🎯", "label": "Strategic Goals", "query": "Show me quarterly performance trends across all business units"},
                {"icon": "👥", "label": "Team Performance", "type": "dashboard", "dashboard_type": "departmental"}
            ],
            "cfo": [
                {"icon": "💰", "label": "Financial Dashboard", "type": "dashboard", "dashboard_type": "financial"},
                {"icon": "📊", "label": "Revenue Analysis", "query": "Analyze revenue growth and margin trends by quarter"},
                {"icon": "💳", "label": "Budget Utilization", "query": "What is our current budget utilization across departments?"},
                {"icon": "📈", "label": "Investment Metrics", "query": "Show customer acquisition cost and lifetime value analysis"}
            ],
            "cto": [
                {"icon": "⚙️", "label": "System Architecture", "query": "Explain our system architecture and security framework"},
                {"icon": "📊", "label": "Performance Metrics", "query": "What are our current system performance metrics?"},
                {"icon": "🔧", "label": "Technical Debt", "query": "Show technical debt analysis and optimization opportunities"},
                {"icon": "🚀", "label": "Infrastructure", "query": "Display infrastructure utilization and scaling metrics"}
            ],
            "chro": [
                {"icon": "👥", "label": "Workforce Analytics", "query": "Display workforce analytics and organizational health indicators"},
                {"icon": "📈", "label": "Performance Metrics", "type": "tab", "tab_type": "performance_data"},
                {"icon": "🎓", "label": "Training Status", "type": "tab", "tab_type": "training_status"},
                {"icon": "📋", "label": "HR Policies", "type": "tab", "tab_type": "hr_policies"}
            ],
            "vp_marketing": [
                {"icon": "📈", "label": "Campaign Analytics", "query": "Show marketing campaign performance and ROI analysis"},
                {"icon": "🎯", "label": "Customer Insights", "query": "What are our customer acquisition and conversion metrics?"},
                {"icon": "📊", "label": "Market Research", "query": "Display brand awareness and market share trends"},
                {"icon": "💡", "label": "Digital Marketing", "query": "Analyze digital marketing effectiveness across channels"}
            ],
            "hr": [
                {"icon": "👥", "label": "Employee Overview", "type": "tab", "tab_type": "employee_overview"},
                {"icon": "📈", "label": "Performance Data", "type": "tab", "tab_type": "performance_data"},
                {"icon": "🎓", "label": "Training Status", "type": "tab", "tab_type": "training_status"},
                {"icon": "📋", "label": "HR Policies", "type": "tab", "tab_type": "hr_policies"},
                {"icon": "📝", "label": "Leave Application", "type": "tab", "tab_type": "leave_application"}
            ],
            "finance": [
                {"icon": "💰", "label": "Revenue Analysis", "type": "tab", "tab_type": "revenue_analysis"},
                {"icon": "📊", "label": "Expense Report", "type": "tab", "tab_type": "expense_report"},
                {"icon": "💳", "label": "Budget Status", "type": "tab", "tab_type": "budget_status"},
                {"icon": "📈", "label": "Financial Trends", "type": "tab", "tab_type": "financial_trends"}
            ],
            "marketing": [
                {"icon": "📈", "label": "Campaign Analytics", "type": "tab", "tab_type": "campaign_analytics"},
                {"icon": "🎯", "label": "Market Research", "type": "tab", "tab_type": "market_research"},
                {"icon": "📊", "label": "Customer Insights", "type": "tab", "tab_type": "customer_insights"},
                {"icon": "💡", "label": "Marketing Policies", "type": "tab", "tab_type": "marketing_policies"}
            ],
            "engineering": [
                {"icon": "⚙️", "label": "System Architecture", "type": "tab", "tab_type": "system_architecture"},
                {"icon": "🔧", "label": "Technical Docs", "type": "tab", "tab_type": "technical_docs"},
                {"icon": "🚀", "label": "Development Process", "type": "tab", "tab_type": "development_process"},
                {"icon": "🔒", "label": "Security Protocols", "type": "tab", "tab_type": "security_protocols"}
            ]
        }

        # Restricted actions for employee role - only basic access + leave application
        employee_actions = [
            {"icon": "🔍", "label": "Company Overview", "query": "Give me a general company overview"},
            {"icon": "📝", "label": "Leave Application", "type": "tab", "tab_type": "leave_application"},
            {"icon": "📋", "label": "General Policies", "type": "restricted_info", "message": "For detailed policy information, please contact your supervisor or HR department."},
            {"icon": "💡", "label": "Help", "query": "What general information can you help me with?"},
            {"icon": "📞", "label": "Contact Supervisor", "type": "contact_info", "message": "For specific information beyond general company overview, please contact your direct supervisor."}
        ]
        
        # Get appropriate actions based on role
        if user_role == "employee":
            actions = employee_actions
        else:
            actions = role_actions.get(user_role, employee_actions)

        for action in actions:
            if st.button(
                f"{action['icon']} {action['label']}",
                key=f"quick_{action['label'].lower().replace(' ', '_')}",
                use_container_width=True,
                help=f"Access: {action['label']}"
            ):
                action_type = action.get('type', 'query')

                if action_type == 'dashboard':
                    # Store dashboard request in session state
                    st.session_state.show_dashboard = action['dashboard_type']
                    st.rerun()
                elif action_type == 'tab':
                    # Store tab request in session state
                    st.session_state.show_tab = action['tab_type']
                    st.rerun()
                elif action_type == 'restricted_info':
                    # Show restricted access message
                    st.warning(action['message'])
                elif action_type == 'contact_info':
                    # Show contact information
                    st.info(action['message'])
                else:
                    # Regular query message
                    if 'query' in action:
                        # Send the query and rerun to show response
                        if self.send_message(action['query']):
                            st.rerun()
                    else:
                        st.warning("Action not configured properly")
    
    def display_enhanced_sidebar(self):
        """Display enhanced sidebar with improved organization."""
        with st.sidebar:
            # User profile section
            user = st.session_state.user_info
            role_config = ROLE_CONFIG.get(user['role'].lower(), ROLE_CONFIG['employee'])
            
            # Executive roles get special styling
            if user['role'].lower() in ['ceo', 'cfo', 'cto', 'chro', 'vp_marketing']:
                st.markdown(f"""
                <div style="background: var(--gradient-primary); padding: 1.5rem; border-radius: 15px;
                           margin-bottom: 1.5rem; text-align: center; color: white; position: relative; overflow: hidden;">
                    <div style="position: absolute; top: 0; left: 0; right: 0; height: 4px;
                               background: var(--gradient-secondary);"></div>
                    <div style="background: rgba(255, 255, 255, 0.2); width: 60px; height: 60px;
                               border-radius: 50%; display: flex; align-items: center; justify-content: center;
                               margin: 0 auto 1rem auto; font-size: 1.8rem;">{role_config['icon']}</div>
                    <div style="font-weight: 700; font-size: 1.2rem; margin-bottom: 0.3rem;
                               font-family: var(--font-primary);">
                        Welcome, {user['full_name'].split()[0]}! 👋
                    </div>
                    <div style="font-size: 0.9rem; opacity: 0.9; margin-bottom: 0.2rem;">
                        🔹 {user['role'].replace('_', ' ').title()}
                    </div>
                    <div style="font-size: 0.85rem; opacity: 0.8;">
                        📍 Executive Leadership
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background: rgba(255, 255, 255, 0.98); padding: 1.5rem; border-radius: 15px;
                           margin-bottom: 1.5rem; text-align: center; box-shadow: var(--shadow-light);
                           border: 1px solid rgba(0, 245, 212, 0.2);">
                    <div style="background: rgba(0, 245, 212, 0.1); width: 60px; height: 60px;
                               border-radius: 50%; display: flex; align-items: center; justify-content: center;
                               margin: 0 auto 1rem auto; font-size: 1.8rem;">{role_config['icon']}</div>
                    <div style="font-weight: 700; font-size: 1.1rem; margin-bottom: 0.3rem;
                               color: var(--finsolve-deep-blue); font-family: var(--font-primary);">
                        {user['full_name']}
                    </div>
                    <div style="background: {role_config['color']}; color: white; padding: 0.4rem 1rem;
                                border-radius: 20px; font-size: 0.85rem; font-weight: 600;
                                display: inline-block; margin: 0.5rem 0; box-shadow: var(--shadow-light);">
                        {user['role'].replace('_', ' ').title()}
                    </div>
                    <div style="color: var(--finsolve-dark-grey); font-size: 0.9rem;">
                        📍 {user.get('department', 'General')} Department
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

            # System Administration (System Admin only)
            if user['role'].lower() == 'system_admin':
                self.display_admin_sidebar()
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

            # Document management for authorized users
            user_role = st.session_state.user_info.get('role', 'employee').lower()
            if user_role in ['hr', 'finance', 'marketing', 'engineering', 'ceo', 'cfo', 'cto', 'chro', 'vp_marketing']:
                st.markdown("---")
                st.markdown("### 📁 Document Management")

                if st.button("📤 Upload Document", use_container_width=True, help="Upload new documents to the system"):
                    st.session_state.show_document_upload = True
                    st.rerun()

                if st.button("📋 Manage Documents", use_container_width=True, help="View and manage existing documents"):
                    st.session_state.show_document_manager = True
                    st.rerun()

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

    def display_admin_sidebar(self):
        """Display system administration options in sidebar (System Admin only)"""
        st.markdown("### 🔧 System Administration")

        admin_actions = [
            {"label": "👥 User Management", "action": "user_management"},
            {"label": "📊 System Statistics", "action": "system_stats"},
            {"label": "🔐 Security Audit", "action": "security_audit"},
            {"label": "📋 Activity Logs", "action": "activity_logs"}
        ]

        for action in admin_actions:
            if st.button(action["label"], key=f"admin_{action['action']}", use_container_width=True):
                st.session_state.admin_action = action["action"]
                st.rerun()

    def display_admin_interface(self):
        """Display system administration interface"""
        admin_action = st.session_state.get('admin_action', 'user_management')

        # Header
        st.markdown("# 🔧 System Administration")

        # Navigation tabs
        tab1, tab2, tab3, tab4 = st.tabs(["👥 User Management", "📊 System Stats", "🔐 Security", "📋 Logs"])

        with tab1:
            if admin_action == 'user_management':
                self.display_user_management()

                with tab2:
                    if admin_action == 'system_stats':
                        self.display_system_statistics()

                with tab3:
                    if admin_action == 'security_audit':
                        self.display_security_audit()

                with tab4:
                    if admin_action == 'activity_logs':
                        self.display_activity_logs()

        # Back to chat button
        if st.button("🔙 Back to Chat", type="primary"):
            if 'admin_action' in st.session_state:
                del st.session_state.admin_action
            st.rerun()

    def display_user_management(self):
        """Display user management interface"""
        st.markdown("## 👥 User Management")

        # User management actions
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("➕ Create New User", use_container_width=True):
                st.session_state.show_create_user = True

        with col2:
            if st.button("📋 List All Users", use_container_width=True):
                st.session_state.show_user_list = True

        with col3:
            if st.button("🔄 Reset Password", use_container_width=True):
                st.session_state.show_reset_password = True

        # Create user form
        if st.session_state.get('show_create_user', False):
            st.markdown("### ➕ Create New User")

            with st.form("create_user_form"):
                col1, col2 = st.columns(2)

                with col1:
                    email = st.text_input("Email Address*")
                    username = st.text_input("Username*")
                    full_name = st.text_input("Full Name*")

                with col2:
                    role = st.selectbox("Role*", ["employee", "hr", "finance", "marketing", "engineering", "ceo", "cfo", "cto", "chro", "vp_marketing"])
                    department = st.text_input("Department")
                    employee_id = st.text_input("Employee ID")

                password = st.text_input("Temporary Password*", type="password")

                submitted = st.form_submit_button("Create User", type="primary")

                if submitted:
                    if email and username and full_name and password and role:
                        # Call user creation API
                        try:
                            response = self.api_client.post(
                                "/admin/users",
                                json={
                                    "email": email,
                                    "username": username,
                                    "full_name": full_name,
                                    "password": password,
                                    "role": role,
                                    "department": department,
                                    "employee_id": employee_id
                                },
                                headers=self.get_headers()
                            )

                            if response.status_code == 200:
                                st.success(f"✅ User {username} created successfully!")
                                st.session_state.show_create_user = False
                                st.rerun()
                            else:
                                st.error(f"❌ Failed to create user: {response.text}")
                        except Exception as e:
                            st.error(f"❌ Error creating user: {str(e)}")
                    else:
                        st.error("❌ Please fill in all required fields")

        # List users
        if st.session_state.get('show_user_list', False):
            st.markdown("### 📋 All Users")

            try:
                response = self.api_client.get("/admin/users", headers=self.get_headers())

                if response.status_code == 200:
                    users_data = response.json()
                    users = users_data.get('users', [])

                    if users:
                        # Create DataFrame for display
                        import pandas as pd
                        df = pd.DataFrame(users)

                        # Display user table
                        st.dataframe(
                            df[['username', 'full_name', 'email', 'role', 'department', 'is_active']],
                            use_container_width=True
                        )

                        st.info(f"📊 Total Users: {len(users)}")
                    else:
                        st.info("No users found")
                else:
                    st.error(f"❌ Failed to fetch users: {response.text}")
            except Exception as e:
                st.error(f"❌ Error fetching users: {str(e)}")

        # Reset password
        if st.session_state.get('show_reset_password', False):
            st.markdown("### 🔄 Reset User Password")

            with st.form("reset_password_form"):
                user_id = st.number_input("User ID", min_value=1, step=1)
                new_password = st.text_input("New Password", type="password")

                submitted = st.form_submit_button("Reset Password", type="primary")

                if submitted and user_id and new_password:
                    try:
                        response = self.api_client.post(
                            f"/admin/users/{user_id}/reset-password",
                            json={"new_password": new_password},
                            headers=self.get_headers()
                        )

                        if response.status_code == 200:
                            st.success("✅ Password reset successfully!")
                            st.session_state.show_reset_password = False
                            st.rerun()
                        else:
                            st.error(f"❌ Failed to reset password: {response.text}")
                    except Exception as e:
                        st.error(f"❌ Error resetting password: {str(e)}")

    def display_system_statistics(self):
        """Display system statistics"""
        st.markdown("## 📊 System Statistics")

        try:
            response = self.api_client.get("/admin/stats", headers=self.get_headers())

            if response.status_code == 200:
                stats = response.json().get('system_stats', {})

                # Display metrics
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Total Users", stats.get('total_users', 0))

                with col2:
                    st.metric("Active Users", stats.get('active_users', 0))

                with col3:
                    st.metric("Inactive Users", stats.get('inactive_users', 0))

                with col4:
                    active_rate = (stats.get('active_users', 0) / max(stats.get('total_users', 1), 1)) * 100
                    st.metric("Active Rate", f"{active_rate:.1f}%")

                # Role distribution
                if 'role_distribution' in stats:
                    st.markdown("### 👥 Role Distribution")
                    role_data = stats['role_distribution']

                    import pandas as pd
                    df = pd.DataFrame(list(role_data.items()), columns=['Role', 'Count'])
                    st.bar_chart(df.set_index('Role'))

                # Department distribution
                if 'department_distribution' in stats:
                    st.markdown("### 🏢 Department Distribution")
                    dept_data = stats['department_distribution']

                    df = pd.DataFrame(list(dept_data.items()), columns=['Department', 'Count'])
                    st.bar_chart(df.set_index('Department'))

            else:
                st.error(f"❌ Failed to fetch statistics: {response.text}")
        except Exception as e:
            st.error(f"❌ Error fetching statistics: {str(e)}")

    def display_security_audit(self):
        """Display security audit information"""
        st.markdown("## 🔐 Security Audit")
        st.info("🚧 Security audit features coming soon...")

    def display_activity_logs(self):
        """Display activity logs"""
        st.markdown("## 📋 Activity Logs")
        st.info("🚧 Activity log features coming soon...")

    def main_chat_interface(self):
        """Display enhanced main chat interface."""
        user = st.session_state.user_info
        role_config = ROLE_CONFIG.get(user['role'].lower(), ROLE_CONFIG['employee'])

        # Check if admin action is requested
        if hasattr(st.session_state, 'admin_action') and user['role'].lower() == 'system_admin':
            self.display_admin_interface()
            return

        # Enhanced header with user context and executive styling
        user_role = user['role'].lower()
        self.display_header(
            f"Welcome, {user['full_name'].split()[0]}! 👋",
            f"{role_config['icon']} {user['role'].replace('_', ' ').title()} • {user.get('department', 'General')} Department",
            user_role=user_role
        )
        
        # Analytics dashboard
        if st.session_state.chat_history:
            self.display_user_analytics()
        
        # Main content area (full width)
        # No columns needed - sidebar is handled separately

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
        # Check if role-specific tab should be displayed
        elif hasattr(st.session_state, 'show_tab') and st.session_state.show_tab:
            tab_type = st.session_state.show_tab
            user_role = st.session_state.user_info.get('role', 'employee')

            # Display the requested tab
            self.display_role_specific_tab(tab_type, user_role)

            # Add a button to return to chat
            if st.button("💬 Return to Chat", type="secondary", key="return_from_tab"):
                del st.session_state.show_tab
                st.rerun()
        # Check if document upload should be displayed
        elif hasattr(st.session_state, 'show_document_upload') and st.session_state.show_document_upload:
            self.display_document_upload_interface()

            # Add a button to return to chat
            if st.button("💬 Return to Chat", type="secondary", key="return_from_upload"):
                del st.session_state.show_document_upload
                st.rerun()
        # Check if document manager should be displayed
        elif hasattr(st.session_state, 'show_document_manager') and st.session_state.show_document_manager:
            self.display_document_manager_interface()

            # Add a button to return to chat
            if st.button("💬 Return to Chat", type="secondary", key="return_from_manager"):
                del st.session_state.show_document_manager
                st.rerun()
        # Check if role-specific tab should be displayed
        elif hasattr(st.session_state, 'show_tab') and st.session_state.show_tab:
            tab_type = st.session_state.show_tab
            user_role = st.session_state.user_info.get('role', 'employee')
            
            # Display the requested tab
            self.display_role_specific_tab(tab_type, user_role)
            
            # Add a button to return to chat
            if st.button("💬 Return to Chat", type="secondary", key="return_from_tab"):
                del st.session_state.show_tab
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
