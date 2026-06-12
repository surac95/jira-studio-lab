"""
Unit tests for the logger utility.

This module contains comprehensive tests for the logging configuration,
including logger setup, level management, and handler configuration.
"""

import unittest
import logging
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import (
    setup_logger,
    get_logger,
    set_log_level,
    get_all_loggers,
    shutdown_loggers,
    _loggers
)


class TestLogger(unittest.TestCase):
    """Test cases for the logger utility."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Clear any existing loggers
        _loggers.clear()
        
        # Create a temporary log directory for tests
        self.test_log_dir = Path(__file__).parent / 'test_logs'
        self.test_log_dir.mkdir(exist_ok=True)
    
    def tearDown(self):
        """Clean up after each test method."""
        # Shutdown all loggers
        shutdown_loggers()
        
        # Clean up test log files
        if self.test_log_dir.exists():
            for log_file in self.test_log_dir.glob('*.log*'):
                try:
                    log_file.unlink()
                except Exception:
                    pass
            try:
                self.test_log_dir.rmdir()
            except Exception:
                pass
    
    def test_setup_logger_basic(self):
        """Test basic logger setup."""
        logger = setup_logger('test_logger')
        
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, 'test_logger')
        self.assertEqual(logger.level, logging.INFO)
    
    def test_setup_logger_with_custom_level(self):
        """Test logger setup with custom log level."""
        logger = setup_logger('test_logger', level='DEBUG')
        
        self.assertEqual(logger.level, logging.DEBUG)
    
    def test_setup_logger_with_custom_file(self):
        """Test logger setup with custom log file."""
        log_file = self.test_log_dir / 'custom.log'
        logger = setup_logger('test_logger', log_file=str(log_file))
        
        self.assertTrue(log_file.exists())
    
    def test_setup_logger_invalid_level(self):
        """Test that invalid log level raises ValueError."""
        with self.assertRaises(ValueError):
            setup_logger('test_logger', level='INVALID')
    
    def test_setup_logger_creates_handlers(self):
        """Test that logger has both console and file handlers."""
        log_file = self.test_log_dir / 'test.log'
        logger = setup_logger('test_logger', log_file=str(log_file))
        
        # Should have 2 handlers: console and file
        self.assertEqual(len(logger.handlers), 2)
        
        # Check handler types
        handler_types = [type(h).__name__ for h in logger.handlers]
        self.assertIn('StreamHandler', handler_types)
        self.assertIn('RotatingFileHandler', handler_types)
    
    def test_setup_logger_singleton_behavior(self):
        """Test that setup_logger returns same instance for same name."""
        logger1 = setup_logger('test_logger')
        logger2 = setup_logger('test_logger')
        
        self.assertIs(logger1, logger2)
    
    def test_setup_logger_different_names(self):
        """Test that different logger names create different instances."""
        logger1 = setup_logger('test_logger1')
        logger2 = setup_logger('test_logger2')
        
        self.assertIsNot(logger1, logger2)
    
    def test_get_logger_existing(self):
        """Test getting an existing logger."""
        setup_logger('test_logger')
        logger = get_logger('test_logger')
        
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, 'test_logger')
    
    def test_get_logger_new(self):
        """Test getting a new logger that doesn't exist."""
        logger = get_logger('new_logger')
        
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, 'new_logger')
    
    @patch.dict(os.environ, {'LOG_LEVEL': 'DEBUG'})
    def test_get_logger_uses_env_log_level(self):
        """Test that get_logger uses LOG_LEVEL from environment."""
        logger = get_logger('test_logger')
        
        self.assertEqual(logger.level, logging.DEBUG)
    
    def test_set_log_level_success(self):
        """Test changing log level of existing logger."""
        logger = setup_logger('test_logger', level='INFO')
        set_log_level('test_logger', 'DEBUG')
        
        self.assertEqual(logger.level, logging.DEBUG)
    
    def test_set_log_level_invalid_level(self):
        """Test that invalid log level raises ValueError."""
        setup_logger('test_logger')
        
        with self.assertRaises(ValueError):
            set_log_level('test_logger', 'INVALID')
    
    def test_set_log_level_nonexistent_logger(self):
        """Test that setting level for nonexistent logger raises KeyError."""
        with self.assertRaises(KeyError):
            set_log_level('nonexistent_logger', 'DEBUG')
    
    def test_set_log_level_updates_handlers(self):
        """Test that set_log_level updates all handlers."""
        log_file = self.test_log_dir / 'test.log'
        logger = setup_logger('test_logger', log_file=str(log_file), level='INFO')
        
        set_log_level('test_logger', 'WARNING')
        
        # Check that all handlers have the new level
        for handler in logger.handlers:
            self.assertEqual(handler.level, logging.WARNING)
    
    def test_get_all_loggers(self):
        """Test getting all configured loggers."""
        setup_logger('logger1')
        setup_logger('logger2')
        setup_logger('logger3')
        
        all_loggers = get_all_loggers()
        
        self.assertEqual(len(all_loggers), 3)
        self.assertIn('logger1', all_loggers)
        self.assertIn('logger2', all_loggers)
        self.assertIn('logger3', all_loggers)
    
    def test_get_all_loggers_returns_copy(self):
        """Test that get_all_loggers returns a copy, not the original dict."""
        setup_logger('test_logger')
        
        all_loggers = get_all_loggers()
        all_loggers['fake_logger'] = None
        
        # Original dict should not be modified
        self.assertNotIn('fake_logger', _loggers)
    
    def test_shutdown_loggers(self):
        """Test shutting down all loggers."""
        logger1 = setup_logger('logger1')
        logger2 = setup_logger('logger2')
        
        shutdown_loggers()
        
        # All loggers should be removed
        self.assertEqual(len(_loggers), 0)
        
        # Handlers should be closed and removed
        self.assertEqual(len(logger1.handlers), 0)
        self.assertEqual(len(logger2.handlers), 0)
    
    def test_logger_writes_to_file(self):
        """Test that logger actually writes to file."""
        log_file = self.test_log_dir / 'write_test.log'
        logger = setup_logger('test_logger', log_file=str(log_file))
        
        test_message = "Test log message"
        logger.info(test_message)
        
        # Force flush
        for handler in logger.handlers:
            handler.flush()
        
        # Check that file exists and contains the message
        self.assertTrue(log_file.exists())
        with open(log_file, 'r') as f:
            content = f.read()
            self.assertIn(test_message, content)
    
    def test_logger_format(self):
        """Test that logger uses correct format."""
        log_file = self.test_log_dir / 'format_test.log'
        logger = setup_logger('test_logger', log_file=str(log_file))
        
        logger.info("Test message")
        
        # Force flush
        for handler in logger.handlers:
            handler.flush()
        
        # Check format includes expected components
        with open(log_file, 'r') as f:
            content = f.read()
            # Should contain timestamp, logger name, level, and message
            self.assertIn('test_logger', content)
            self.assertIn('INFO', content)
            self.assertIn('Test message', content)
    
    def test_rotating_file_handler_configuration(self):
        """Test that rotating file handler is configured correctly."""
        log_file = self.test_log_dir / 'rotating_test.log'
        logger = setup_logger('test_logger', log_file=str(log_file))
        
        # Find the rotating file handler
        rotating_handler = None
        for handler in logger.handlers:
            if type(handler).__name__ == 'RotatingFileHandler':
                rotating_handler = handler
                break
        
        self.assertIsNotNone(rotating_handler)
        # Check max bytes (10MB)
        self.assertEqual(rotating_handler.maxBytes, 10 * 1024 * 1024)
        # Check backup count
        self.assertEqual(rotating_handler.backupCount, 5)
    
    def test_logger_levels_hierarchy(self):
        """Test different log levels work correctly."""
        log_file = self.test_log_dir / 'levels_test.log'
        logger = setup_logger('test_logger', log_file=str(log_file), level='DEBUG')
        
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")
        
        # Force flush
        for handler in logger.handlers:
            handler.flush()
        
        # Check all messages are in the file
        with open(log_file, 'r') as f:
            content = f.read()
            self.assertIn("Debug message", content)
            self.assertIn("Info message", content)
            self.assertIn("Warning message", content)
            self.assertIn("Error message", content)
            self.assertIn("Critical message", content)


if __name__ == '__main__':
    unittest.main()

# Made with Bob
