# 📝 راهنمای تست‌های پروژه

این دایرکتوری شامل تست‌های pytest برای پروژه FastAPI است.

## 📂 ساختار فایل‌های تست

```text
tests/
├── conftest.py       # کانفیگ‌ها و fixture های pytest
├── test_api.py       # تست‌های API endpoints
└── README.md         # این فایل
```

## 🔧 فایل‌های اصلی

### `conftest.py`

این فایل شامل تمام کانفیگ‌های pytest و fixture های قابل استفاده مجدد است:

**Fixtures موجود:**

- `setup_test_database`: ایجاد و حذف database برای تست‌ها
- `db_session`: session دیتابیس برای تست‌ها
- `override_dependencies`: override کردن dependencies در FastAPI
- `client`: TestClient برای ارسال request به API
- `test_user`: ایجاد یک کاربر تستی در database
- `authenticated_client`: client با authentication (دارای cookies)
- `test_user_credentials`: اطلاعات کاربری برای تست signup/login
- `sample_cost_data`: داده‌های نمونه برای تست cost

### `test_api.py`

این فایل شامل تمام تست‌های API endpoints است که به صورت class-based سازماندهی شده‌اند:

**کلاس‌های تست:**

1. `TestRootEndpoint`: تست endpoint اصلی
2. `TestAuthentication`: تست‌های احراز هویت (signup, login, logout, refresh)
3. `TestCostCRUD`: تست‌های CRUD برای cost
4. `TestAuthorization`: تست‌های authorization (دسترسی کاربران)
5. `TestDataValidation`: تست‌های validation داده‌ها

## 🚀 اجرای تست‌ها

### اجرای تمام تست‌ها

```bash
pytest
```

### اجرای تست‌های یک کلاس خاص

```bash
pytest tests/test_api.py::TestAuthentication
```

### اجرای یک تست خاص

```bash
pytest tests/test_api.py::TestAuthentication::test_login_success
```

### اجرای با نمایش print ها

```bash
pytest -s
```

### اجرای با coverage

```bash
pytest --cov=. --cov-report=html
```

### اجرای تست‌های failed

```bash
pytest --lf
```

### اجرای تست‌های با marker خاص

```bash
pytest -m auth
pytest -m crud
pytest -m "not slow"
```

## 📊 گزارش Coverage

برای دریافت گزارش coverage:

```bash
pip install pytest-cov
pytest --cov=. --cov-report=term-missing
pytest --cov=. --cov-report=html
```

فایل HTML گزارش در `htmlcov/index.html` ایجاد می‌شود.

## 🧪 نوشتن تست جدید

### مثال 1: تست ساده

```python
def test_example(client):
    response = client.get("/")
    assert response.status_code == 200
```

### مثال 2: تست با authentication

```python
def test_protected_endpoint(authenticated_client):
    response = authenticated_client.get("/costs")
    assert response.status_code == 200
```

### مثال 3: تست با داده‌های دیتابیس

```python
def test_with_db(db_session, test_user):
    assert test_user.id is not None
    assert test_user.user_name == "testuser"
```

## 📝 نکات مهم

1. **تست‌ها مستقل هستند**: هر تست باید مستقل از تست‌های دیگر باشد
2. **Database در حافظه است**: از SQLite in-memory استفاده می‌شود
3. **Cleanup خودکار است**: بعد از هر تست، تغییرات rollback می‌شوند
4. **Authentication با Cookie**: تست‌های authenticated از cookie استفاده می‌کنند

## 🐛 دیباگ تست‌ها

### استفاده از breakpoint

```python
def test_example(client):
    import pdb; pdb.set_trace()  # یا breakpoint()
    response = client.get("/")
    assert response.status_code == 200
```

### نمایش output

```bash
pytest -s -v
```

### اجرای با پرینت جزئیات

```bash
pytest --tb=long -vv
```

## 📈 بهبود تست‌ها

چیزهایی که می‌توان اضافه کرد:

- [ ] تست‌های performance
- [ ] تست‌های concurrent requests
- [ ] تست‌های rate limiting
- [ ] mock کردن external services
- [ ] تست‌های integration با database واقعی
- [ ] تست‌های end-to-end

## 🔗 منابع مفید

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing Guide](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/14/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites)
