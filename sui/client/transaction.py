from dataclasses import dataclass


@dataclass
class SuiDate:
    date: int
    day: int
    hours: int
    minutes: int
    month: int
    seconds: int
    time: int
    timezoneOffset: int
    year: int


@dataclass
class SuiTransaction:
    account: int
    buyerAcount: str
    buyerAcountId: int
    categoryIcon: str
    categoryId: int
    categoryName: str
    content: str
    currencyAmount: float
    date: SuiDate
    imgId: int
    itemAmount: float
    memberId: int
    memberName: str
    memo: str
    projectId: int
    projectName: str
    relation: str
    sId: str
    sellerAcount: str
    sellerAcountId: int
    tranId: int
    tranType: int
    tranName: str
    transferStoreId: int
    url: str
