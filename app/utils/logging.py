import logging
import sys
from flask import Flask

def init_logging(app: Flask):
    """
    Initializes standard console stream logging for the Flask application.
    Sets levels and message format.
    """
    # Remove default handlers if any to avoid duplicated logs
    for handler in app.logger.handlers[:]:
        app.logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s (%(filename)s:%(lineno)d): %(message)s'
    )
    handler.setFormatter(formatter)
    
    # Configure level based on debug status
    if app.debug:
        app.logger.setLevel(logging.DEBUG)
        handler.setLevel(logging.DEBUG)
    else:
        app.logger.setLevel(logging.INFO)
        handler.setLevel(logging.INFO)

    app.logger.addHandler(handler)
    app.logger.info("Logging initialized successfully.")
