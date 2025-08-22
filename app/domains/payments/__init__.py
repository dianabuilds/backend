"""
Payments домен: шлюзы, оркестратор, транзакции, комиссии и админ-API.

Постепенный перенос:
- services/payments_manager.py -> domains/payments/manager.py
- services/payments_ledger.py  -> domains/payments/ledger.py
- models/payment_gateway.py    -> domains/payments/models/gateway.py
- models/payment_transaction.py-> domains/payments/models/transaction.py
- api/admin_payments.py        -> domains/payments/api_admin.py
"""
