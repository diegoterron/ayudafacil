import logging
import sys

# Configure root logger to write to stdout/stderr in a standardized way
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Provide a standard logger for the application components
logger = logging.getLogger("ayudafacil")
