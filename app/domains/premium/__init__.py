"""
Premium домен: тарифы, подписки, квоты/лимиты.

Постепенный перенос:
- models/premium.py       -> domains/premium/models.py
- services/plans.py       -> domains/premium/plans.py
- services/user_quota.py  -> domains/premium/quotas.py
- api/admin_premium.py    -> domains/premium/api_admin.py
- api/premium_limits.py   -> domains/premium/api_public.py
"""
