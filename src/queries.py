from sqlalchemy import create_engine, event, delete, func, text
from create_tables import Patient, Doctor, Appointment, Payment
from sqlalchemy.orm import Session, joinedload, selectinload
from csv import DictWriter
import traceback

# object that connects to db (in parent folder)
engine = create_engine("sqlite:///../hospital.db")


# enforce referential integrity on each new connection
@event.listens_for(engine, "connect")
def enable_foreign_keys(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def main():

    qry_patients("../queries/q1.csv")
    qry_dr_workload("../queries/q2.csv")
    qry_payment("../queries/q3.csv")
    qry_ranking("../queries/q4.csv")
    row_count = update_dr_salary("Senior", 5)
    print(f"{row_count} rows were affected during salary update")
    removed = del_payment_rec(10)
    if removed:
        print("Payment 10 was successfully deleted")
    else:
        print("Payment 10 could not be deleted")


def update_dr_salary(rank: str, percent: float) -> int:
    """Updates doctor salary by percentage based on the given rank"""

    with Session(engine) as session:
        session.begin()
        rows_affected = 0
        try:
            doctors = session.query(Doctor).filter(Doctor.rank == rank).all()
            for d in doctors:
                d.salary *= 1 + (percent / 100)
                rows_affected += 1
            session.commit()
            return rows_affected
        except Exception:
            session.rollback()
            traceback.print_exc
            return 0


def del_payment_rec(ID: int) -> bool:
    """Removes payment identified by ID from payments table"""

    with Session(engine) as session:
        session.begin()
        try:
            session.query(Payment).filter(Payment.paymentID == ID).delete()
            session.commit()
            # verify payment rec not longer exists
            exist = session.query(Payment).filter(Payment.paymentID == ID).first()
            return True if exist is None else False
        except Exception:
            session.rollback()
            traceback.print_exc
            return False


def qry_ranking(filepath: str) -> None:
    """
    Retrieves all doctors, their appointment count, and a ranking
    based on the appointment count (highest first). Writes results to csv
    """
    with Session(engine) as session:
        session.begin()
        header = ["Doctor Name", "Speciality", "Appointment Count", "Rank"]
        qry_data = []
        try:
            result = session.execute(text("""
                    WITH doctor_ap AS (
                        SELECT d.doctorName, d.speciality, COUNT(ap.doctorID) as total_appointments
                        FROM doctors d LEFT JOIN appointments ap 
                        ON ap.doctorID = d.doctorID
                        GROUP BY d.doctorID, d.doctorName
                    )
                    SELECT doctorName, speciality, total_appointments, 
                    DENSE_RANK() OVER(ORDER BY total_appointments DESC) as ranking
                    FROM doctor_ap"""))
            for row in result:
                qry_data.append(
                    {
                        "Doctor Name": row[0],
                        "Speciality": row[1],
                        "Appointment Count": row[2],
                        "Rank": row[3],
                    }
                )
            # write to file
            write_to_file(filepath, header, qry_data)
            session.commit()
        except Exception:
            session.rollback()
            traceback.print_exc


def write_to_file(file: str, header: list[str], data: list[dict]) -> None:
    """Writes data to csv file"""
    with open(file, "w", newline="", encoding="utf-8-sig") as f:
        writer = DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(data)


def qry_payment(filepath: str) -> None:
    """
    Retrieves a report of payments made patients, including their
    insurance provider, total number and paid amount. Writes results to csv
    """
    with Session(engine) as session:
        session.begin()
        header = [
            "Patient ID",
            "Patient Name",
            "Insurance Provider",
            "Total Payments",
            "Total Paid Amount",
        ]
        qry_data = []
        try:
            result = session.execute(text("""
                        SELECT p.patientID, p.patientName, i.provider, COUNT(py.patientID) as total_payments,
                        SUM(py.amount) as total_amount FROM patients p LEFT JOIN payments py 
                        ON py.patientID = p.patientID JOIN insurances i ON p.insuranceID = i.insuranceID
                        GROUP BY p.patientID, p.patientName, i.provider
                        ORDER BY total_amount
                    """))
            for row in result:
                qry_data.append(
                    {
                        "Patient ID": row[0],
                        "Patient Name": row[1],
                        "Insurance Provider": row[2],
                        "Total Payments": row[3],
                        "Total Paid Amount": row[4],
                    }
                )
            # write to file
            write_to_file(filepath, header, qry_data)
            session.commit()
        except Exception:
            session.rollback()
            traceback.print_exc


def qry_dr_workload(filepath: str) -> None:
    """
    Retrieves list of doctors and their total appointments.
    It includes doctors with no appointments, sorted from the highest appointment count to the lowest.
    Results are written to a csv
    """
    with Session(engine) as session:
        session.begin()
        header = ["Doctor Name", "Total Appointments"]
        qry_data = []
        try:
            results = (
                session.query(
                    Doctor.doctorName, func.count(Appointment.doctorID).label("count")
                )
                .outerjoin(Appointment, Doctor.doctorID == Appointment.doctorID)
                .group_by(Doctor.doctorID, Doctor.doctorName)
                .order_by(func.count(Appointment.doctorID).desc())
                .all()
            )
            for row in results:
                # build list of dict
                qry_data.append(
                    {
                        "Doctor Name": row.doctorName,
                        "Total Appointments": row.count,
                    }
                )
            # write to file
            write_to_file(filepath, header, qry_data)
            session.commit()
        except Exception:
            session.rollback()
            traceback.print_exc


def qry_patients(filepath: str) -> None:
    """
    Retrieves patient name, phone number, and insurance provider for all patients.
    Sort alphabetically by patient name. Include patients who do not have an insurance provider recorded.
    Write results to a csv.
    """
    with Session(engine) as session:
        session.begin()
        header = ["Patient Name", "Phone Number", "Insurance Provider"]
        qry_data = []
        try:
            patients = (
                session.query(Patient)
                .options(joinedload(Patient.insurance))
                .order_by((Patient.patientName))
                .all()
            )
            for p in patients:
                insurance_provider = (
                    p.insurance.provider if p.insurance else "No Insurance"
                )
                # build list of dict
                qry_data.append(
                    {
                        "Patient Name": p.patientName,
                        "Phone Number": p.phone,
                        "Insurance Provider": insurance_provider,
                    }
                )
            # write results to file
            write_to_file(filepath, header, qry_data)
            session.commit()
        except Exception:
            session.rollback()
            traceback.print_exc


if __name__ == "__main__":
    main()
