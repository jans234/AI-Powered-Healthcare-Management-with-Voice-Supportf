import mysql.connector
from mysql.connector import Error, pooling
from datetime import datetime, timedelta, date, time as datetime_time
from typing import List, Dict, Optional
import json
from contextlib import contextmanager

# Database Configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'healthcare_appointment_system',
    'pool_name': 'healthcare_pool',
    'pool_size': 5
}

try:
    connection_pool = pooling.MySQLConnectionPool(**DB_CONFIG)
    print("✅ Database connection pool created successfully")
except Error as e:
    print(f"❌ Error creating connection pool: {e}")
    connection_pool = None


@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    connection = None
    try:
        connection = connection_pool.get_connection()
        yield connection
    except Error as e:
        print(f"Database error: {e}")
        if connection:
            connection.rollback()
        raise
    finally:
        if connection and connection.is_connected():
            connection.close()


# Helper Class
class DatabaseHelper:
    """Helper class for database operations"""
    
    @staticmethod
    def execute_query(query: str, params: tuple = None, fetch: bool = True):
        """Execute a query and return results"""
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params or ())
            
            if fetch:
                result = cursor.fetchall()
                cursor.close()
                return result
            else:
                conn.commit()
                last_id = cursor.lastrowid
                cursor.close()
                return last_id


# PatientDB
class PatientDB:
    """Patient database operations"""

    @staticmethod
    def get_patient_by_phone(phone: str) -> Optional[Dict]:
        query = "SELECT * FROM patients WHERE phone = %s"
        result = DatabaseHelper.execute_query(query, (phone,))
        return result[0] if result else None

    @staticmethod
    def get_patient_by_email(email: str) -> Optional[Dict]:
        query = "SELECT * FROM patients WHERE email = %s"
        result = DatabaseHelper.execute_query(query, (email,))
        return result[0] if result else None

    @staticmethod
    def create_patient(first_name, last_name, email, phone, date_of_birth, gender, blood_group=None, address=None):
        query = """
        INSERT INTO patients (first_name, last_name, email, phone, date_of_birth, gender, blood_group, address)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (first_name, last_name, email, phone, date_of_birth, gender, blood_group, address)
        return DatabaseHelper.execute_query(query, params, fetch=False)


# DoctorDB
class DoctorDB:
    """Doctor database operations"""

    @staticmethod
    def get_all_doctors() -> List[Dict]:
        query = """
        SELECT doctor_id, CONCAT(first_name, ' ', last_name) AS name,
               specialization, email, phone, years_of_experience,
               consultation_fee, rating
        FROM doctors
        WHERE is_available = TRUE
        ORDER BY specialization, rating DESC
        """
        return DatabaseHelper.execute_query(query)

    @staticmethod
    def get_doctors_by_specialization(specialization: str) -> List[Dict]:
        """Get doctors filtered by specialization"""
        query = """
        SELECT doctor_id, CONCAT(first_name, ' ', last_name) AS name,
               specialization, email, phone, years_of_experience,
               consultation_fee, rating
        FROM doctors
        WHERE is_available = TRUE AND LOWER(specialization) LIKE LOWER(%s)
        ORDER BY rating DESC
        """
        return DatabaseHelper.execute_query(query, (f'%{specialization}%',))

    @staticmethod
    def get_doctor_by_id(doctor_id: int) -> Optional[Dict]:
        query = """
        SELECT doctor_id, CONCAT(first_name, ' ', last_name) AS name,
               specialization, email, phone, years_of_experience,
               consultation_fee, rating
        FROM doctors
        WHERE doctor_id = %s
        """
        results = DatabaseHelper.execute_query(query, (doctor_id,))
        return results[0] if results else None

    @staticmethod
    def get_doctor_schedule(doctor_id: int) -> List[Dict]:
        query = """
        SELECT day_of_week, start_time, end_time, slot_duration
        FROM doctor_schedules
        WHERE doctor_id = %s AND is_active = TRUE
        ORDER BY FIELD(day_of_week, 'Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday')
        """
        return DatabaseHelper.execute_query(query, (doctor_id,))
    
    @staticmethod
    def get_available_slots(doctor_id: int, appointment_date: date) -> Dict:
        """Get available time slots for a doctor on a specific date"""
        from datetime import datetime, timedelta, time as dt_time

        day_name = appointment_date.strftime('%A')

        # Get doctor's schedule for that day
        schedule_query = """
        SELECT start_time, end_time, slot_duration, day_of_week
        FROM doctor_schedules
        WHERE doctor_id = %s AND is_active = TRUE
        """
        all_schedules = DatabaseHelper.execute_query(schedule_query, (doctor_id,))

        # Filter for the requested day
        day_schedule = [s for s in all_schedules if s["day_of_week"] == day_name]

        if not day_schedule:
            available_days = [s["day_of_week"] for s in all_schedules]
            return {
                "available_slots": [],
                "message": f"Doctor is not available on {day_name}. Works on: {', '.join(available_days)}."
            }

        s = day_schedule[0]
        start_time = s["start_time"]
        end_time = s["end_time"]
        slot_duration = s["slot_duration"]

        # Handle MySQL returning timedelta instead of time
        if isinstance(start_time, timedelta):
            start_time = (datetime.min + start_time).time()
        if isinstance(end_time, timedelta):
            end_time = (datetime.min + end_time).time()

        # Fetch already booked slots
        booked_query = """
        SELECT appointment_time
        FROM appointments
        WHERE doctor_id = %s AND appointment_date = %s 
        AND status IN ('Scheduled', 'Confirmed')
        """
        booked_slots = DatabaseHelper.execute_query(booked_query, (doctor_id, appointment_date))
        booked_times = {slot['appointment_time'] for slot in booked_slots}

        # Generate available time slots
        available_slots = []
        current_time = datetime.combine(appointment_date, start_time)
        end_datetime = datetime.combine(appointment_date, end_time)

        while current_time < end_datetime:
            slot_time = current_time.time()
            if slot_time not in booked_times:
                available_slots.append(slot_time.strftime('%H:%M'))
            current_time += timedelta(minutes=slot_duration)

        if not available_slots:
            return {"available_slots": [], "message": f"No slots left on {appointment_date}. Try another day."}

        return {"available_slots": available_slots, "message": f"Available slots on {appointment_date}"}


# AppointmentDB
class AppointmentDB:
    """Appointment database operations"""

    @staticmethod
    def create_appointment(patient_id: int, doctor_id: int, appointment_date: date, appointment_time: datetime_time,
                           reason_for_visit: str, symptoms: str = None) -> int:
        query = """
        INSERT INTO appointments (patient_id, doctor_id, appointment_date, appointment_time, reason_for_visit, symptoms, status)
        VALUES (%s, %s, %s, %s, %s, %s, 'Scheduled')
        """
        params = (patient_id, doctor_id, appointment_date, appointment_time, reason_for_visit, symptoms)
        return DatabaseHelper.execute_query(query, params, fetch=False)

    @staticmethod
    def get_appointment_by_id(appointment_id: int) -> Optional[Dict]:
        query = """
        SELECT a.*, CONCAT(p.first_name,' ',p.last_name) AS patient_name,
               CONCAT(d.first_name,' ',d.last_name) AS doctor_name,
               d.specialization, d.consultation_fee
        FROM appointments a
        JOIN patients p ON a.patient_id=p.patient_id
        JOIN doctors d ON a.doctor_id=d.doctor_id
        WHERE a.appointment_id = %s
        """
        res = DatabaseHelper.execute_query(query, (appointment_id,))
        return res[0] if res else None

    @staticmethod
    def get_patient_appointments(patient_id: int, include_past: bool = False) -> List[Dict]:
        """Get appointments for a patient"""
        if include_past:
            query = """
            SELECT a.*, CONCAT(d.first_name,' ',d.last_name) AS doctor_name,
                   d.specialization, d.consultation_fee
            FROM appointments a
            JOIN doctors d ON a.doctor_id=d.doctor_id
            WHERE a.patient_id = %s
            ORDER BY a.appointment_date DESC, a.appointment_time DESC
            """
        else:
            query = """
            SELECT a.*, CONCAT(d.first_name,' ',d.last_name) AS doctor_name,
                   d.specialization, d.consultation_fee
            FROM appointments a
            JOIN doctors d ON a.doctor_id=d.doctor_id
            WHERE a.patient_id = %s AND a.appointment_date >= CURDATE()
            AND a.status IN ('Scheduled', 'Confirmed')
            ORDER BY a.appointment_date, a.appointment_time
            """
        return DatabaseHelper.execute_query(query, (patient_id,))

    @staticmethod
    def cancel_appointment(appointment_id: int, cancelled_by: str, cancellation_reason: str):
        """Cancel an appointment"""
        query = """
        UPDATE appointments
        SET status = 'Cancelled',
            cancelled_by = %s,
            cancellation_reason = %s,
            cancelled_at = NOW()
        WHERE appointment_id = %s
        """
        DatabaseHelper.execute_query(query, (cancelled_by, cancellation_reason, appointment_id), fetch=False)

    @staticmethod
    def reschedule_appointment(appointment_id: int, new_date: date, new_time: datetime_time):
        """Reschedule an appointment"""
        query = """
        UPDATE appointments
        SET appointment_date = %s,
            appointment_time = %s,
            updated_at = NOW()
        WHERE appointment_id = %s
        """
        DatabaseHelper.execute_query(query, (new_date, new_time, appointment_id), fetch=False)


# ConversationDB
class ConversationDB:
    """Conversation logging"""

    @staticmethod
    def log_conversation(patient_id, conversation_type, user_message, bot_response, intent=None, entities=None):
        query = """
        INSERT INTO conversation_logs (patient_id, conversation_type, user_message, bot_response, intent, entities)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        params = (patient_id, conversation_type, user_message, bot_response, intent, json.dumps(entities))
        return DatabaseHelper.execute_query(query, params, fetch=False)


# Utilities
def test_connection():
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
        print("✅ Database connection OK")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False