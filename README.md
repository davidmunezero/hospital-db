# Hospital Management Database

A small hospital-management database project built with **Python**, **SQLAlchemy**, and **SQLite**. It defines a relational schema for hospital operations, loads CSV sample data, and produces reports and update/delete examples.

## Overview

The database tracks **patients, insurance providers, doctors, departments, appointments, prescriptions, and payments**. SQLAlchemy ORM models define the tables and their relationships; SQLite stores the data in `hospital.db`.

This repository is intended as an *educational example* of relational database design and SQLAlchemy workflows. The included CSV files contain **sample data**, not a production-ready patient record system.

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

## Database Schema

![Hospital database schema](schema.png)

| Table | Purpose |
| --- | --- |
| `insurances` | Insurance provider and coverage percentage |
| `patients` | Patient contact and birth-date details, optionally linked to insurance |
| `doctors` | Doctor specialty, rank, salary, and join date |
| `departments` | Department name and budget, optionally headed by a doctor |
| `appointments` | Appointment date, room, diagnosis, patient, and doctor |
| `prescriptions` | Prescription description associated with an appointment |
| `payments` | Payment date, category, amount, and patient |

**Foreign keys** connect related records. The scripts enable SQLite foreign-key enforcement when opening a connection, and the models include checks for values such as *positive salaries*, *positive payment amounts*, and *insurance coverage between 0 and 100*.

## Object-Relational Mapping (ORM)

Each entity in the schema diagram is represented by a **SQLAlchemy model class**. The class maps to a table through `__tablename__`, and the entity's attributes become columns with appropriate data types and constraints. For example, the insurance and patient entities map to `Insurance` and `Patient`:

```python
class Insurance(Base):
    __tablename__ = "insurances"
    insuranceID = Column(Integer, primary_key=True)
    provider = Column(String, nullable=False)
    coverage = Column(
        Float, CheckConstraint("coverage BETWEEN 0 AND 100"), nullable=False
    )
    patients = relationship("Patient", back_populates="insurance")


class Patient(Base):
    __tablename__ = "patients"
    patientID = Column(Integer, primary_key=True)
    patientName = Column(String, nullable=False)
    birthdate = Column(Date, nullable=False)
    phone = Column(String, unique=True, nullable=False)
    address = Column(String)
    insuranceID = Column(
        Integer,
        ForeignKey("insurances.insuranceID", ondelete="SET NULL", onupdate="CASCADE"),
    )
    insurance = relationship("Insurance", back_populates="patients")
    appointments = relationship("Appointment", back_populates="patient")
    payments = relationship("Payment", back_populates="patient")
```

In this mapping, `primary_key=True` identifies a table's **primary key**; `nullable=False` marks required fields; `unique=True` enforces unique phone numbers; and `CheckConstraint` restricts insurance coverage to **0–100**. The patient's `insuranceID` foreign key connects it to `insurances.insuranceID`. The `relationship()` declarations provide ORM navigation between records, while `back_populates` pairs the relationship on each model. **Relationships are not additional database columns.**

The same approach maps doctors, departments, appointments, prescriptions, and payments. For example, appointments reference both patients and doctors, prescriptions reference appointments, and payments reference patients. `Base.metadata.create_all(engine)` creates the tables from the model definitions if they do not already exist; *it does not migrate or rebuild existing tables*.

## Inserting Data

Sample records are stored as CSV files in the `data/` directory. `src/insert_data.py` reads those files and creates SQLAlchemy model objects, rather than sending raw `INSERT` statements manually. The import process has the following steps:

1. It maps each table to its CSV file using `FILE_PATHS`.
2. It verifies that every required CSV file exists.
3. It removes existing rows so that re-running the import does not create duplicates.
4. It inserts parent and child tables in foreign-key dependency order.
5. It converts date and date-time strings from CSV data into Python objects before creating ORM records.

The script begins with a dictionary that associates each model with a source file:

```python
FILE_PATHS = {
    "insurance": "../data/insurance.csv",
    "patient": "../data/patient.csv",
    "doctor": "../data/doctor.csv",
    "dept": "../data/department.csv",
    "appointment": "../data/appointment.csv",
    "prescription": "../data/prescription.csv",
    "payment": "../data/payment.csv",
}
```

Before loading data, `tables_exist()` opens every listed file and exits without starting the import if any file is missing. Existing rows are then deleted in reverse model dependency order:

```python
for table in reversed(Base.metadata.sorted_tables):
    session.execute(delete(table))
session.commit()
```

Each CSV file is read using `csv.DictReader`, which converts every row into a dictionary keyed by the CSV header. **Empty rows are skipped.** Each dictionary value is converted into the appropriate SQLAlchemy model fields, and the resulting objects are collected in a list:

```python
patients = []
with open(filepath, encoding="utf-8-sig") as file:
    reader = DictReader(file)
    for row in reader:
        if all(not record for record in row.values()) :
            continue

        patient = Patient(
            patientID=row["patientID"],
            patientName=row["patientName"],
            birthdate=date.fromisoformat(row["birthdate"]),
            phone=row["phone"],
            address=row["address"],
            insuranceID=row["insuranceID"] or None,
        )
        patients.append(patient)

session.add_all(patients)
session.commit()
```

Some relationships allow the foreign key to be absent. Therefore, foreign-key values such as `insuranceID`, `deptHead`, `patientID`, `doctorID`, and `appointmentID` are converted to `None` when their CSV value is empty. **Empty optional relationships are represented as SQL `NULL`**, not as invalid foreign-key references.

Date and date-time fields receive special conversion:

- `birthdate` and `joinDate` use `date.fromisoformat()` because they represent *dates*.
- `appointmentDate` and `paymentDate` use `datetime.fromisoformat()` because they include *time information*.
- Numeric fields such as coverage, salary, budget, and amount are passed to SQLAlchemy for *conversion and validation*.

Each insert function uses a **`Session` transaction**. `session.begin()` starts the transaction, `session.add_all()` adds a collection of ORM objects, and `session.commit()` writes the objects to SQLite. If an exception occurs, `session.rollback()` restores the database to the state before the transaction.

The insertion order is **deliberately dependency-based**:

1. **Insurance records**
2. **Patient records**
3. **Doctor records**
4. **Department records**
5. **Appointment records**
6. **Prescription records**
7. **Payment records**

This order ensures that parent records exist before a child record references them. The `main()` function performs the complete import by removing existing data and then calling the corresponding insert function for every CSV file:

```python
drop_existing_data()
insert_insurances(FILE_PATHS["insurance"])
insert_patients(FILE_PATHS["patient"])
insert_doctors(FILE_PATHS["doctor"])
insert_depts(FILE_PATHS["dept"])
insert_appointments(FILE_PATHS["appointment"])
insert_prescriptions(FILE_PATHS["prescription"])
insert_payments(FILE_PATHS["payment"])
```

## Queries and reports

Running `queries.py` writes **four CSV reports** under `../queries/`. The report functions use SQLAlchemy ORM queries or SQL executed through the session, then pass the rows to a CSV `DictWriter`.

### `q1.csv` — Patients and insurance

Lists patient names and phone numbers with their insurance provider, sorted alphabetically by patient name. The ORM query uses `joinedload` to fetch the related insurance along with each patient and *avoids a separate lookup for every patient*. Patients without linked insurance are labeled **“No Insurance.”**

```python
patients = (
    session.query(Patient)
    .options(joinedload(Patient.insurance))
    .order_by(Patient.patientName)
    .all()
)
```

### `q2.csv` — Doctor workload

Lists doctors and their appointment counts in **descending workload order**. An outer join includes doctors who have no appointments; their count is **zero**. The query groups by doctor so each doctor appears once.

```python
results = (
    session.query(
        Doctor.doctorName, func.count(Appointment.doctorID).label("count")
    )
    .outerjoin(Appointment, Doctor.doctorID == Appointment.doctorID)
    .group_by(Doctor.doctorID, Doctor.doctorName)
    .order_by(func.count(Appointment.doctorID).desc())
    .all()
)
```

### `q3.csv` — Patient payment summary

Reports patient ID and name, insurance provider, number of payments, and total amount paid. SQL joins patients to payments and insurance, groups the rows by patient and provider, and orders by total paid amount ascending. Because the insurance table is joined with an **inner `JOIN`**, patients without an insurance record are *not included* in this report.

```python
result = session.execute(text("""
    SELECT p.patientID, p.patientName, i.provider, COUNT(py.patientID) AS total_payments,
           SUM(py.amount) AS total_amount
    FROM patients p
    LEFT JOIN payments py ON py.patientID = p.patientID
    JOIN insurances i ON p.insuranceID = i.insuranceID
    GROUP BY p.patientID, p.patientName, i.provider
    ORDER BY total_amount
"""))
```

### `q4.csv` — Doctor appointment rankings

Counts appointments per doctor, including doctors with no appointments, then ranks doctors by appointment count from **highest to lowest**. A *common table expression* (CTE) names the intermediate per-doctor totals. `DENSE_RANK()` gives doctors with equal counts the **same rank**, without gaps in subsequent ranks.

```sql
WITH doctor_ap AS (
    SELECT d.doctorName, d.speciality, COUNT(ap.doctorID) AS total_appointments
    FROM doctors d
    LEFT JOIN appointments ap ON ap.doctorID = d.doctorID
    GROUP BY d.doctorID, d.doctorName
)
SELECT doctorName, speciality, total_appointments,
       DENSE_RANK() OVER (ORDER BY total_appointments DESC) AS ranking
FROM doctor_ap;
```

### Database Changes Made by the Query Script

In addition to creating reports, `queries.py` **increases the salary** of doctors with rank `Senior` by **5%** and **attempts to delete** payment record `10`. Re-running it can apply the salary increase again. **Use a copy of the database if you want to preserve the original data.**

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

`insert_data.py` loads the CSV files from `../data/` in dependency order. **The data loader deletes all existing rows in the database tables before importing the CSV data.** This is to avoid inserting duplicate records when the script is run again.

## License

This project is distributed under the [**MIT License**](LICENSE).
