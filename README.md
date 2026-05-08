# CSAA Course Registration System

Student course registration system for managing courses, rooms, schedules, terms, parents, children, and enrollment orders.

## Project Structure

```text
csaa-course-system/
  backend/    Django + Django REST Framework API
  frontend/   Vue 3 + Vite admin and parent-facing web app
```

## Local Development

Open two terminals.

### 1. Start Backend

```powershell
cd backend
python -m pip install -r requirements-local.txt
python manage.py runserver 127.0.0.1:8000
```

Backend API: `http://127.0.0.1:8000`

### 2. Start Frontend

```powershell
cd frontend
npm install
npm run dev
```

Frontend app: `http://127.0.0.1:8080`

## Set Up on Another Computer

```powershell
git clone https://github.com/lalunasun/csaa-booking-system.git
cd csaa-booking-system
```

Then start the backend:

```powershell
cd backend
python -m pip install -r requirements-local.txt
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

Open a second terminal and start the frontend:

```powershell
cd frontend
npm install
npm run dev
```

If you want to keep the same local test data on another computer, copy `backend/db.sqlite3` manually from this computer because it is ignored by Git.

### Local Admin Login

```text
Username: test
Password: test
```

## Notes

- `backend/db.sqlite3` is local development data and is ignored by Git.
- The frontend defaults to `http://127.0.0.1:8000` for API calls.
- For another API host, set `VITE_API_BASE_URL` before starting the frontend.
