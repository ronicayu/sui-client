from collections import namedtuple
from dataclasses import dataclass
from typing import Dict

from bs4 import BeautifulSoup

from sui.client.constants import TransactionType

Category = namedtuple('Category', ['id', 'name', 'type', 'isSub', 'sub_ids'])


@dataclass
class AccountBookMeta:
    categories: Dict[str, Category]
    stores: Dict[str, int]
    members: Dict[str, int]
    accounts: Dict[str, int]
    projects: Dict[str, int]


def parse_category(id_str):
    id_str = id_str[:id_str.rfind('-')]
    if 'cCat-out-' in id_str:
        category_type = TransactionType.PAYOUT
        id_str = id_str.replace('cCat-out-', '')
    elif 'cCat-in-' in id_str:
        category_type = TransactionType.INCOME
        id_str = id_str.replace('cCat-in-', '')
    else:
        return None, None
    return int(id_str), category_type


def parse_categories(soup):
    categories = {}
    category_list = soup.find("div", id="panel-category").findAll('a')
    for category in category_list:
        id_str = category.get('id')
        id, category_type = parse_category(id_str)
        name = category.text

        is_sub = 'ctit' in category.get('class')
        sub_ids = []
        if is_sub:
            sub_class = id_str[:id_str.rfind('-a')]
            sub_categories = category.parent.findAll('a', class_=sub_class)
            sub_ids = []
            for sub_category in sub_categories:
                sub_id_str = sub_category.get('id')
                sub_id, _ = parse_category(sub_id_str)
                sub_ids.append(sub_id)
        categories[name] = Category(id, name, category_type, is_sub, sub_ids)
    return categories


def parse_id_names(doc, zone: str):
    prefix = 'c' + zone[:3].title() + '-'
    id_names = {}
    elements = doc.find('div', id='panel-' + zone).findAll('a')
    for element in elements:
        id_str = element.get('id')
        if id_str == prefix + 'a':
            continue
        id_str = id_str[:id_str.rfind('-')]
        id_str = id_str[len(prefix):]
        id_int = int(id_str)
        name = element.text
        id_names[name] = id_int
    return id_names


class AccountBook:
    def __init__(self):
        self.account_books = {}
        self.account_book_meta: AccountBookMeta = None
        self.current_account_book = None

    def get_account_id(self, name):
        return self.account_book_meta.accounts[name]

    def get_category_id(self, name):
        return self.account_book_meta.categories[name].id

    def get_store_id(self, name):
        return self.account_book_meta.stores[name]

    def get_member_id(self, name):
        return self.account_book_meta.members[name]

    def get_project_id(self, name):
        return self.account_book_meta.projects[name]

    def parse_account_list(self, html):
        soup = BeautifulSoup(html, "html.parser")
        account_list = soup.find("ul", class_="s-accountbook-all").findAll('li')
        if len(account_list) == 0:
            raise "Couldn't find account book list"

        for account in account_list:
            name = account.get('title')
            id_str = account.get('data-bookid')
            if id_str is not None:
                self.account_books[name] = int(id_str)

    def set_account_book(self, name):
        self.current_account_book = name

    def parse_account_book_meta(self, html):
        soup = BeautifulSoup(html, "html.parser")
        # 解析分类
        categories = parse_categories(soup)

        dropdowns = soup.find('div', id='filter-bar').find('div', class_='fb-choose')

        stores = parse_id_names(dropdowns, 'store')
        members = parse_id_names(dropdowns, 'member')
        accounts = parse_id_names(dropdowns, 'account')
        projects = parse_id_names(dropdowns, 'project')
        self.account_book_meta = AccountBookMeta(categories, stores, members, accounts, projects)
