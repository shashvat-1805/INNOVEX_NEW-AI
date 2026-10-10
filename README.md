# INNOVEX — No Node.js version

This package runs the INNOVEX demo UI using Python's built-in HTTP server and SQLite database. **Node.js, npm, and `pip install` are not required.**

## Requirements

- Python 3.10+ recommended (Python 3.8+ may also work)
- Windows, macOS, or Linux

## Run on Windows

1. Extract the ZIP file to a normal folder, for example `C:\Users\YourName\Downloads\innovex_no_node`.
2. Open that folder in File Explorer.
3. Click the address bar, type `powershell`, and press Enter.
4. Run:

   ```powershell
   python --version
   python app.py
   ```

   If `python` is not recognized, try `py --version` and then `py app.py`.
5. Open **http://127.0.0.1:3000** in your browser.
6. Keep the PowerShell window open while using the app. Press `Ctrl+C` to stop it.

## Data storage

The app stores its shared demo workspace in `data/innovex.sqlite3`. The database is created automatically the first time the server starts. Browser local storage is also used by the frontend.

## Included endpoints

- `GET /api/health`
- `GET /api/demo/state`
- `PUT /api/demo/state`

## Important scope note

This no-Node package preserves the current frontend and its shared, persistent demo workspace. It does **not** port the separate authenticated Express REST API (registration/login, roles/permissions, challenge API endpoints, audit, and admin endpoints) to Python. The frontend currently syncs its workflow state through `/api/demo/state`; this package supports that workflow for local demos. Do not expose this unauthenticated demo server to the public internet or use it for sensitive information.
