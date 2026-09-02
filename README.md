# Prod Manager

A lightweight desktop production-management app: Products, Production In,
Production Out, and a searchable Movement Log — with Excel export
everywhere you need to save daily records.

## What's included

- `main.py` — entry point
- `app.py` — the GUI (Products / Production In / Production Out / Movement Log tabs)
- `database.py` — local SQLite storage (`prod_manager.db`, created automatically next to the app)
- `excel_utils.py` — formatted `.xlsx` export
- `searchable_combo.py` — the "type to search a model" widget (no more scrolling)
- `icon.ico` — the app icon
- `requirements.txt`, `build.bat` — for turning this into a Windows `.exe`

## Features (matching your list)

1. **Products tab** — Excel export instead of CSV.
2. **Production In / Production Out** — the "Model" field in the add-record
   form is a type-to-search box: start typing a model number or name and a
   filtered list appears instantly, instead of scrolling a long dropdown.
3. **Movement Log** — a "Search by model" box filters the log live, plus
   Type and Date-range filters.
4. **Excel export** — available on Products, Production In, Production Out,
   and Movement Log, each pre-named with today's date
   (e.g. `Production_In_2026-09-02.xlsx`) for easy daily saving.
5. **Professional icon** — `icon.ico`, applied to both the window and the
   compiled `.exe`.

Stock is tracked automatically: a Production In record increases a
product's stock, a Production Out record decreases it — you can see the
running total in the Products tab.

## Running it on Windows (no compiling needed)

1. Install Python 3.10+ from python.org (check "Add python.exe to PATH"
   during setup). Tkinter is included automatically with the official
   Windows installer.
2. Open a terminal in this folder and run:
   ```
   pip install -r requirements.txt
   python main.py
   ```

## Building your own Prod_Manager.exe

### Option A — you have a Windows PC
1. Do the two steps above once (`pip install -r requirements.txt`).
2. Double-click `build.bat` (or run it from a terminal in this folder).
3. Your new installer-free executable appears at `dist\Prod_Manager.exe`.
   You can copy that single file anywhere on a Windows PC and run it —
   it will create its `prod_manager.db` file next to itself the first
   time it runs.

### Option B — no Windows PC needed (free GitHub Actions build)
This project includes `.github/workflows/build-exe.yml`, which tells
GitHub to build `Prod_Manager.exe` for you automatically on a free
Windows cloud machine, no install or command line needed on your side.

1. Create a free account at github.com if you don't have one.
2. Click "New repository", give it any name (e.g. `prod-manager`), keep
   it Private or Public, click "Create repository".
3. On the new repo's page, click "uploading an existing file" (or
   "Add file" → "Upload files").
4. Drag in **everything inside this `prod_manager` folder**. If your
   file browser hides the `.github` folder (since it starts with a dot)
   and it doesn't get uploaded, that's fine — instead, in your GitHub
   repo click "Add file" → "Create new file", type the path
   `.github/workflows/build-exe.yml` as the filename (GitHub will
   create the folders automatically), then copy-paste the contents of
   that file from this project and commit.
5. Click "Commit changes". This automatically starts the build.
6. Click the "Actions" tab at the top of your repo → open the run that
   just started (a few minutes) → once it finishes, scroll down to
   "Artifacts" → download **Prod_Manager-windows-exe**. That's your
   portable `Prod_Manager.exe`.

If you'd rather ship it as a proper installer (Setup wizard, Start Menu
shortcut, uninstaller) instead of a single `.exe`, the free **Inno Setup**
tool can wrap `dist\Prod_Manager.exe` into one — happy to write that
`.iss` script too if you want that later.

## Notes / next steps

- All data is stored locally in `prod_manager.db` (SQLite) next to the
  app — nothing is sent anywhere.
- If you want multi-user network access, a login screen, PDF export,
  or anything else added, just ask — this is meant as a base you and I
  can keep extending now that we have the actual source code.
