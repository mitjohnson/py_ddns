import unittest, os

from ddns.config import Config, ConfigParser
class TestConfig(unittest.TestCase):
    def setUp(self):
        """Create a temporary configuration file for testing."""
        
        self.config_file = 'test_ddns.ini'
        self.config_content = """
        [Cloudflare]
        api_token = test_token
        zone_id = test_zone_id
        """
        with open(self.config_file, 'w') as f:
            f.write(self.config_content)

    def tearDown(self):
        """Remove the temporary configuration file after tests."""
        if os.path.exists(self.config_file):
            os.remove(self.config_file)

    def test_load_config(self):
        """Test if the configuration file loads correctly."""
        config = Config(self.config_file)
        self.assertIsInstance(config.config, ConfigParser)
        self.assertTrue(config.config.has_section('Cloudflare'))

    def test_get_option(self):
        """Test retrieving an option from the configuration."""
        config = Config(self.config_file)
        api_token = config.get('Cloudflare', 'api_token')
        self.assertEqual(api_token, 'test_token')

    def test_get_non_existent_option(self):
        """Test retrieving a non-existent option raises KeyError."""
        config = Config(self.config_file)
        with self.assertRaises(KeyError):
            config.get('Cloudflare', 'non_existent_option')

    def test_file_not_found(self):
        """Test that a FileNotFoundError is raised for a non-existent file."""
        with self.assertRaises(FileNotFoundError):
            Config('non_existent_file.ini')

if __name__ == '__main__':
    unittest.main()