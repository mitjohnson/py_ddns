from configparser import ConfigParser
import logging, os

class Config:
    """
    A class to manage configuration settings using ConfigParser.

    This class loads configuration settings from a specified INI file
    and provides methods to access the settings.

    Attributes:
        config (ConfigParser): The ConfigParser instance that holds the configuration.
        config_file (str): The path to the configuration file.
    """

    def __init__(self, config_file: str = 'py_ddns.ini') -> None:
        """
        Initializes the Config class and loads the configuration file.

        Args:
            config_file (str): The path to the configuration file. Defaults to 'ddns.ini'.

        Raises:
            FileNotFoundError: If the specified configuration file does not exist.
        """
        self.config = ConfigParser()
        self.config_file = config_file
        self.load_config()
        self.setup_logging()

    def setup_logging(self) -> None:
        """
        Sets up the logging configuration for the application.
        """
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s', 
            handlers=[
                logging.FileHandler('py_ddns.log'),
                logging.StreamHandler()
            ]
        )
        logging.info("Logging is set up.")

    def load_config(self) -> None:
        """
        Loads the configuration from the specified file.

        Raises:
            FileNotFoundError: If the configuration file does not exist.
        """

        if not os.path.exists(self.config_file):
            raise FileNotFoundError(f"Configuration file '{self.config_file}' not found.")
        
        self.config.read(self.config_file)

    def get(self, section: str, option: str) -> str:
        """
        Retrieves the value of a specified option from a given section.

        Args:
            section (str): The section in the configuration file.
            option (str): The option within the section.

        Returns:
            str: The value of the specified option.

        Raises:
            KeyError: If the specified option does not exist in the section.
        """

        if self.config.has_option(section, option):
            return self.config.get(section, option)
        
        else:

            raise KeyError(f"Option '{option}' not found in section '{section}'.")
