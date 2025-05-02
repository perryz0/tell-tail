"""
Test script to verify the centralized logging functionality.
"""
from services.logging import logger, setup_logger

def main():
    # Test default logger
    logger.info("Testing default logger - INFO")
    logger.warning("Testing default logger - WARNING")
    logger.error("Testing default logger - ERROR")
    logger.debug("This debug message should not appear with default INFO level")
    
    # Test custom logger
    custom_logger = setup_logger("custom_component")
    custom_logger.info("Testing custom logger - INFO")
    custom_logger.warning("Testing custom logger - WARNING")
    custom_logger.error("Testing custom logger - ERROR")
    
    print("\nCheck the logs/ directory for the log files:")
    print("- telltail.log")
    print("- custom_component.log")

if __name__ == "__main__":
    main() 