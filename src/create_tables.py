from sqlalchemy import (
    text,
    create_engine,
    event,
    Column,
    Integer,
    String,
    Float,
    CheckConstraint,
    Date,
    ForeignKey,
    DateTime,
)
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

# parent class that catalogs all models
Base = declarative_base()


# class definitions
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


class Doctor(Base):
    __tablename__ = "doctors"
    doctorID = Column(Integer, primary_key=True)
    doctorName = Column(String, nullable=False)
    speciality = Column(String, nullable=False)
    rank = Column(String)
    salary = Column(Float, CheckConstraint("salary > 0"), nullable=False)
    joinDate = Column(Date)
    dept = relationship("Department", back_populates="doctor")
    appointments = relationship("Appointment", back_populates="doctor")


class Department(Base):
    __tablename__ = "departments"
    deptID = Column(Integer, primary_key=True)
    deptName = Column(String, nullable=False)
    budget = Column(Float, CheckConstraint("budget > 0"))
    deptHead = Column(
        Integer, ForeignKey("doctors.doctorID", ondelete="SET NULL", onupdate="CASCADE")
    )
    doctor = relationship("Doctor", back_populates="dept")


class Appointment(Base):
    __tablename__ = "appointments"
    appointmentID = Column(Integer, primary_key=True)
    appointmentDate = Column(DateTime, default=datetime.now)
    roomNo = Column(String, nullable=False)
    diagnosis = Column(String, nullable=False)
    patientID = Column(
        Integer,
        ForeignKey("patients.patientID", ondelete="RESTRICT", onupdate="CASCADE"),
    )
    patient = relationship("Patient", back_populates="appointments")
    doctorID = Column(
        Integer, ForeignKey("doctors.doctorID", ondelete="RESTRICT", onupdate="CASCADE")
    )
    doctor = relationship("Doctor", back_populates="appointments")
    prescription = relationship("Prescription", back_populates="appointment")


class Prescription(Base):
    __tablename__ = "prescriptions"
    prescriptionID = Column(Integer, primary_key=True)
    description = Column(String, nullable=False)
    appointmentID = Column(
        Integer,
        ForeignKey(
            "appointments.appointmentID", ondelete="RESTRICT", onupdate="CASCADE"
        ),
    )
    appointment = relationship("Appointment", back_populates="prescription")


class Payment(Base):
    __tablename__ = "payments"
    paymentID = Column(Integer, primary_key=True)
    paymentDate = Column(DateTime, nullable=False)
    category = Column(String, nullable=False)
    amount = Column(Float, CheckConstraint("amount > 0"), nullable=False)
    patientID = Column(
        Integer,
        ForeignKey("patients.patientID", ondelete="RESTRICT", onupdate="CASCADE"),
    )
    patient = relationship("Patient", back_populates="payments")


def main():
    # object that connects to db (in the parent folder)
    engine = create_engine("sqlite:///../hospital.db")

    # enforce referential integrity on each new connection
    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # create all defined tables
    Base.metadata.create_all(engine)


if __name__ == "__main__":
    main()
