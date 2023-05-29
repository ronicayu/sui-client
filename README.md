# Sui (随手记) python client
It provides a below features:
- get account book details. e.g. categories, accounts, members, projects, etc.
- create new transaction record.
- get transaction records by date range.
- delete transactions by id.


# Requirements
python 3.10+

# Install
`pip install git+https://github.com/ronicayu/sui-client.git`

# Example
```python
from sui.client import SuiClient
from datetime import datetime

client = SuiClient()
client.login("<sui username>", "<password>")
client.get_account_list()
client.switch_account_book("<account book name>")
client.get_account_book_meta()
# add a new income transaction
txn_id = client.add_income("现金", 100, "test", None, None, "工资收入", None, datetime.now())
# get transactions by date range
txns = client.get_transactions(datetime(2023, 5, 1), datetime(2023, 5, 28))
# delete transaction by id
client.delete_transaction(txn_id)
```