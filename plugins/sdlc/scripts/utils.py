"""Utility functions for ADW system."""

import logging
import os
import sys
import uuid
from datetime import datetime


def make_adw_id() -> str:
    """Generate a short 8-character UUID for ADW tracking."""
    return str(uuid.uuid4())[:8]


def setup_logger(adw_id: str, trigger_type: str = "adw_plan_build") -> logging.Logger:
    """Set up logger that writes to both console and file using adw_id.
    
    Args:
        adw_id: The ADW workflow ID
        trigger_type: Type of trigger (adw_plan_build, trigger_webhook, etc.)
    
    Returns:
        Configured logger instance
    """
    # Create log directory: agents/{adw_id}/adw_plan_build/
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_dir = os.path.join(project_root, "agents", adw_id, trigger_type)
    os.makedirs(log_dir, exist_ok=True)
    
    # Log file path: agents/{adw_id}/adw_plan_build/execution.log
    log_file = os.path.join(log_dir, "execution.log")
    
    # Create logger with unique name using adw_id
    logger = logging.getLogger(f"adw_{adw_id}")
    logger.setLevel(logging.DEBUG)
    
    # Clear any existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # File handler - captures everything
    file_handler = logging.FileHandler(log_file, mode='a')
    file_handler.setLevel(logging.DEBUG)
    
    # Console handler - INFO and above
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Format with timestamp for file
    file_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Simpler format for console (similar to current print statements)
    console_formatter = logging.Formatter('%(message)s')
    
    file_handler.setFormatter(file_formatter)
    console_handler.setFormatter(console_formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Log initial setup message
    logger.info(f"ADW Logger initialized - ID: {adw_id}")
    logger.debug(f"Log file: {log_file}")
    
    return logger


def get_logger(adw_id: str) -> logging.Logger:
    """Get existing logger by ADW ID.
    
    Args:
        adw_id: The ADW workflow ID
        
    Returns:
        Logger instance
    """
    return logging.getLogger(f"adw_{adw_id}")