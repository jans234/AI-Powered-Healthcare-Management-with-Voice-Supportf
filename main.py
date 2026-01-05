from fastapi import FastAPI, HTTPException, Depends, status, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from datetime import date, time as datetime_time
from send_email import email_service
import uvicorn
from workflow import *
from database import *
from voice import voice_service  # Import voice service
import os
from dotenv import load_dotenv
import io
import base64

load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Healthcare Appointment API",
    description="AI-powered healthcare appointment booking system with LangGraph and Voice Support",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware - allow all origins for development
# Restrict this in production!
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production: ["https://yourdomain.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "interface")
INDEX_PATH = os.path.join(FRONTEND_DIR, "index.html")

# Serve static files (JS, CSS, images, etc.)
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


# PYDANTIC MODELS (Request/Response schemas)

class ChatRequest(BaseModel):
    """Chat request model"""
    session_id: str = Field(..., description="Unique session identifier")
    message: str = Field(..., min_length=1, description="User message")
    patient_phone: Optional[str] = Field(None, description="Patient phone number")
    
    @validator('message')
    def message_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Message cannot be empty')
        return v.strip()


class ChatResponse(BaseModel):
    """Chat response model"""
    session_id: str
    message: str
    response: str
    timestamp: str


class PatientRegisterRequest(BaseModel):
    """Patient registration request"""
    first_name: str = Field(..., min_length=2)
    last_name: str = Field(..., min_length=2)
    email: str = Field(..., pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    phone: str = Field(..., pattern=r'^\+92-\d{3}-\d{7}$')
    date_of_birth: str = Field(..., description="YYYY-MM-DD format")
    gender: str = Field(..., pattern=r'^(Male|Female|Other)$')
    blood_group: Optional[str] = None
    address: Optional[str] = None
    medical_history: Optional[str] = None


class AppointmentBookRequest(BaseModel):
    """Appointment booking request"""
    patient_phone: str = Field(..., pattern=r'^\+92-\d{3}-\d{7}$')
    doctor_id: int = Field(..., gt=0)
    appointment_date: str = Field(..., description="YYYY-MM-DD format")
    appointment_time: str = Field(..., pattern=r'^\d{2}:\d{2}$')
    reason_for_visit: str = Field(..., min_length=5)
    symptoms: Optional[str] = None


class AppointmentCancelRequest(BaseModel):
    """Appointment cancellation request"""
    appointment_id: int = Field(..., gt=0)
    patient_phone: str = Field(..., pattern=r'^\+92-\d{3}-\d{7}$')
    cancellation_reason: str = Field(..., min_length=5)


class DoctorSearchRequest(BaseModel):
    """Doctor search request"""
    specialization: Optional[str] = None


# HEALTH CHECK & STATUS
@app.get("/api", tags=["Health"])
async def root():
    """API information"""
    return {
        "service": "Healthcare Appointment API",
        "version": "2.0.0",
        "status": "operational",
        "features": ["chat", "voice", "appointments", "doctors", "patients"],
        "docs": "/docs",
        "endpoints": {
            "chat": "/api/chat",
            "voice": "/api/voice/*",
            "doctors": "/api/doctors",
            "appointments": "/api/appointments",
            "patients": "/api/patients"
        }
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    db_status = test_connection()
    
    return {
        "status": "healthy" if db_status else "degraded",
        "database": "connected" if db_status else "disconnected",
        "services": {
            "langgraph_agent": "operational",
            "email_service": "operational",
            "voice_service": "enabled" if voice_service.enabled else "disabled",
            "database": "connected" if db_status else "disconnected"
        }
    }


# CHAT ENDPOINTS

@app.post("/api/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest):
    """
    Send a message to the AI agent and get a response.
    
    The agent can handle:
    - Booking appointments
    - Viewing appointments
    - Canceling appointments
    - Finding doctors
    - Patient registration
    - General healthcare queries
    """
    try:
        from datetime import datetime
        
        response = conversation_manager.chat(
            session_id=request.session_id,
            user_message=request.message,
            patient_phone=request.patient_phone
        )
        
        return ChatResponse(
            session_id=request.session_id,
            message=request.message,
            response=response,
            timestamp=datetime.now().isoformat()
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing chat: {str(e)}"
        )


@app.delete("/api/chat/session/{session_id}", tags=["Chat"])
async def clear_session(session_id: str):
    """Clear conversation history for a session"""
    try:
        conversation_manager.clear_conversation(session_id)
        return {"message": "Session cleared successfully", "session_id": session_id}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error clearing session: {str(e)}"
        )


# VOICE ENDPOINTS

@app.post("/api/voice/transcribe", tags=["Voice"])
async def transcribe_audio(audio: UploadFile = File(...)):
    """
    Transcribe audio to text using OpenAI Whisper.
    Accepts audio files in various formats (mp3, wav, m4a, webm, etc.)
    """
    try:
        # Read audio file
        audio_data = await audio.read()
        
        # Create a file-like object
        audio_file = io.BytesIO(audio_data)
        audio_file.name = audio.filename
        
        # Transcribe
        result = voice_service.transcribe_audio(audio_file)
        
        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result['error']
            )
        
        return {
            "success": True,
            "text": result['text'],
            "message": "Audio transcribed successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error transcribing audio: {str(e)}"
        )


@app.post("/api/voice/speak", tags=["Voice"])
async def text_to_speech(text: str, voice: Optional[str] = "nova"):
    """
    Convert text to speech using OpenAI TTS.
    
    Args:
        text: Text to convert to speech
        voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer)
    
    Returns:
        Audio file (MP3)
    """
    try:
        if not text or len(text.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text cannot be empty"
            )
        
        # Generate speech
        result = voice_service.text_to_speech(text, voice)
        
        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result['error']
            )
        
        # Return audio as streaming response
        return StreamingResponse(
            io.BytesIO(result['audio_data']),
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "attachment; filename=speech.mp3"
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating speech: {str(e)}"
        )


@app.post("/api/voice/chat", tags=["Voice"])
async def voice_chat(
    audio: UploadFile = File(...),
    session_id: str = None,
    patient_phone: Optional[str] = None
):
    """
    Complete voice chat flow: transcribe audio, process with agent, return text and audio response.
    
    Args:
        audio: Audio file with user's voice message
        session_id: Session identifier
        patient_phone: Patient's phone number (optional)
    
    Returns:
        JSON with transcribed text, bot response text, and audio data
    """
    try:
        from datetime import datetime
        
        # Generate session ID if not provided
        if not session_id:
            session_id = f"voice_{datetime.now().timestamp()}"
        
        # 1. Transcribe audio to text
        audio_data = await audio.read()
        audio_file = io.BytesIO(audio_data)
        audio_file.name = audio.filename
        
        transcribe_result = voice_service.transcribe_audio(audio_file)
        
        if not transcribe_result['success']:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Transcription failed: {transcribe_result['error']}"
            )
        
        user_text = transcribe_result['text']
        
        # 2. Process with chat agent
        response = conversation_manager.chat(
            session_id=session_id,
            user_message=user_text,
            patient_phone=patient_phone
        )
        
        # 3. Convert response to speech
        tts_result = voice_service.text_to_speech(response)
        
        if not tts_result['success']:
            # Return text response even if TTS fails
            return {
                "success": True,
                "session_id": session_id,
                "user_message": user_text,
                "bot_response": response,
                "audio_available": False,
                "timestamp": datetime.now().isoformat()
            }
        
        # 4. Return response with audio
        # Convert audio to base64 for easy transmission
        audio_base64 = base64.b64encode(tts_result['audio_data']).decode('utf-8')
        
        return {
            "success": True,
            "session_id": session_id,
            "user_message": user_text,
            "bot_response": response,
            "audio_available": True,
            "audio_base64": audio_base64,
            "timestamp": datetime.now().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing voice chat: {str(e)}"
        )


@app.get("/api/voice/status", tags=["Voice"])
async def voice_service_status():
    """Check voice service status"""
    return {
        "enabled": voice_service.enabled,
        "tts_available": True if voice_service.enabled else False,
        "stt_available": True if voice_service.enabled else False,
        "default_voice": voice_service.default_voice
    }


# DOCTOR ENDPOINTS

@app.get("/api/doctors", tags=["Doctors"])
async def get_doctors(specialization: Optional[str] = None):
    """
    Get list of available doctors.
    Optionally filter by specialization.
    """
    try:
        if specialization:
            doctors = DoctorDB.get_doctors_by_specialization(specialization)
        else:
            doctors = DoctorDB.get_all_doctors()
        
        return {
            "success": True,
            "count": len(doctors),
            "doctors": doctors
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching doctors: {str(e)}"
        )


@app.get("/api/doctors/{doctor_id}", tags=["Doctors"])
async def get_doctor(doctor_id: int):
    """Get detailed information about a specific doctor"""
    try:
        doctor = DoctorDB.get_doctor_by_id(doctor_id)
        
        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Doctor with ID {doctor_id} not found"
            )
        
        schedule = DoctorDB.get_doctor_schedule(doctor_id)
        
        return {
            "success": True,
            "doctor": doctor,
            "schedule": schedule
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching doctor: {str(e)}"
        )


@app.get("/api/doctors/{doctor_id}/slots", tags=["Doctors"])
async def get_available_slots(doctor_id: int, date: str):
    """
    Get available time slots for a doctor on a specific date.
    Date format: YYYY-MM-DD
    """
    try:
        from datetime import datetime
        
        # Parse and validate date
        try:
            appt_date = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD"
            )
        
        slots = DoctorDB.get_available_slots(doctor_id, appt_date)
        
        return {
            "success": True,
            "doctor_id": doctor_id,
            "date": date,
            "available_slots": slots.get("available_slots", []),
            "count": len(slots.get("available_slots", [])),
            "message": slots.get("message", "")
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching slots: {str(e)}"
        )


@app.get("/api/specializations", tags=["Doctors"])
async def get_specializations():
    """Get list of all available specializations"""
    try:
        query = "SELECT DISTINCT specialization FROM doctors WHERE is_available = TRUE ORDER BY specialization"
        result = DatabaseHelper.execute_query(query)
        
        specializations = [row['specialization'] for row in result]
        
        return {
            "success": True,
            "specializations": specializations,
            "count": len(specializations)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching specializations: {str(e)}"
        )


# PATIENT ENDPOINTS

@app.post("/api/patients/register", tags=["Patients"])
async def register_patient(request: PatientRegisterRequest):
    """Register a new patient"""
    try:
        # Check if patient already exists
        existing = PatientDB.get_patient_by_phone(request.phone)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Patient with this phone number already exists"
            )
        
        existing_email = PatientDB.get_patient_by_email(request.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Patient with this email already exists"
            )
        
        # Create patient
        patient_id = PatientDB.create_patient(
            first_name=request.first_name,
            last_name=request.last_name,
            email=request.email,
            phone=request.phone,
            date_of_birth=request.date_of_birth,
            gender=request.gender,
            blood_group=request.blood_group,
            address=request.address
        )
        
        return {
            "success": True,
            "message": "Patient registered successfully",
            "patient_id": patient_id,
            "patient": {
                "name": f"{request.first_name} {request.last_name}",
                "email": request.email,
                "phone": request.phone
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error registering patient: {str(e)}"
        )


@app.get("/api/patients/phone/{phone}", tags=["Patients"])
async def get_patient_by_phone(phone: str):
    """Get patient information by phone number"""
    try:
        patient = PatientDB.get_patient_by_phone(phone)
        
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found"
            )
        
        # Remove sensitive info
        patient.pop('medical_history', None)
        
        return {
            "success": True,
            "patient": patient
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching patient: {str(e)}"
        )


# APPOINTMENT ENDPOINTS

@app.post("/api/appointments/book", tags=["Appointments"])
async def book_appointment(request: AppointmentBookRequest):
    """
    Book a new appointment.
    Sends email notifications to both doctor and patient.
    """
    try:
        from datetime import datetime
        
        # Verify patient exists
        patient = PatientDB.get_patient_by_phone(request.patient_phone)
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found. Please register first."
            )
        
        # Verify doctor exists
        doctor = DoctorDB.get_doctor_by_id(request.doctor_id)
        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Doctor not found"
            )
        
        # Parse date and time
        appt_date = datetime.strptime(request.appointment_date, '%Y-%m-%d').date()
        appt_time = datetime.strptime(request.appointment_time, '%H:%M').time()
        
        # Check if slot is available
        available_slots_result = DoctorDB.get_available_slots(request.doctor_id, appt_date)
        available_slots = available_slots_result.get("available_slots", [])
        time_str = appt_time.strftime('%H:%M')
        
        if time_str not in available_slots:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Time slot not available"
            )
        
        # Create appointment
        appointment_id = AppointmentDB.create_appointment(
            patient_id=patient['patient_id'],
            doctor_id=request.doctor_id,
            appointment_date=appt_date,
            appointment_time=appt_time,
            reason_for_visit=request.reason_for_visit,
            symptoms=request.symptoms
        )
        
        # Send emails
        email_service.send_appointment_request_to_doctor(
            doctor_email=doctor['email'],
            doctor_name=doctor['name'],
            patient_name=f"{patient['first_name']} {patient['last_name']}",
            patient_email=patient['email'],
            patient_phone=patient['phone'],
            appointment_date=appt_date,
            appointment_time=appt_time,
            reason=request.reason_for_visit,
            symptoms=request.symptoms
        )
        
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
        
        return {
            "success": True,
            "message": "Appointment booked successfully! Emails sent to doctor and patient.",
            "appointment_id": appointment_id,
            "appointment": {
                "patient": f"{patient['first_name']} {patient['last_name']}",
                "doctor": doctor['name'],
                "specialization": doctor['specialization'],
                "date": request.appointment_date,
                "time": request.appointment_time,
                "fee": float(doctor['consultation_fee'])
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error booking appointment: {str(e)}"
        )


@app.get("/api/appointments/patient/{phone}", tags=["Appointments"])
async def get_patient_appointments(phone: str, include_past: bool = False):
    """Get all appointments for a patient"""
    try:
        patient = PatientDB.get_patient_by_phone(phone)
        
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found"
            )
        
        appointments = AppointmentDB.get_patient_appointments(
            patient['patient_id'],
            include_past=include_past
        )
        
        return {
            "success": True,
            "patient": f"{patient['first_name']} {patient['last_name']}",
            "count": len(appointments),
            "appointments": appointments
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching appointments: {str(e)}"
        )


@app.get("/api/appointments/{appointment_id}", tags=["Appointments"])
async def get_appointment(appointment_id: int):
    """Get details of a specific appointment"""
    try:
        appointment = AppointmentDB.get_appointment_by_id(appointment_id)
        
        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found"
            )
        
        return {
            "success": True,
            "appointment": appointment
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching appointment: {str(e)}"
        )


@app.post("/api/appointments/cancel", tags=["Appointments"])
async def cancel_appointment(request: AppointmentCancelRequest):
    """
    Cancel an appointment.
    Sends email notifications to both doctor and patient.
    """
    try:
        # Verify patient
        patient = PatientDB.get_patient_by_phone(request.patient_phone)
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found"
            )
        
        # Get appointment
        appointment = AppointmentDB.get_appointment_by_id(request.appointment_id)
        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found"
            )
        
        # Verify ownership
        if appointment['patient_id'] != patient['patient_id']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only cancel your own appointments"
            )
        
        # Check if cancellable
        if appointment['status'] not in ['Scheduled', 'Confirmed']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel appointment with status: {appointment['status']}"
            )
        
        # Cancel appointment
        AppointmentDB.cancel_appointment(
            appointment_id=request.appointment_id,
            cancelled_by='Patient',
            cancellation_reason=request.cancellation_reason
        )
        
        # Send emails
        from send_email import email_service
        doctor = DoctorDB.get_doctor_by_id(appointment['doctor_id'])
        
        email_service.send_cancellation_to_doctor(
            doctor_email=doctor['email'],
            doctor_name=doctor['name'],
            patient_name=appointment['patient_name'],
            appointment_date=appointment['appointment_date'],
            appointment_time=appointment['appointment_time'],
            cancellation_reason=request.cancellation_reason
        )
        
        email_service.send_cancellation_to_patient(
            patient_email=patient['email'],
            patient_name=f"{patient['first_name']} {patient['last_name']}",
            doctor_name=appointment['doctor_name'],
            appointment_date=appointment['appointment_date'],
            appointment_time=appointment['appointment_time']
        )
        
        return {
            "success": True,
            "message": "Appointment cancelled successfully! Emails sent to doctor and patient.",
            "appointment_id": request.appointment_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cancelling appointment: {str(e)}"
        )


# ERROR HANDLERS

@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Not Found", "detail": "The requested resource was not found"}
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "detail": "An unexpected error occurred"}
    )

# STARTUP & SHUTDOWN EVENTS

# @app.on_event("startup")
# async def startup_event():
    # """Run on server startup"""
    # print("\n" + "="*70)
    # print("🏥 Healthcare Appointment API Starting...")
    # print("="*70)
    
    # Test database connection
    # if test_connection():
    #     print("✅ Database connection successful")
    # else:
    #     print("⚠️  Database connection failed - some features may not work")
    
    # Check voice service
    # if voice_service.enabled:
    #     print("✅ Voice service enabled")
    # else:
    #     print("⚠️  Voice service disabled")
    
    # print(f"✅ API Documentation: http://localhost:8000/docs")
    # print(f"✅ Alternative Docs: http://localhost:8000/redoc")
    # print("="*70 + "\n")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on server shutdown"""
    # print("\n" + "="*70)
    # print("👋 Healthcare Appointment API Shutting Down...")
    # print("="*70 + "\n")

@app.get("/")
async def serve_index():
    return FileResponse(INDEX_PATH)

@app.get("/routes")
async def list_routes():
    return [route.path for route in app.routes]


if __name__ == "__main__":
    # Get configuration from environment
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    debug = os.getenv("DEBUG_MODE", "True").lower() == "true"
    
    # print("\n🚀 Starting Healthcare Appointment API Server...")
    print(f"🌐 Server: http://{host}:{port}")
    print(f"📚 Docs: http://{host}:{port}/docs")
    print(f"🎤 Voice: Enabled" if voice_service.enabled else "🎤 Voice: Disabled")
    print(f"🔧 Debug Mode: {debug}\n")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )