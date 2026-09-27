# VEERA’S CAKE – Digital Cake Catalog

Mobile-friendly Flask + SQLite catalog with Admin Panel.

## Included
- Customer catalog with search/category filter
- Eggless cake catalog branding
- WhatsApp order button: 9284248422
- Admin login
- Add / Edit / Delete cake
- Upload cake photo
- Price, weight, category, description
- Available / Out of Stock toggle
- Health endpoint: `/health`
- Free-hosting deployment files: `Procfile`, `runtime.txt`
- Windows install/run `.bat` files

## Default local admin
- Username: `admin`
- Password: `123456`

**Change these for a public deployment** using environment variables:
- `ADMIN_USER`
- `ADMIN_PASSWORD`
- `SECRET_KEY`

## Windows 11
1. Install Python 3.12.
2. Extract this ZIP.
3. Double-click `install_windows.bat`.
4. Double-click `run_windows.bat`.
5. Open `http://127.0.0.1:5000`
6. Admin: `http://127.0.0.1:5000/login`

## Free hosting
This project is ready for common Python web hosts that support Gunicorn. Set the start command from the Procfile (`gunicorn app:app`).

Important: SQLite database and uploaded images are stored on the server filesystem. Some free hosts use ephemeral storage, so database/uploads may be reset after redeploy/restart. For a permanent public catalog, use a host with persistent storage or move images/database to persistent external storage.

## QR code
After the site is deployed, create one permanent QR code pointing to the public catalog URL (the `/` page). The QR does not need to change when you add/edit cakes because the catalog URL stays the same.

## Logo
The catalog currently uses text branding `VEERA’S CAKE`. A new logo can be added later without changing the catalog data.
