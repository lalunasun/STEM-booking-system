# CSAA Backend

Django REST API for the CSAA course registration system.

## Local Setup

Build the frontend first from `../frontend`:

```powershell
npm install
npm run build
```

Then start Django:

```powershell
python -m pip install -r requirements-local.txt
python manage.py runserver 127.0.0.1:8000
```

The API and built frontend will both run at `http://127.0.0.1:8000`.

Admin app entry:

```text
http://127.0.0.1:8000/admin/schedule
```
