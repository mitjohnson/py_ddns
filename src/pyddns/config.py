"""
Configuration and Storage Utilities

This module provides utility functions to access singleton instances of
the `Config` and `Storage` classes used in the Dynamic DNS (DDNS) application.
These functions ensure that there is a single instance of each class throughout
the application, promoting efficient resource management and consistent access
to configuration settings and data storage.
"""

from configparser import ConfigParser
import logging
import os


class Config:
    """
    A class to manage configuration settings using ConfigParser.

    This class loads configuration settings from a specified INI file
    and provides methods to access the settings.
    """

    def __init__(self, config_file: str = "py_ddns.ini") -> None:
        """
        Initializes the Config class and loads the configuration file.
        """
        self.config = ConfigParser()
        self.config_file = config_file
        self.load_config()
        self.setup_logging()

    def setup_logging(self) -> None:
        """
        Sets up the logging configuration for the application.
        """
        logging_level = self.config.get("Client_settings", "logging_level")

        if logging_level.lower().strip() not in ["info", "debug"]:
            raise ValueError(
                "Invalid logging level."
                f"Expected info or logging, got {logging_level}"
            )

        if logging_level.lower() == "debug":
            level = logging.DEBUG
        else:
            level = logging.INFO

        logging.basicConfig(
            level=level,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler("py_ddns.log"),
                logging.StreamHandler(),
            ],
        )
        logging.info("Logging is set up, level = %s", logging_level.upper())

    def load_config(self) -> None:
        """
        Loads the configuration from the specified file.
        """

        if not os.path.exists(self.config_file):
            raise FileNotFoundError(
                f"Configuration file '{self.config_file}' not found."
            )

        self.config.read(self.config_file)

    def get(self, section: str, option: str) -> str:
        """
        Retrieves the value of a specified option from a given section.

        Args:
            section (str): The section in the configuration file.
            option (str): The option within the section.

        Raises:
            KeyError: If the specified option does not exist in the section.
        """

        if self.config.has_option(section, option):
            return self.config.get(section, option)

        raise KeyError(f"Option '{option}' not found in section '{section}'.")
