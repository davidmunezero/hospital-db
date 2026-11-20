from create_tables import (
    Insurance,
    Patient,
    Doctor,
    Department,
    Appointment,
    Prescription,
    Payment,
    Base,
)
from csv import DictReader
from sqlalchemy import create_engine, event, delete
from sqlalchemy.orm import Session
from datetime import date, datetime
import sys
import traceback

FILE_PATHS = {
    "insurance": "../data/insurance.csv",
    "patient": "../data/patient.csv",
    "doctor": "../data/doctor.csv",
    "dept": "../data/department.csv",
    "appointment": "../data/appointment.csv",
    "prescription": "../data/prescription.csv",
    "payment": "../data/payment.csv",
}

# object that connects to db (in parent folder)
engine = create_engine("sqlite:///../hospital.db")


# enforce referential integrity on each new connection
@event.listens_for(engine, "connect")
def enable_foreign_keys(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def main():

    if not tables_exist(FILE_PATHS):
        sys.exit("Error: Could not insert data because some table data are missing.")

    drop_existing_data()  # to avoid duplicate data
    insert_insurances(FILE_PATHS["insurance"])
    insert_patients(FILE_PATHS["patient"])
    insert_doctors(FILE_PATHS["doctor"])
    insert_depts(FILE_PATHS["dept"])
    insert_appointments(FILE_PATHS["appointment"])
    insert_prescriptions(FILE_PATHS["prescription"])
    insert_payments(FILE_PATHS["payment"])


def drop_existing_data():
    """Removes all rows from all tables in db"""
    with Session(engine) as session:
        session.begin()
        # drop child tables before their parent tables
        try:
            for table in reversed(Base.metadata.sorted_tables):
                session.execute(delete(table))
            session.commit()
        except Exception:
            session.rollback()
            traceback.print_exc
            sys.exit("Could not remove existing data from database tables")


def tables_exist(filepaths: dict) -> bool:
    """Returns True if all tables exists in the filepaths"""

    # for each key in dictionary
    for path in filepaths.values():
        try:
            with open(path, encoding="utf-8-sig") as _:
                pass
        except FileNotFoundError:
            return False
    return True


"""These functions insert data in their corresponding tables in the db"""


def insert_insurances(filepath: str) -> None:
    # list of insurance objects
    with Session(engine) as session:
        session.begin()
        try:
            insurances = []
            valid_rows = 0
            with open(filepath, encoding="utf-8-sig") as file:
                reader = DictReader(file)
                for row in reader:
                    # skip empty rows
                    if all(not record for record in row.values()):
                        continue
                    valid_rows += 1
                    insurance = Insurance(
                        insuranceID=row["insuranceID"],
                        provider=row["provider"],
                        coverage=row["coverage"],
                    )
                    insurances.append(insurance)
            session.add_all(insurances)
            session.commit()
            if valid_rows != len(insurances):
                raise ImportError("Could not insert all insurances table rows")
        except Exception:
            session.rollback()
            traceback.print_exc()
            sys.exit(f"An unexpected error occurred")


def insert_patients(filepath: str) -> None:
    with Session(engine) as session:
        session.begin()
        try:
            patients = []
            valid_rows = 0
            with open(filepath, encoding="utf-8-sig") as file:
                reader = DictReader(file)
                for row in reader:
                    # skip empty rows
                    if all(not record for record in row.values()):
                        continue
                    valid_rows += 1
                    # handle missing fk in table
                    insuranceID = (
                        None if row["insuranceID"] == "" else row["insuranceID"]
                    )
                    patient = Patient(
                        patientID=row["patientID"],
                        patientName=row["patientName"],
                        birthdate=date.fromisoformat(row["birthdate"]),
                        phone=row["phone"],
                        address=row["address"],
                        insuranceID=insuranceID,
                    )
                    patients.append(patient)
            session.add_all(patients)
            session.commit()
            if valid_rows != len(patients):
                raise ImportError("Could not insert all patients table rows")
        except Exception:
            session.rollback()
            traceback.print_exc()
            sys.exit(f"An unexpected error occurred")


def insert_doctors(filepath: str) -> None:
    with Session(engine) as session:
        session.begin()
        try:
            doctors = []
            valid_rows = 0
            with open(filepath, encoding="utf-8-sig") as file:
                reader = DictReader(file)
                for row in reader:
                    # skip empty rows
                    if all(not record for record in row.values()):
                        continue
                    valid_rows += 1
                    doctor = Doctor(
                        doctorID=row["doctorID"],
                        doctorName=row["doctorName"],
                        speciality=row["speciality"],
                        rank=row["rank"],
                        salary=row["salary"],
                        joinDate=date.fromisoformat(row["joinDate"]),
                    )
                    doctors.append(doctor)
            session.add_all(doctors)
            session.commit()
            if valid_rows != len(doctors):
                raise ImportError("Could not insert all doctors table rows")
        except Exception:
            session.rollback()
            traceback.print_exc()
            sys.exit(f"An unexpected error occurred")


def insert_depts(filepath: str) -> None:
    with Session(engine) as session:
        session.begin()
        try:
            depts = []
            valid_rows = 0
            with open(filepath, encoding="utf-8-sig") as file:
                reader = DictReader(file)
                for row in reader:
                    # skip empty rows
                    if all(not record for record in row.values()):
                        continue
                    valid_rows += 1
                    # handle missing fk
                    deptHead = None if row["deptHead"] == "" else row["deptHead"]
                    dept = Department(
                        deptID=row["deptID"],
                        deptName=row["deptName"],
                        budget=row["budget"],
                        deptHead=deptHead,
                    )
                    depts.append(dept)
            session.add_all(depts)
            session.commit()
            if valid_rows != len(depts):
                raise ImportError("Could not insert all departments table rows")
        except Exception:
            session.rollback()
            traceback.print_exc()
            sys.exit(f"An unexpected error occurred")


def insert_appointments(filepath: str) -> None:
    with Session(engine) as session:
        session.begin()
        try:
            appointments = []
            valid_rows = 0
            with open(filepath, encoding="utf-8-sig") as file:
                reader = DictReader(file)
                for row in reader:
                    # skip empty rows
                    if all(not record for record in row.values()):
                        continue
                    valid_rows += 1
                    # handle missing fk
                    patientID = None if row["patientID"] == "" else row["patientID"]
                    doctorID = None if row["doctorID"] == "" else row["doctorID"]
                    appointment = Appointment(
                        appointmentID=row["appointmentID"],
                        appointmentDate=datetime.fromisoformat(row["appointmentDate"]),
                        roomNo=row["roomNo"],
                        diagnosis=row["diagnosis"],
                        patientID=patientID,
                        doctorID=doctorID,
                    )
                    appointments.append(appointment)
            session.add_all(appointments)
            session.commit()
            if valid_rows != len(appointments):
                raise ImportError("Could not insert all appointments table rows")
        except Exception:
            session.rollback()
            traceback.print_exc()
            sys.exit(f"An unexpected error occurred")


def insert_prescriptions(filepath: str) -> None:
    with Session(engine) as session:
        session.begin()
        try:
            prescriptions = []
            valid_rows = 0
            with open(filepath, encoding="utf-8-sig") as file:
                reader = DictReader(file)
                for row in reader:
                    # skip empty rows
                    if all(not record for record in row.values()):
                        continue
                    valid_rows += 1
                    # handle missing fk
                    appointmentID = (
                        None if row["appointmentID"] == "" else row["appointmentID"]
                    )
                    prescription = Prescription(
                        prescriptionID=row["prescriptionID"],
                        description=row["description"],
                        appointmentID=appointmentID,
                    )
                    prescriptions.append(prescription)
            session.add_all(prescriptions)
            session.commit()
            if valid_rows != len(prescriptions):
                raise ImportError("Could not insert all prescriptions table rows")
        except Exception:
            session.rollback()
            traceback.print_exc()
            sys.exit(f"An unexpected error occurred")


def insert_payments(filepath: str) -> None:
    with Session(engine) as session:
        session.begin()
        try:
            payments = []
            valid_rows = 0
            with open(filepath, encoding="utf-8-sig") as file:
                reader = DictReader(file)
                for row in reader:
                    # skip empty rows
                    if all(not record for record in row.values()):
                        continue
                    valid_rows += 1
                    # handle missing fk
                    patientID = None if row["patientID"] == "" else row["patientID"]
                    payment = Payment(
                        paymentID=row["paymentID"],
                        paymentDate=datetime.fromisoformat(row["paymentDate"]),
                        category=row["category"],
                        amount=row["amount"],
                        patientID=patientID,
                    )
                    payments.append(payment)
            session.add_all(payments)
            session.commit()
            if valid_rows != len(payments):
                raise ImportError("Could not insert all payments table rows")
        except Exception:
            session.rollback()
            traceback.print_exc()
            sys.exit(f"An unexpected error occurred")


if __name__ == "__main__":
    main()
