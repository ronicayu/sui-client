import hashlib
import json
import logging
from collections import namedtuple
from datetime import datetime
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup

from sui.client.constants import TransactionType

LoginUrl = "https://login.sui.com"
BaseUrl = "https://www.sui.com"

MaxAuthRedirectCount = 5

VCCodeInfo = namedtuple("VCCode", ["vc_code", "uid"])


class SuiApi:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
                                        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36'})

    def login(self, email, password):
        vccode_info = self._get_vccode()

        self._verify_user(vccode_info, email, password)
        self._auth_redirect("GET", LoginUrl + "/auth.do", None, 0)

    def _get_vccode(self):
        resp = self.session.get(LoginUrl + "/login.do?opt=vccode")
        if resp.status_code != 200:
            raise f"Failed to get VCCode: {resp.status_code}"

        resp_info = json.loads(resp.text)

        if "vccode" not in resp_info:
            raise "Couldn't find VCCode in response"

        return VCCodeInfo(resp_info["vccode"], resp_info["uid"])

    def _verify_user(self, vccode_info, email, password):
        def hex_sha1(input_string):
            sha1sum = hashlib.sha1(input_string.encode()).hexdigest()
            return sha1sum

        password = hex_sha1(password)
        password = hex_sha1(email + password)
        password = hex_sha1(password + vccode_info.vc_code)

        data = {
            "email": email,
            "status": "1",  # 是否保持登录状态: 0不保持、1保持
            "password": password,
            "uid": vccode_info.uid,
        }
        resp = self.session.get(LoginUrl + "/login.do?" + urlencode(data))
        if resp.status_code != 200:
            raise f"Error: {resp.status_code}"

        resp_info = json.loads(resp.text)

        if "status" not in resp_info:
            raise "status not found"

        status = resp_info["status"]

        if status == 'ok':
            return
        elif status == "no":
            raise "invalid username or password"
        elif status == "lock":
            raise "account is locked, please retry later"
        elif status == "lock-status":
            raise "account is locked, please contact customer service"
        else:
            raise f"unknown status: {status}"

    def _auth_redirect(self, method, address, data, jump_count):
        logging.info(f"{jump_count}th redirection: {method} {address}, data: {data}")

        if jump_count > MaxAuthRedirectCount:
            raise "Too many redirection"

        if method == "POST":
            resp = self.session.post(address, data=data)
        elif method == "GET":
            resp = self.session.get(address, params=data)
        else:
            raise "Unknown method"

        soup = BeautifulSoup(resp.text, "html.parser")
        onload = soup.find("body").get("onload")
        if onload != 'document.forms[0].submit()':
            return

        form = soup.find("form")
        action = form.get("action")
        method = form.get("method")
        form_data = {}
        inputs = form.findAll("input")
        for input in inputs:
            name = input.get("name")
            value = input.get("value")
            if name is not None:
                form_data[name] = value

        self._auth_redirect(method, action, form_data, jump_count + 1)

    def switch_account_book_by_id(self, id: int):
        data = {
            'opt': 'switch',
            'switchId': str(id),
            'return': 'xxx'
        }
        resp = self.session.get(BaseUrl + "/systemSet/book.do", params=data)
        if resp.status_code != 200:
            raise f"Failed to switch account book: {resp.status_code}"

    def get_account_book_list(self):
        resp = self.session.get(BaseUrl + "/report_index.do")
        if resp.status_code != 200:
            raise f"Failed to get account book list: {resp.status_code}"
        return resp.text

    def get_account_book_meta(self):
        resp = self.session.get(BaseUrl + '/tally/new.do')
        if resp.status_code != 200:
            raise f"Failed to get account book meta: {resp.status_code}"

        return resp.text

    def add_income(self, store, memo, category_id, project_id, member_id, txn_time, amount: float, account_id: int):
        return self._create_or_update_transaction(0, TransactionType.INCOME, store, memo, category_id, project_id,
                                                  member_id, txn_time, amount, account_id)

    def add_payout(self, store, memo, category_id, project_id, member_id, txn_time, amount: float, account_id: int):
        return self._create_or_update_transaction(0, TransactionType.PAYOUT, store, memo, category_id, project_id,
                                                  member_id, txn_time, amount, account_id)

    def add_transfer(self, store, memo, category_id, project_id, member_id, txn_time, amount: float, seller_id: int,
                     buyer_id: int):
        return self._create_or_update_transaction(0, TransactionType.TRANSFER, store, memo, category_id, project_id,
                                                  member_id, txn_time, amount, None, seller_id, buyer_id)

    def _create_or_update_transaction(self, txn_id, txn_type, store, memo, category_id,
                                      project_id, member_id, txn_time, amount: float,
                                      account_id: int = None, seller_id: int = None, buyer_id: int = None):
        data = {
            'id': str(txn_id),
            'store': store,
            'memo': memo,
            'category': str(category_id),
            'project': str(project_id),
            'member': str(member_id),
            'time': txn_time.strftime("%Y-%m-%d %H:%M"),
            'price': amount
        }

        uri = '/tally/'
        if txn_type == TransactionType.INCOME:
            uri += 'income.rmi'
            data['account'] = str(account_id)
        elif txn_type == TransactionType.PAYOUT:
            uri += 'payout.rmi'
            data['account'] = str(account_id)
        elif txn_type == TransactionType.TRANSFER:
            uri += 'transfer.rmi'
            data['in_account'] = str(seller_id)
            data['out_account'] = str(buyer_id)

        resp = self.session.post(BaseUrl + uri, data=data)
        if resp.status_code != 200:
            raise f"Failed to create transaction: {resp.status_code}"

        if 'id:' not in resp.text:
            raise f"Failed to create transaction: {resp.text}"
        # sample: '{id:{id:21695292018743},price:100}'
        id_str = resp.text.removeprefix('{id:{id:')
        id_str = id_str[:id_str.rfind('},')]
        return id_str

    def update_transaction(self):
        pass

    def delete_transaction(self, txn_ids: [int]):
        data = {
            'ids': ','.join(txn_ids),
            'opt': 'batchDel'
        }
        resp = self.session.post(BaseUrl + '/tally/new.rmi', data=data)
        if resp.status_code != 200:
            raise f"Failed to delete transactions: {resp.status_code}"

        return resp.text

    def get_transactions(self, begin_date: datetime, end_date: datetime):
        page = 1
        transaction_list = []
        while True:
            resp_json = self._get_transaction_one_page(begin_date, end_date, page)
            for grp in resp_json['groups']:
                transaction_list.extend(grp['list'])
            if resp_json['pageNo'] == resp_json['pageCount']:
                break
            page += 1

        return transaction_list

    def _get_transaction_one_page(self, begin_date: datetime, end_date: datetime, page: int):
        data = {
            'page': str(page),
            'opt': 'list2',
            'beginDate': begin_date.strftime("%Y.%m.%d"),
            'endDate': end_date.strftime("%Y.%m.%d"),
            'bids': '0',
            'cids': '0',
            'mids': '0',
            'pids': '0',
            'sids': '0',
            'memids': '0',

        }
        resp = self.session.post(BaseUrl + '/tally/new.rmi', data=data)
        if resp.status_code != 200:
            raise f"Failed to get transactions: {resp.status_code}"

        json_data = json.loads(resp.text)
        return json_data
