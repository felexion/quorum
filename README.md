# Quorum

**Quorum** is a complete, offline-capable meeting management system designed for organizations that need to keep their data local. It handles everything from attendance and quorum calculations to minute-logging and report generation—no internet connection required.

## Key Features

* **Offline First:** Runs entirely on a local machine using a lightweight SQLite database.
* **Meeting Management:** Schedule meetings with types (Regular, Special, Emergency, etc.) and pre-set agendas.
* **Live Quorum Calculator:** Automatically tracks attendance and alerts you when quorum is met.
* **Minutes & Motions:** Log motions (Proposer, Seconder, Result) and discussion statements in real-time.
* **Agenda Linking:** Link specific motions and statements to agenda items for organized reporting.
* **Report Generation:** One-click generation of professional, printer-friendly Minutes of the Meeting.
* **Customizable:** Set your Organization Name, Logo, and System Theme (Color Palette) via Settings.

## Tech Stack

* **Backend:** Python (Flask)
* **Database:** SQLite (via Flask-SQLAlchemy)
* **Frontend:** HTML5, CSS3, Bootstrap 5 (Static/Local)

## Installation & Setup

1.  **Clone the repository**
    ```bash
    git clone [https://github.com/felexion/quorum.git](https://github.com/felexion/quorum.git)
    cd quorum
    ```

2.  **Create a Virtual Environment**
    ```bash
    # Windows
    python -m venv venv
    venv\Scripts\activate

    # Linux/Mac
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install Flask Flask-SQLAlchemy
    ```

4.  **Initialize Folders**
    Ensure the upload directory exists for organization logos:
    ```bash
    mkdir -p static/uploads
    ```

5.  **Run the Application**
    ```bash
    python app.py
    ```
    The application will start at `http://127.0.0.1:5000`.

## Usage Workflow

1. **Setup:** Go to **Settings** to define your Roles (e.g., President, Secretary) and Org details.
2.  **Members:** Go to **Members** to populate your roster.
3.  **Schedule:** Create a new meeting in the **Meetings** tab and set your Agenda.
4.  **Live Meeting:** Open the meeting to take attendance. The system will calculate Quorum.
5.  **Log:** Use the **Motions** and **Minutes Log** tabs to record the proceedings.
6.  **Report:** Click **Generate Minutes** to get a clean PDF-ready version of the events.

## Development Status

This project is currently in the **Development Phase**. Features may change, and the database schema is subject to updates.

## Author

Designed and developed by Rexvictor (felexion).
Repository: [felexion/quorum](https://github.com/felexion/quorum)