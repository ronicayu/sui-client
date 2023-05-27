from datetime import datetime

from .account_book import AccountBook
from .sui_api import SuiApi
from .transaction import SuiTransaction


class Client:
    def __init__(self):
        self.suiApi = SuiApi()
        self.verbose = False
        self.account_book = AccountBook()

    def login_and_init(self, email, password, account_book_name):
        self.login(email, password)
        self.get_account_list()
        self.switch_account_book(account_book_name)
        self.get_account_book_meta()

    def login(self, email, password):
        self.suiApi.login(email, password)

    def get_account_list(self):
        resp = self.suiApi.get_account_book_list()
        self.account_book.parse_account_list(resp)

    def switch_account_book(self, name: str):
        if name in self.account_book.account_books:
            account_id = self.account_book.account_books[name]
            self.suiApi.switch_account_book_by_id(account_id)
            self.account_book.set_account_book(name)
            return
        raise f"Couldn't find account book: {name}"

    def get_account_book_meta(self):
        resp = self.suiApi.get_account_book_meta()
        self.account_book.parse_account_book_meta(resp)

    def add_income(self, account_name, amount: float, memo, store_name, project_name, category_name, member_name, dt):
        account_id = self.account_book.get_account_id(account_name)
        store_id = 0 if store_name is None else self.account_book.get_store_id(store_name)
        project_id = 0 if project_name is None else self.account_book.get_project_id(project_name)
        category_id = self.account_book.get_category_id(category_name)
        member_id = 0 if member_name is None else self.account_book.get_member_id(member_name)

        return self.suiApi.add_income(store=store_id,
                                      memo=memo,
                                      project_id=project_id,
                                      amount=amount,
                                      account_id=account_id,
                                      category_id=category_id,
                                      member_id=member_id,
                                      txn_time=dt)

    def delete_transaction(self, txn_id):
        self.suiApi.delete_transaction([txn_id])

    def delete_transactions(self, txn_ids):
        self.suiApi.delete_transaction(txn_ids)

    def get_transactions(self, begin_date: datetime, end_date: datetime):
        transactions = self.suiApi.get_transactions(begin_date, end_date)
        sui_transactions = []
        for txn in transactions:
            sui_txn = SuiTransaction(**txn)
            sui_transactions.append(sui_txn)
        return sui_transactions
