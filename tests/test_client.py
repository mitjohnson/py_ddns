import unittest
from unittest.mock import patch, Mock
import logging, requests
from ddns.src.client import DDNS_Client

class TestDDNSClient(DDNS_Client):
    def update_dns(self, ip_address: str, record_name: str) -> None:
        # bstract
        pass

class TestDDNSClientMethods(unittest.TestCase):

    @patch('requests.get')
    def test_get_ip_success(self, mock_get):
        # Mock the response from requests.get
        mock_get.return_value = Mock(status_code=200, text='192.0.2.1')
        
        client = TestDDNSClient()
        ip_address = client._get_ip()
        
        self.assertEqual(ip_address, '192.0.2.1')
        mock_get.assert_called_once_with('https://api.ipify.org')

    @patch('requests.get')
    def test_get_ip_failure(self, mock_get):
        # Mock a request exception
        mock_get.side_effect = requests.exceptions.RequestException("Network error")
        
        client = TestDDNSClient()
        
        with self.assertRaises(requests.exceptions.RequestException):
            client._get_ip()
        
        # Check that the error was logged
        with self.assertLogs('root', level='ERROR') as log:
            with self.assertRaises(requests.exceptions.RequestException):
                client._get_ip()
            self.assertIn("Error getting IP: Network error", log.output[0])

if __name__ == '__main__':
    unittest.main()
