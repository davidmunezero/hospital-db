# Hospital Management Database

A small hospital-management database project built with Python, SQLAlchemy, and SQLite. It defines a relational schema for hospital operations, loads CSV sample data, and runs reports and update/delete examples.

## Overview

The database tracks patients, insurance providers, doctors, departments, appointments, prescriptions, and payments. SQLAlchemy ORM models define the tables and their relationships; SQLite stores the data in `hospital.db`.

This repository is intended as an educational example of relational database design and SQLAlchemy workflows. The included CSV files contain sample data, not a production-ready patient record system.

## Schema

The schema is illustrated in [`schema.png`](schema.png).

| Table | Purpose |
| --- | --- |
| `insurances` | Insurance provider and coverage percentage |
| `patients` | Patient contact and birth-date details, optionally linked to insurance |
| `doctors` | Doctor specialty, rank, salary, and join date |
| `departments` | Department name and budget, optionally headed by a doctor |
| `appointments` | Appointment date, room, diagnosis, patient, and doctor |
| `prescriptions` | Prescription description associated with an appointment |
| `payments` | Payment date, category, amount, and patient |

Foreign keys connect related records. The scripts enable SQLite foreign-key enforcement when opening a connection, and the models include checks for values such as positive salaries and payment amounts and insurance coverage between 0 and 100.

## Project contents

```text
.
├── data/                 # CSV source data for each table
├── queries/              # CSV report outputs (q1.csv through q4.csv)
├── src/
│   ├── create_tables.py  # SQLAlchemy models and table creation
│   ├── insert_data.py    # Load CSV data into the database
│   └── queries.py        # Reports and example data modifications
├── hospital.db           # SQLite database file
├── schema.png            # Database schema diagram
└── README.md
```

## Requirements

- Python 3.9 or later
- SQLAlchemy

## Setup and usage

The commands below assume you run the scripts from the `src/` directory. The scripts use relative paths to find the CSV files in `data/` and create/use `hospital.db` in the repository root.

### 1. Install dependencies

From the repository root, install SQLAlchemy:

```bash
pip install sqlalchemy
```

### 2. Configure the database

Change to the source directory and create the database tables:

```bash
cd src
python create_tables.py
```

This creates any missing tables in the SQLite database at `../hospital.db`.

### 3. Run the program

After the database has been configured, load the sample CSV data and run the reports:

```bash
python insert_data.py
python queries.py
```

`insert_data.py` loads the CSV files from `../data/` in dependency order. **The data loader deletes all existing rows in the database tables before importing the CSV data.** Back up any database contents you need before running it.

`queries.py` writes these CSV reports to `../queries/`:

1. `q1.csv` — patient names, phone numbers, and insurance providers.
2. `q2.csv` — doctors and appointment counts, ordered by workload.
3. `q3.csv` — patient payment totals and insurance providers.
4. `q4.csv` — doctors ranked by appointment count.

**Important:** `queries.py` also changes the database: it increases the salary of doctors with rank `Senior` by 5% and attempts to delete payment record `10`. Re-running it can apply the salary increase again. Use a copy of the database if you want to preserve the original data.

## Implementation

- `src/create_tables.py` defines the SQLAlchemy models and creates the schema.
- `src/insert_data.py` reads the CSV files with Python's `csv` module and inserts records using SQLAlchemy sessions.
- `src/queries.py` demonstrates ORM and SQL queries, writes report results as CSV files, and includes update and delete operations.

## License

This project is distributed under the [MIT License](LICENSE).
