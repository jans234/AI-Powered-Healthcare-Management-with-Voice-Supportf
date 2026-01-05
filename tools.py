# tools.py

from langchain.tools import tool
from typing import Dict, List, Optional
from datetime import datetime, date, time as datetime_time, timedelta
from database import PatientDB, DoctorDB, AppointmentDB
from send_email import email_service
import json


@tool
def get_available_doctors(specialization: Optional[str] = None) -> str:
    """
    Get list of available doctors, optionally filtered by specialization.
    
    Args:
        specialization: Doctor's specialization (e.g., 'Cardiologist', 'Pediatrician').
                       If None, returns all doctors.
    
    Returns:
        JSON string with list of doctors
    """
    try:
        if specialization:
            doctors = DoctorDB.get_doctors_by_specialization(specialization)
        else:
            doctors = DoctorDB.get_all_doctors()
        
        if not doctors:
            return json.dumps({
                "success": False,
                "message": f"No doctors found{' for ' + specialization if specialization else ''}",
                "doctors": []
            })
        
        # Format doctor information
        formatted_doctors = []
        for doc in doctors:
            formatted_doctors.append({
                "doctor_id": doc['doctor_id'],
                "name": doc['name'],
                "specialization": doc['specialization'],
                "experience_years": doc['years_of_experience'],
                "consultation_fee": float(doc['consultation_fee']),
                "rating": float(doc['rating']),
                "phone": doc['phone']
            })
        
        return json.dumps({
            "success": True,
            "message": f"Found {len(doctors)} doctor(s)",
            "doctors": formatted_doctors
        })
    
    except Exception as e:
        return json.dumps({
            "success": False,
            "message": f"Error fetching doctors: {str(e)}",
            "doctors": []
        })


@tool
def get_doctor_details(doctor_id: int) -> str:
    """
    Get detailed information about a specific doctor including their schedule.
    
    Args:
        doctor_id: The ID of the doctor
    
    Returns:
        JSON string with doctor details and schedule
    """
    try:
        doctor = DoctorDB.get_doctor_by_id(doctor_id)
        
        if not doctor:
            return json.dumps({
                "success": False,
                "message": f"Doctor with ID {doctor_id} not found"
            })
        
        schedule = DoctorDB.get_doctor_schedule(doctor_id)
        
        formatted_schedule = []
        for slot in schedule:
            formatted_schedule.append({
                "day": slot['day_of_week'],
                "start_time": str(slot['start_time']),
                "end_time": str(slot['end_time']),
                "slot_duration_minutes": slot['slot_duration']
            })
        
        return json.dumps({
            "success": True,
            "doctor": {
                "doctor_id": doctor['doctor_id'],
                "name": doctor['name'],
                "specialization": doctor['specialization'],
                "experience_years": doctor['years_of_experience'],
                "consultation_fee": float(doctor['consultation_fee']),
                "rating": float(doctor['rating']),
                "email": doctor['email'],
                "phone": doctor['phone']
            },
            "schedule": formatted_schedule
        })
    
    except Exception as e:
        return json.dumps({
            "success": False,
            "message": f"Error fetching doctor details: {str(e)}"
        })


@tool
def get_available_slots(doctor_id: int, appointment_date: str) -> str:
    """
    Get available time slots for a doctor on a specific date.
    
    Args:
        doctor_id: The ID of the doctor
        appointment_date: Date in YYYY-MM-DD format (e.g., '2025-11-15')
    
    Returns:
        JSON string with available time slots
    """
    try:
        # Parse date
        appt_date = datetime.strptime(appointment_date, '%Y-%m-%d').date()
        
        # Check if date is in the future
        if appt_date < date.today():
            return json.dumps({
                "success": False,
                "message": "Cannot book appointments in the past"
            })
        
        # Check if date is too far in future (e.g., 90 days)
        max_date = date.today() + timedelta(days=90)
        if appt_date > max_date:
            return json.dumps({
                "success": False,
                "message": "Cannot book appointments more than 90 days in advance"
            })
        
        slots_result = DoctorDB.get_available_slots(doctor_id, appt_date)
        
        # Handle dictionary return from get_available_slots
        if isinstance(slots_result, dict):
            slots = slots_result.get("available_slots", [])
            message = slots_result.get("message", "")
        else:
            slots = []
            message = "Error retrieving slots"
        
        if not slots:
            return json.dumps({
                "success": False,
                "message": message or f"No available slots for {appointment_date}. Doctor may not be available on this day."
            })
        
        return json.dumps({
            "success": True,
            "message": f"Found {len(slots)} available slot(s)",
            "date": appointment_date,
            "available_slots": slots
        })
    
    except ValueError:
        return json.dumps({
            "success": False,
            "message": "Invalid date format. Please use YYYY-MM-DD (e.g., 2025-11-15)"
        })
    except Exception as e:
        return json.dumps({
            "success": False,
            "message": f"Error fetching available slots: {str(e)}"
        })


@tool
def book_appointment(patient_phone: str, doctor_id: int, appointment_date: str,
                    appointment_time: str, reason_for_visit: str,
                    symptoms: Optional[str] = None) -> str:
    """
    Book a new appointment for a patient. Sends email notifications to both doctor and patient.
    
    Args:
        patient_phone: Patient's phone number (format: +92-XXX-XXXXXXX)
        doctor_id: The ID of the doctor
        appointment_date: Date in YYYY-MM-DD format
        appointment_time: Time in HH:MM format (24-hour, e.g., '14:30')
        reason_for_visit: Reason for the appointment
        symptoms: Optional symptoms description
    
    Returns:
        JSON string with booking confirmation
    """
    try:
        # Get patient by phone
        patient = PatientDB.get_patient_by_phone(patient_phone)
        
        if not patient:
            return json.dumps({
                "success": False,
                "message": f"No patient found with phone number {patient_phone}. Please register first."
            })
        
        # Get doctor details
        doctor = DoctorDB.get_doctor_by_id(doctor_id)
        if not doctor:
            return json.dumps({
                "success": False,
                "message": f"Doctor with ID {doctor_id} not found"
            })
        
        # Parse date and time
        appt_date = datetime.strptime(appointment_date, '%Y-%m-%d').date()
        appt_time = datetime.strptime(appointment_time, '%H:%M').time()
        
        # Validate date
        if appt_date < date.today():
            return json.dumps({
                "success": False,
                "message": "Cannot book appointments in the past"
            })
        
        # Check if slot is available
        available_slots_result = DoctorDB.get_available_slots(doctor_id, appt_date)
        
        # Handle dictionary return
        if isinstance(available_slots_result, dict):
            available_slots = available_slots_result.get("available_slots", [])
        else:
            available_slots = []
        
        time_str = appt_time.strftime('%H:%M')
        
        if time_str not in available_slots:
            return json.dumps({
                "success": False,
                "message": f"The time slot {appointment_time} is not available. Please choose from available slots.",
                "available_slots": available_slots
            })
        
        # Create appointment
        appointment_id = AppointmentDB.create_appointment(
            patient_id=patient['patient_id'],
            doctor_id=doctor_id,
            appointment_date=appt_date,
            appointment_time=appt_time,
            reason_for_visit=reason_for_visit,
            symptoms=symptoms
        )
        
        # Send email to doctor
        email_service.send_appointment_request_to_doctor(
            doctor_email=doctor['email'],
            doctor_name=doctor['name'],
            patient_name=f"{patient['first_name']} {patient['last_name']}",
            patient_email=patient['email'],
            patient_phone=patient['phone'],
            appointment_date=appt_date,
            appointment_time=appt_time,
            reason=reason_for_visit,
            symptoms=symptoms
        )
        
        # Send confirmation email to patient
        email_service.send_appointment_confirmation_to_patient(
            patient_email=patient['email'],
            patient_name=f"{patient['first_name']} {patient['last_name']}",
            doctor_name=doctor['name'],
            doctor_specialization=doctor['specialization'],
            appointment_date=appt_date,
            appointment_time=appt_time,
            appointment_id=appointment_id,
            consultation_fee=float(doctor['consultation_fee'])
        )
        
        return json.dumps({
            "success": True,
            "message": "Appointment booked successfully! Confirmation emails sent to both doctor and patient.",
            "appointment_id": appointment_id,
            "appointment_details": {
                "patient_name": f"{patient['first_name']} {patient['last_name']}",
                "doctor_name": doctor['name'],
                "specialization": doctor['specialization'],
                "date": appointment_date,
                "time": appointment_time,
                "consultation_fee": float(doctor['consultation_fee']),
                "reason": reason_for_visit
            }
        })
    
    except ValueError as e:
        return json.dumps({
            "success": False,
            "message": f"Invalid date/time format: {str(e)}"
        })
    except Exception as e:
        return json.dumps({
            "success": False,
            "message": f"Error booking appointment: {str(e)}"
        })


@tool
def get_patient_appointments(patient_phone: str, include_past: bool = False) -> str:
    """
    Get all appointments for a patient.
    
    Args:
        patient_phone: Patient's phone number
        include_past: Whether to include past appointments (default: False)
    
    Returns:
        JSON string with list of appointments
    """
    try:
        patient = PatientDB.get_patient_by_phone(patient_phone)
        
        if not patient:
            return json.dumps({
                "success": False,
                "message": f"No patient found with phone number {patient_phone}"
            })
        
        appointments = AppointmentDB.get_patient_appointments(
            patient['patient_id'],
            include_past=include_past
        )
        
        if not appointments:
            return json.dumps({
                "success": True,
                "message": "No appointments found",
                "appointments": []
            })
        
        formatted_appointments = []
        for apt in appointments:
            formatted_appointments.append({
                "appointment_id": apt['appointment_id'],
                "doctor_name": apt['doctor_name'],
                "specialization": apt['specialization'],
                "date": str(apt['appointment_date']),
                "time": str(apt['appointment_time']),
                "status": apt['status'],
                "reason": apt['reason_for_visit'],
                "consultation_fee": float(apt['consultation_fee'])
            })
        
        return json.dumps({
            "success": True,
            "message": f"Found {len(appointments)} appointment(s)",
            "appointments": formatted_appointments
        })
    
    except Exception as e:
        return json.dumps({
            "success": False,
            "message": f"Error fetching appointments: {str(e)}"
        })


@tool
def cancel_appointment(appointment_id: int, patient_phone: str,
                      cancellation_reason: str) -> str:
    """
    Cancel an existing appointment. Sends email notifications to both doctor and patient.
    
    Args:
        appointment_id: The ID of the appointment to cancel
        patient_phone: Patient's phone number for verification
        cancellation_reason: Reason for cancellation
    
    Returns:
        JSON string with cancellation confirmation
    """
    try:
        # Get patient
        patient = PatientDB.get_patient_by_phone(patient_phone)
        if not patient:
            return json.dumps({
                "success": False,
                "message": f"No patient found with phone number {patient_phone}"
            })
        
        # Get appointment details
        appointment = AppointmentDB.get_appointment_by_id(appointment_id)
        
        if not appointment:
            return json.dumps({
                "success": False,
                "message": f"Appointment with ID {appointment_id} not found"
            })
        
        # Verify patient owns this appointment
        if appointment['patient_id'] != patient['patient_id']:
            return json.dumps({
                "success": False,
                "message": "You can only cancel your own appointments"
            })
        
        # Check if appointment can be cancelled
        if appointment['status'] not in ['Scheduled', 'Confirmed']:
            return json.dumps({
                "success": False,
                "message": f"Cannot cancel appointment with status: {appointment['status']}"
            })
        
        # Cancel the appointment
        AppointmentDB.cancel_appointment(
            appointment_id=appointment_id,
            cancelled_by='Patient',
            cancellation_reason=cancellation_reason
        )
        
        # Get doctor details
        doctor = DoctorDB.get_doctor_by_id(appointment['doctor_id'])
        
        # Send email to doctor
        email_service.send_cancellation_to_doctor(
            doctor_email=doctor['email'],
            doctor_name=doctor['name'],
            patient_name=appointment['patient_name'],
            appointment_date=appointment['appointment_date'],
            appointment_time=appointment['appointment_time'],
            cancellation_reason=cancellation_reason
        )
        
        # Send confirmation to patient
        email_service.send_cancellation_to_patient(
            patient_email=patient['email'],
            patient_name=f"{patient['first_name']} {patient['last_name']}",
            doctor_name=appointment['doctor_name'],
            appointment_date=appointment['appointment_date'],
            appointment_time=appointment['appointment_time']
        )
        
        return json.dumps({
            "success": True,
            "message": "Appointment cancelled successfully! Cancellation emails sent to both doctor and patient.",
            "cancelled_appointment": {
                "appointment_id": appointment_id,
                "doctor_name": appointment['doctor_name'],
                "date": str(appointment['appointment_date']),
                "time": str(appointment['appointment_time'])
            }
        })
    
    except Exception as e:
        return json.dumps({
            "success": False,
            "message": f"Error cancelling appointment: {str(e)}"
        })


@tool
def reschedule_appointment(appointment_id: int, patient_phone: str,
                          new_date: str, new_time: str) -> str:
    """
    Reschedule an existing appointment.
    
    Args:
        appointment_id: The ID of the appointment to reschedule
        patient_phone: Patient's phone number for verification
        new_date: New date in YYYY-MM-DD format
        new_time: New time in HH:MM format (24-hour)
    
    Returns:
        JSON string with reschedule confirmation
    """
    try:
        # Get patient
        patient = PatientDB.get_patient_by_phone(patient_phone)
        if not patient:
            return json.dumps({
                "success": False,
                "message": f"No patient found with phone number {patient_phone}"
            })
        
        # Get appointment
        appointment = AppointmentDB.get_appointment_by_id(appointment_id)
        if not appointment:
            return json.dumps({
                "success": False,
                "message": f"Appointment with ID {appointment_id} not found"
            })
        
        # Verify ownership
        if appointment['patient_id'] != patient['patient_id']:
            return json.dumps({
                "success": False,
                "message": "You can only reschedule your own appointments"
            })
        
        # Parse new date and time
        appt_date = datetime.strptime(new_date, '%Y-%m-%d').date()
        appt_time = datetime.strptime(new_time, '%H:%M').time()
        
        # Check if new slot is available
        available_slots_result = DoctorDB.get_available_slots(appointment['doctor_id'], appt_date)
        
        # Handle dictionary return
        if isinstance(available_slots_result, dict):
            available_slots = available_slots_result.get("available_slots", [])
        else:
            available_slots = []
        
        time_str = appt_time.strftime('%H:%M')
        
        if time_str not in available_slots:
            return json.dumps({
                "success": False,
                "message": f"The time slot {new_time} is not available",
                "available_slots": available_slots
            })
        
        # Reschedule
        AppointmentDB.reschedule_appointment(appointment_id, appt_date, appt_time)
        
        return json.dumps({
            "success": True,
            "message": "Appointment rescheduled successfully!",
            "updated_appointment": {
                "appointment_id": appointment_id,
                "doctor_name": appointment['doctor_name'],
                "old_date": str(appointment['appointment_date']),
                "old_time": str(appointment['appointment_time']),
                "new_date": new_date,
                "new_time": new_time
            }
        })
    
    except Exception as e:
        return json.dumps({
            "success": False,
            "message": f"Error rescheduling appointment: {str(e)}"
        })


@tool
def register_new_patient(first_name: str, last_name: str, email: str,
                        phone: str, date_of_birth: str, gender: str,
                        blood_group: Optional[str] = None,
                        address: Optional[str] = None) -> str:
    """
    Register a new patient in the system.
    
    Args:
        first_name: Patient's first name
        last_name: Patient's last name
        email: Patient's email address
        phone: Patient's phone number (format: +92-XXX-XXXXXXX)
        date_of_birth: Date of birth in YYYY-MM-DD format
        gender: Gender (Male/Female/Other)
        blood_group: Optional blood group (e.g., 'A+', 'O-')
        address: Optional address
    
    Returns:
        JSON string with registration confirmation
    """
    try:
        # Check if patient already exists
        existing = PatientDB.get_patient_by_phone(phone)
        if existing:
            return json.dumps({
                "success": False,
                "message": f"Patient with phone number {phone} already exists"
            })
        
        existing_email = PatientDB.get_patient_by_email(email)
        if existing_email:
            return json.dumps({
                "success": False,
                "message": f"Patient with email {email} already exists"
            })
        
        # Create patient
        patient_id = PatientDB.create_patient(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            date_of_birth=date_of_birth,
            gender=gender,
            blood_group=blood_group,
            address=address
        )
        
        return json.dumps({
            "success": True,
            "message": "Patient registered successfully!",
            "patient_id": patient_id,
            "patient_info": {
                "name": f"{first_name} {last_name}",
                "email": email,
                "phone": phone
            }
        })
    
    except Exception as e:
        return json.dumps({
            "success": False,
            "message": f"Error registering patient: {str(e)}"
        })


# List of all tools
healthcare_tools = [
    get_available_doctors,
    get_doctor_details,
    get_available_slots,
    book_appointment,
    get_patient_appointments,
    cancel_appointment,
    reschedule_appointment,
    register_new_patient
]