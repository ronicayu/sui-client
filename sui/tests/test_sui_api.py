import datetime
from unittest import TestCase
from unittest.mock import patch

import requests
from requests.cookies import MockResponse
from rest_framework import status
from datetime import datetime
from sui.client.sui_api import SuiApi


class TestSuiApi(TestCase):
    @patch('requests.Session')
    def test_get_transactions(self, mock_session):
        session = requests.Session()
        sui_api = SuiApi()
        session_instance = mock_session.return_value
        mock_session:MockResponse = session_instance.post.return_value
        mock_session.status_code = status.HTTP_200_OK
        with open("data/get_txn.json") as f:
            mock_session.text = f.read()
        txns = sui_api.get_transactions(datetime(2023,5,1), datetime(2023,5,28))
        self.assertEqual(len(txns), 4)


