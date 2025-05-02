# TellTail Logging Module

This module provides centralized logging for the TellTail Discord bot.

## Features

- Unified logging format across all components
- Console output with timestamps
- Rotating file logs (in `/logs` directory) with more detailed information
- File rotation at 10MB with 5 backup files

## Usage

```python
from services.logging import logger

# Use the logger in your code
logger.info("This is an info message")
logger.warning("This is a warning message")
logger.error("This is an error message")
logger.debug("This is a debug message")
```

## Custom Loggers

If you need a separate named logger for a specific component:

```python
from services.logging import setup_logger

# Create a custom logger
my_logger = setup_logger("component_name")
my_logger.info("Component-specific log")
```

## Log Files

Log files are stored in the `/logs` directory with automatic rotation:
- `telltail.log` - Current log file
- `telltail.log.1` through `telltail.log.5` - Backup log files 