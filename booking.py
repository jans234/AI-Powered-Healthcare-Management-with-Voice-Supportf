# # # simple_test.py
# # """
# # Simple direct test - bypasses LangGraph agent
# # Tests booking and email functionality directly
# # """

# # from datetime import datetime, date, time as dt_time
# # from database import PatientDB, DoctorDB, AppointmentDB
# # from send_email import email_service
# # from colorama import init, Fore, Style

# # init(autoreset=True)

# # print("\n" + "="*70)
# # print(Fore.CYAN + Style.BRIGHT + "SIMPLE DIRECT BOOKING TEST")
# # print("="*70 + "\n")

# # # Step 1: Get patient
# # print(Fore.YELLOW + "Step 1: Getting patient...")
# # patient_phone = "+92-301-4444444"
# # patient = PatientDB.get_patient_by_phone(patient_phone)

# # if not patient:
# #     print(Fore.RED + f"Patient not found. Creating...")
# #     patient_id = PatientDB.create_patient(
# #         first_name="Ayesha",
# #         last_name="Raza", 
# #         email="ayesha.raza@email.com",
# #         phone=patient_phone,
# #         date_of_birth="1988-11-30",
# #         gender="Female",
# #         blood_group="AB+",
# #         address="Test Address"
# #     )
# #     patient = PatientDB.get_patient_by_phone(patient_phone)

# # print(Fore.GREEN + f"✅ Patient: {patient['first_name']} {patient['last_name']}")
# # print(f"   Email: {patient['email']}")

# # # Step 2: Get doctor
# # print(Fore.YELLOW + "\nStep 2: Getting doctor...")
# # doctor_id = 10  # ENT Specialist - Ahmed Khan
# # doctor = DoctorDB.get_doctor_by_id(doctor_id)
# # print(Fore.GREEN + f"✅ Doctor: {doctor['name']} ({doctor['specialization']})")

# # # Step 3: Check available slots
# # print(Fore.YELLOW + "\nStep 3: Checking available slots...")
# # appt_date = date(2025, 11, 15)  # Friday
# # slots_result = DoctorDB.get_available_slots(doctor_id, appt_date)

# # # Handle the dictionary return type
# # if isinstance(slots_result, dict):
# #     slots = slots_result.get("available_slots", [])
# #     message = slots_result.get("message", "")
# # else:
# #     slots = []
# #     message = "Unexpected response format"

# # if not slots:
# #     print(Fore.RED + "❌ No slots available on this date!")
# #     print(Fore.YELLOW + f"Message: {message}")
# #     print(Fore.YELLOW + "Checking doctor's schedule...")
# #     schedule = DoctorDB.get_doctor_schedule(doctor_id)
# #     print(Fore.CYAN + "Doctor's weekly schedule:")
# #     for s in schedule:
# #         print(f"   {s['day_of_week']}: {s['start_time']} - {s['end_time']}")
# #     exit()

# # print(Fore.GREEN + f"✅ Found {len(slots)} available slots")
# # print(f"   First few slots: {', '.join(slots[:5])}")

# # # Step 4: Book appointment
# # print(Fore.YELLOW + "\nStep 4: Booking appointment...")
# # appt_time = dt_time(11, 0)  # 11:00 AM

# # appointment_id = AppointmentDB.create_appointment(
# #     patient_id=patient['patient_id'],
# #     doctor_id=doctor_id,
# #     appointment_date=appt_date,
# #     appointment_time=appt_time,
# #     reason_for_visit="Nose bleeding consultation",
# #     symptoms="Nose bleeding and shortness of breath"
# # )

# # print(Fore.GREEN + f"✅ Appointment created! ID: {appointment_id}")

# # # Step 5: Send emails
# # print(Fore.YELLOW + "\nStep 5: Sending emails...")

# # # Email to doctor
# # print(Fore.CYAN + "   Sending email to doctor...")
# # doctor_email_sent = email_service.send_appointment_request_to_doctor(
# #     doctor_email=doctor['email'],
# #     doctor_name=doctor['name'],
# #     patient_name=f"{patient['first_name']} {patient['last_name']}",
# #     patient_email=patient['email'],
# #     patient_phone=patient['phone'],
# #     appointment_date=appt_date,
# #     appointment_time=appt_time,
# #     reason="Nose bleeding consultation",
# #     symptoms="Nose bleeding and shortness of breath"
# # )

# # # Email to patient
# # print(Fore.CYAN + "   Sending email to patient...")
# # patient_email_sent = email_service.send_appointment_confirmation_to_patient(
# #     patient_email=patient['email'],
# #     patient_name=f"{patient['first_name']} {patient['last_name']}",
# #     doctor_name=doctor['name'],
# #     doctor_specialization=doctor['specialization'],
# #     appointment_date=appt_date,
# #     appointment_time=appt_time,
# #     appointment_id=appointment_id,
# #     consultation_fee=float(doctor['consultation_fee'])
# # )

# # # Final result
# # print("\n" + "="*70)
# # print(Fore.GREEN + Style.BRIGHT + "✅ BOOKING COMPLETE!")
# # print("="*70)

# # print(Fore.CYAN + "\n📋 Booking Summary:")
# # print(f"   Appointment ID: #{appointment_id}")
# # print(f"   Patient: {patient['first_name']} {patient['last_name']}")
# # print(f"   Doctor: Dr. {doctor['name']} ({doctor['specialization']})")
# # print(f"   Date: {appt_date.strftime('%A, %B %d, %Y')}")
# # print(f"   Time: {appt_time.strftime('%I:%M %p')}")
# # print(f"   Fee: PKR {doctor['consultation_fee']}")

# # print(Fore.CYAN + "\n📧 Email Status:")
# # if doctor_email_sent:
# #     print(Fore.GREEN + "   ✅ Doctor notification sent")
# # else:
# #     print(Fore.YELLOW + "   ⚠️ Doctor email disabled or failed")

# # if patient_email_sent:
# #     print(Fore.GREEN + "   ✅ Patient confirmation sent")
# # else:
# #     print(Fore.YELLOW + "   ⚠️ Patient email disabled or failed")

# # print(Fore.CYAN + "\n💡 Next Steps:")
# # print("   1. Check patient email: " + patient['email'])
# # print("   2. Check doctor email: " + doctor['email'])
# # print("   3. View in database: SELECT * FROM appointments WHERE appointment_id = " + str(appointment_id))

# # print("\n" + "="*70)
# # print(Fore.GREEN + Style.BRIGHT + "🎉 TEST COMPLETED SUCCESSFULLY!")
# # print("="*70 + "\n")


# # workflow.py
# from typing import TypedDict, Annotated, Sequence
# from langgraph.graph import StateGraph, END
# from langgraph.prebuilt import ToolNode
# from langchain_openai import ChatOpenAI
# from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
# import operator
# from tools import healthcare_tools
# from database import PatientDB, ConversationDB
# import os
# from dotenv import load_dotenv

# load_dotenv()


# class AgentState(TypedDict):
#     """State of the agent"""
#     messages: Annotated[Sequence[BaseMessage], operator.add]
#     patient_phone: str
#     patient_id: int = None


# SYSTEM_PROMPT = """You are a professional healthcare appointment assistant. Help patients book appointments, find doctors, and manage their healthcare needs.

# **FORMATTING GUIDELINES - VERY IMPORTANT:**
# When showing doctor lists, format them as clean HTML lists:
# - Use <ul> and <li> tags for lists
# - Use <strong> tags for doctor names and key information
# - Format: <strong>Dr. Name</strong> - Specialization

# Example format:
# <ul>
# <li><strong>Dr. Sarah Johnson</strong> - Cardiologist<br>Experience: 15 years | Fee: PKR 3,000 | Rating: ⭐ 4.8</li>
# <li><strong>Dr. Michael Chen</strong> - Pediatrician<br>Experience: 10 years | Fee: PKR 2,500 | Rating: ⭐ 4.9</li>
# </ul>

# **BOOKING WORKFLOW:**
# 1. If patient phone is not provided, ask for it
# 2. When asked about doctors or specialization, call get_available_doctors
# 3. Show formatted doctor list and ask which doctor they prefer
# 4. Ask for preferred date
# 5. Call get_available_slots and show available times
# 6. Ask for reason for visit
# 7. Once you have ALL information (phone, doctor_id, date, time, reason), immediately call book_appointment
# 8. Confirm booking and inform about emails

# **REGISTRATION WORKFLOW:**
# If patient needs to register, collect:
# 1. First Name
# 2. Last Name  
# 3. Email
# 4. Phone (+92-XXX-XXXXXXX format)
# 5. Date of Birth (YYYY-MM-DD)
# 6. Gender (Male/Female/Other)
# 7. Blood Group (optional)
# 8. Address (optional)

# Then call register_new_patient with all information.

# **TIME CONVERSION:**
# - Display times in 12-hour format (9:00 AM, 2:30 PM)
# - When booking, convert to 24-hour (09:00, 14:30)
# - Conversions: 9 AM → 09:00, 10 AM → 10:00, 2 PM → 14:00, 3 PM → 15:00

# **IMPORTANT RULES:**
# - Always format responses with HTML tags for better display
# - Use <strong> for emphasis, <br> for line breaks
# - Don't repeat tool calls unnecessarily
# - Be conversational but efficient
# - After successful booking, DON'T ask what's next - just confirm success
# """


# class HealthcareAgent:
#     """LangGraph-based Healthcare Agent"""
    
#     def __init__(self):
#         self.llm = ChatOpenAI(
#             model=os.getenv('OPENAI_MODEL', 'gpt-4'),
#             temperature=0.3,
#             streaming=True
#         )
        
#         self.llm_with_tools = self.llm.bind_tools(healthcare_tools)
#         self.graph = self._create_graph()
#         self.app = self.graph.compile()
    
#     def _create_graph(self) -> StateGraph:
#         """Create the LangGraph workflow"""
#         workflow = StateGraph(AgentState)
        
#         workflow.add_node("agent", self.call_agent)
#         workflow.add_node("tools", ToolNode(healthcare_tools))
        
#         workflow.set_entry_point("agent")
        
#         workflow.add_conditional_edges(
#             "agent",
#             self.should_continue,
#             {
#                 "continue": "tools",
#                 "end": END
#             }
#         )
        
#         workflow.add_edge("tools", "agent")
        
#         return workflow
    
#     def call_agent(self, state: AgentState) -> AgentState:
#         """Call the agent with the current state"""
#         messages = state['messages']
        
#         if len(messages) == 0 or not isinstance(messages[0], SystemMessage):
#             messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)
        
#         response = self.llm_with_tools.invoke(messages)
        
#         return {"messages": [response]}
    
#     def should_continue(self, state: AgentState):
#         """Determine if we should continue to tools or end"""
#         messages = state['messages']
#         last_message = messages[-1]
        
#         if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
#             return "continue"
        
#         return "end"
    
#     def run(self, user_input: str, patient_phone: str = None, 
#             conversation_history: list = None) -> dict:
#         """Run the agent with user input"""
#         messages = []
        
#         if conversation_history:
#             messages.extend(conversation_history)
        
#         messages.append(HumanMessage(content=user_input))
        
#         initial_state = {
#             "messages": messages,
#             "patient_phone": patient_phone or ""
#         }
        
#         config = {"recursion_limit": 50}
#         result = self.app.invoke(initial_state, config=config)
        
#         final_messages = result['messages']
#         assistant_message = None
        
#         for msg in reversed(final_messages):
#             if isinstance(msg, AIMessage) and not (hasattr(msg, 'tool_calls') and msg.tool_calls):
#                 assistant_message = msg.content
#                 break
        
#         return {
#             "response": assistant_message,
#             "messages": final_messages,
#             "patient_phone": result.get('patient_phone', '')
#         }


# class ConversationManager:
#     """Manage conversations with patients"""
    
#     def __init__(self):
#         self.agent = HealthcareAgent()
#         self.conversations = {}
    
#     def chat(self, session_id: str, user_message: str, 
#              patient_phone: str = None) -> str:
#         """Send a message and get a response"""
#         history = self.conversations.get(session_id, [])
        
#         result = self.agent.run(
#             user_input=user_message,
#             patient_phone=patient_phone,
#             conversation_history=history
#         )
        
#         all_messages = result['messages']
#         if len(all_messages) > 21:
#             self.conversations[session_id] = [all_messages[0]] + all_messages[-20:]
#         else:
#             self.conversations[session_id] = all_messages
        
#         if patient_phone:
#             try:
#                 patient = PatientDB.get_patient_by_phone(patient_phone)
#                 if patient:
#                     ConversationDB.log_conversation(
#                         patient_id=patient['patient_id'],
#                         conversation_type='Text',
#                         user_message=user_message,
#                         bot_response=result['response']
#                     )
#             except Exception as e:
#                 print(f"Error logging conversation: {e}")
        
#         return result['response']
    
#     def clear_conversation(self, session_id: str):
#         """Clear conversation history for a session"""
#         if session_id in self.conversations:
#             del self.conversations[session_id]
    
#     def get_conversation_history(self, session_id: str) -> list:
#         """Get conversation history for a session"""
#         return self.conversations.get(session_id, [])


# conversation_manager = ConversationManager()









# if __name__ == "__main__":
#     # Test email service
#     from datetime import date, time
    
#     print("Testing Email Service...")
#     print("=" * 50)
    
#     # Test appointment request to doctor
#     success = email_service.send_appointment_request_to_doctor(
#         doctor_email="doctor@example.com",
#         doctor_name="Sarah Johnson",
#         patient_name="Ali Ahmad",
#         patient_email="ali@example.com",
#         patient_phone="+92-301-1111111",
#         appointment_date=date(2025, 11, 15),
#         appointment_time=time(10, 30),
#         reason="Regular checkup",
#         symptoms="Mild fever"
#     )
#     print(f"Doctor notification: {'✅ Sent' if success else '❌ Failed'}")
    
#     # Test confirmation to patient
#     success = email_service.send_appointment_confirmation_to_patient(
#         patient_email="patient@example.com",
#         patient_name="Ali Ahmad",
#         doctor_name="Sarah Johnson",
#         doctor_specialization="Cardiologist",
#         appointment_date=date(2025, 11, 15),
#         appointment_time=time(10, 30),
#         appointment_id=12345,
#         consultation_fee=3000.00
#     )
#     print(f"Patient confirmation: {'✅ Sent' if success else '❌ Failed'}")