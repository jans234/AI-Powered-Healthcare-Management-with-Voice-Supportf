# email_service.py
"""
Email service for sending notifications to patients and doctors
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, List
import os
from dotenv import load_dotenv
from datetime import datetime, date, time as datetime_time

load_dotenv()


class EmailService:
    """Handle email notifications for appointments"""
    
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.smtp_email = os.getenv('SMTP_EMAIL')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.enabled = os.getenv('SEND_EMAIL_NOTIFICATIONS', 'True').lower() == 'true'
    
    def send_email(self, to_email: str, subject: str, html_body: str, 
                   plain_body: str = None) -> bool:
        """Send an email"""
        if not self.enabled:
            print(f"[EMAIL DISABLED] Would send to {to_email}: {subject}")
            return True
        
        if not all([self.smtp_email, self.smtp_password]):
            print("[EMAIL ERROR] SMTP credentials not configured")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.smtp_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add plain text and HTML parts
            if plain_body:
                part1 = MIMEText(plain_body, 'plain')
                msg.attach(part1)
            
            part2 = MIMEText(html_body, 'html')
            msg.attach(part2)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_email, self.smtp_password)
                server.send_message(msg)
            
            print(f"✅ Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email to {to_email}: {e}")
            return False
    
    def send_appointment_request_to_doctor(self, doctor_email: str, doctor_name: str,
                                          patient_name: str, patient_email: str,
                                          patient_phone: str, appointment_date: date,
                                          appointment_time: datetime_time, 
                                          reason: str, symptoms: str = None) -> bool:
        """Notify doctor about new appointment request"""
        
        subject = f"New Appointment Request - {patient_name}"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                          color: white; padding: 20px; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 20px; border: 1px solid #ddd; }}
                .info-box {{ background: white; padding: 15px; margin: 10px 0; 
                            border-left: 4px solid #667eea; border-radius: 5px; }}
                .label {{ font-weight: bold; color: #667eea; }}
                .footer {{ background: #333; color: white; padding: 15px; 
                          text-align: center; border-radius: 0 0 10px 10px; }}
                .button {{ background: #667eea; color: white; padding: 12px 30px; 
                          text-decoration: none; border-radius: 5px; display: inline-block;
                          margin-top: 15px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>🏥 New Appointment Request</h2>
                </div>
                
                <div class="content">
                    <p>Dear Dr. {doctor_name},</p>
                    <p>You have received a new appointment request from a patient.</p>
                    
                    <div class="info-box">
                        <h3>📋 Appointment Details</h3>
                        <p><span class="label">Date:</span> {appointment_date.strftime('%A, %B %d, %Y')}</p>
                        <p><span class="label">Time:</span> {appointment_time.strftime('%I:%M %p')}</p>
                        <p><span class="label">Reason:</span> {reason}</p>
                        {f'<p><span class="label">Symptoms:</span> {symptoms}</p>' if symptoms else ''}
                    </div>
                    
                    <div class="info-box">
                        <h3>👤 Patient Information</h3>
                        <p><span class="label">Name:</span> {patient_name}</p>
                        <p><span class="label">Email:</span> {patient_email}</p>
                        <p><span class="label">Phone:</span> {patient_phone}</p>
                    </div>
                    
                    <p>Please confirm or reschedule this appointment at your earliest convenience.</p>
                </div>
                
                <div class="footer">
                    <p>Healthcare Appointment System</p>
                    <p style="font-size: 12px;">This is an automated notification</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        plain_body = f"""
        New Appointment Request
        
        Dear Dr. {doctor_name},
        
        You have received a new appointment request:
        
        Appointment Details:
        - Date: {appointment_date.strftime('%A, %B %d, %Y')}
        - Time: {appointment_time.strftime('%I:%M %p')}
        - Reason: {reason}
        {f'- Symptoms: {symptoms}' if symptoms else ''}
        
        Patient Information:
        - Name: {patient_name}
        - Email: {patient_email}
        - Phone: {patient_phone}
        
        Healthcare Appointment System
        """
        
        return self.send_email(doctor_email, subject, html_body, plain_body)
    
    def send_appointment_confirmation_to_patient(self, patient_email: str, 
                                                patient_name: str, doctor_name: str,
                                                doctor_specialization: str,
                                                appointment_date: date,
                                                appointment_time: datetime_time,
                                                appointment_id: int,
                                                consultation_fee: float) -> bool:
        """Send appointment confirmation to patient"""
        
        subject = f"Appointment Confirmed - Dr. {doctor_name}"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                          color: white; padding: 20px; border-radius: 10px 10px 0 0; text-align: center; }}
                .content {{ background: #f9f9f9; padding: 20px; border: 1px solid #ddd; }}
                .success-badge {{ background: #4CAF50; color: white; padding: 10px 20px; 
                                 border-radius: 20px; display: inline-block; margin: 15px 0; }}
                .info-box {{ background: white; padding: 15px; margin: 15px 0; 
                            border-left: 4px solid #4CAF50; border-radius: 5px; }}
                .label {{ font-weight: bold; color: #667eea; }}
                .appointment-id {{ font-size: 24px; font-weight: bold; color: #667eea; 
                                  text-align: center; margin: 15px 0; }}
                .footer {{ background: #333; color: white; padding: 15px; 
                          text-align: center; border-radius: 0 0 10px 10px; }}
                .warning {{ background: #fff3cd; border-left: 4px solid #ffc107; 
                           padding: 15px; margin: 15px 0; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>✅ Appointment Confirmed!</h2>
                    <div class="success-badge">Successfully Booked</div>
                </div>
                
                <div class="content">
                    <p>Dear {patient_name},</p>
                    <p>Your appointment has been successfully confirmed. We look forward to seeing you!</p>
                    
                    <div class="appointment-id">
                        Appointment ID: #{appointment_id}
                    </div>
                    
                    <div class="info-box">
                        <h3>📅 Appointment Details</h3>
                        <p><span class="label">Doctor:</span> Dr. {doctor_name}</p>
                        <p><span class="label">Specialization:</span> {doctor_specialization}</p>
                        <p><span class="label">Date:</span> {appointment_date.strftime('%A, %B %d, %Y')}</p>
                        <p><span class="label">Time:</span> {appointment_time.strftime('%I:%M %p')}</p>
                        <p><span class="label">Consultation Fee:</span> PKR {consultation_fee:,.2f}</p>
                    </div>
                    
                    <div class="warning">
                        <strong>⚠️ Important Reminders:</strong>
                        <ul>
                            <li>Please arrive 10 minutes before your appointment time</li>
                            <li>Bring your medical records and previous prescriptions</li>
                            <li>If you need to cancel, please do so at least 24 hours in advance</li>
                        </ul>
                    </div>
                    
                    <p style="margin-top: 20px;">If you have any questions, please contact us at your convenience.</p>
                </div>
                
                <div class="footer">
                    <p>Healthcare Appointment System</p>
                    <p style="font-size: 12px;">Save this email for your records</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        plain_body = f"""
        Appointment Confirmed!
        
        Dear {patient_name},
        
        Your appointment has been successfully confirmed.
        
        Appointment ID: #{appointment_id}
        
        Appointment Details:
        - Doctor: Dr. {doctor_name}
        - Specialization: {doctor_specialization}
        - Date: {appointment_date.strftime('%A, %B %d, %Y')}
        - Time: {appointment_time.strftime('%I:%M %p')}
        - Consultation Fee: PKR {consultation_fee:,.2f}
        
        Important Reminders:
        - Please arrive 10 minutes early
        - Bring your medical records
        - Cancel at least 24 hours in advance if needed
        
        Healthcare Appointment System
        """
        
        return self.send_email(patient_email, subject, html_body, plain_body)
    
    def send_cancellation_to_doctor(self, doctor_email: str, doctor_name: str,
                                   patient_name: str, appointment_date: date,
                                   appointment_time: datetime_time,
                                   cancellation_reason: str) -> bool:
        """Notify doctor about appointment cancellation"""
        
        subject = f"Appointment Cancelled - {patient_name}"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #dc3545; color: white; padding: 20px; 
                          border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 20px; border: 1px solid #ddd; }}
                .info-box {{ background: white; padding: 15px; margin: 10px 0; 
                            border-left: 4px solid #dc3545; border-radius: 5px; }}
                .label {{ font-weight: bold; color: #dc3545; }}
                .footer {{ background: #333; color: white; padding: 15px; 
                          text-align: center; border-radius: 0 0 10px 10px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>🚫 Appointment Cancelled</h2>
                </div>
                
                <div class="content">
                    <p>Dear Dr. {doctor_name},</p>
                    <p>An appointment has been cancelled by the patient.</p>
                    
                    <div class="info-box">
                        <h3>📋 Cancelled Appointment</h3>
                        <p><span class="label">Patient:</span> {patient_name}</p>
                        <p><span class="label">Date:</span> {appointment_date.strftime('%A, %B %d, %Y')}</p>
                        <p><span class="label">Time:</span> {appointment_time.strftime('%I:%M %p')}</p>
                        <p><span class="label">Reason:</span> {cancellation_reason}</p>
                    </div>
                    
                    <p>This time slot is now available for other appointments.</p>
                </div>
                
                <div class="footer">
                    <p>Healthcare Appointment System</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        plain_body = f"""
        Appointment Cancelled
        
        Dear Dr. {doctor_name},
        
        An appointment has been cancelled:
        
        - Patient: {patient_name}
        - Date: {appointment_date.strftime('%A, %B %d, %Y')}
        - Time: {appointment_time.strftime('%I:%M %p')}
        - Reason: {cancellation_reason}
        
        Healthcare Appointment System
        """
        
        return self.send_email(doctor_email, subject, html_body, plain_body)
    
    def send_cancellation_to_patient(self, patient_email: str, patient_name: str,
                                    doctor_name: str, appointment_date: date,
                                    appointment_time: datetime_time) -> bool:
        """Send cancellation confirmation to patient"""
        
        subject = "Appointment Cancelled - Confirmation"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #dc3545; color: white; padding: 20px; 
                          border-radius: 10px 10px 0 0; text-align: center; }}
                .content {{ background: #f9f9f9; padding: 20px; border: 1px solid #ddd; }}
                .info-box {{ background: white; padding: 15px; margin: 15px 0; 
                            border-left: 4px solid #dc3545; border-radius: 5px; }}
                .label {{ font-weight: bold; color: #dc3545; }}
                .footer {{ background: #333; color: white; padding: 15px; 
                          text-align: center; border-radius: 0 0 10px 10px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Appointment Cancelled</h2>
                </div>
                
                <div class="content">
                    <p>Dear {patient_name},</p>
                    <p>Your appointment has been successfully cancelled.</p>
                    
                    <div class="info-box">
                        <h3>📋 Cancelled Appointment Details</h3>
                        <p><span class="label">Doctor:</span> Dr. {doctor_name}</p>
                        <p><span class="label">Date:</span> {appointment_date.strftime('%A, %B %d, %Y')}</p>
                        <p><span class="label">Time:</span> {appointment_time.strftime('%I:%M %p')}</p>
                    </div>
                    
                    <p>If you'd like to reschedule, please contact us or book a new appointment.</p>
                </div>
                
                <div class="footer">
                    <p>Healthcare Appointment System</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        plain_body = f"""
        Appointment Cancelled
        
        Dear {patient_name},
        
        Your appointment has been cancelled:
        
        - Doctor: Dr. {doctor_name}
        - Date: {appointment_date.strftime('%A, %B %d, %Y')}
        - Time: {appointment_time.strftime('%I:%M %p')}
        
        Healthcare Appointment System
        """
        
        return self.send_email(patient_email, subject, html_body, plain_body)


# Initialize email service
email_service = EmailService()


