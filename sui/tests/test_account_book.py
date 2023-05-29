from unittest import TestCase
from sui.client import AccountBook


class TestAccountBook(TestCase):
    def test_parse_account_list(self):
        with open("data/new_txn.html") as f:
            html = f.read()
        account_book = AccountBook()
        account_book.parse_account_book_meta(html)
        # TODO verify data correctness
