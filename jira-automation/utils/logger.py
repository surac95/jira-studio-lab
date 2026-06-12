"""
Logging configuration for JIRA automation system.

This module provides centralized logging configuration with support for
both file and console output, rotating file handlers, and configurable
log levels.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional, Union
from pathlib import Path


# Global dictionary to store configured loggers
_loggers = {}


def setup_logger(
    name: str,
    log_file: Optional[Union[str, Path]] = None,
    level: str = "INFO"
) -> logging.Logger:
    """
    Set up and configure a logger with file and console handlers.
    
    This function creates a logger with:
    - Console handler for immediate feedback
    - Rotating file handler (10MB max, 5 backups) for persistent logs
    - Consistent formatting across all handlers
    - Configurable log level
    
    Args:
        name: Name of the logger (typically __name__ of the module)
        log_file: Path to log file (default: logs/{name}.log)
        level: Logging level as string (default: 'INFO')
               Valid values: 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
    
    Returns:
        Configured logger instance
        
    Raises:
        ValueError: If an invalid log level is provided
        OSError: If log directory cannot be created
    """
    # Return existing logger if already configured
    if name in _loggers:
        return _loggers[name]
    
    # Create logger
    logger = logging.getLogger(name)
    
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {level}')
    
    logger.setLevel(numeric_level)
    
    # Prevent duplicate handlers if logger already exists
    if logger.handlers:
        return logger
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if log_file is specified or default)
    if log_file is None:
        # Default log file path
        log_dir = Path(__file__).parent.parent / 'logs'
        log_file_path = log_dir / f'{name.replace(".", "_")}.log'
    else:
        log_file_path = Path(log_file)
    
    # Ensure log directory exists
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create rotating file handler
    # Max size: 10MB, Keep 5 backup files
    file_handler = RotatingFileHandler(
        log_file_path,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Store logger in global dictionary
    _loggers[name] = logger
    
    logger.info(f"Logger '{name}' initialized with level {level}")
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance by name.
    
    If the logger has been previously configured with setup_logger(),
    returns the existing logger. Otherwise, creates a new logger with
    default configuration.
    
    Args:
        name: Name of the logger to retrieve
        
    Returns:
        Logger instance
    """
    if name in _loggers:
        return _loggers[name]
    
    # Get log level from environment variable or use INFO as default
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    
    return setup_logger(name, level=log_level)


def set_log_level(logger_name: str, level: str) -> None:
    """
    Change the log level of an existing logger.
    
    Args:
        logger_name: Name of the logger to modify
        level: New log level as string ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        
    Raises:
        ValueError: If an invalid log level is provided
        KeyError: If logger does not exist
    """
    if logger_name not in _loggers:
        raise KeyError(f"Logger '{logger_name}' not found. Use setup_logger() first.")
    
    logger = _loggers[logger_name]
    
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {level}')
    
    logger.setLevel(numeric_level)
    
    # Update all handlers
    for handler in logger.handlers:
        handler.setLevel(numeric_level)
    
    logger.info(f"Log level changed to {level}")


def get_all_loggers() -> dict:
    """
    Get all configured loggers.
    
    Returns:
        Dictionary mapping logger names to logger instances
    """
    return _loggers.copy()


def shutdown_loggers() -> None:
    """
    Shutdown all loggers and close their handlers.
    
    This should be called when the application is shutting down
    to ensure all log messages are flushed and files are closed properly.
    """
    for logger_name, logger in _loggers.items():
        logger.info(f"Shutting down logger '{logger_name}'")
        for handler in logger.handlers:
            handler.close()
            logger.removeHandler(handler)
    
    _loggers.clear()
    logging.shutdown()

# Made with Bob
