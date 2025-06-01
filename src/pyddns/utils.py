"""
Configuration and Storage Utilities

This module provides utility functions to access singleton instances of
the `Config` and `Storage` classes used in the Dynamic DNS (DDNS) application.
These functions ensure that there is a single instance of each class throughout
the application, promoting efficient resource management and consistent access
to configuration settings and data storage.
"""

from pyddns.config import Config
from pyddns.cache import Storage

root_config = Config()


def _get_config() -> Config:
    """returns the singleton config instance."""
    return root_config


root_storage = Storage()


def _get_storage() -> Storage:
    """returns the singleton storage instance."""
    return root_storage
