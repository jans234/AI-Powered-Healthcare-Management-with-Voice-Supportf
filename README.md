# 🏥 Healthcare Appointment Agent with AI Voice Assistant

An AI-powered healthcare appointment booking system featuring text chat and voice interaction, built with FastAPI, LangGraph, OpenAI (GPT-4, Whisper, TTS), and MySQL.
This system enables patients to find doctors, book appointments, manage schedules, and interact naturally via chat or voice.

# ✨ Key Features

## 🤖 AI Agent

LangGraph-based conversational agent

Context-aware multi-step workflows

Tool-using AI (doctor search, booking, cancellation, etc.)

## 🎤 Voice & Chat

Text chat interface

Voice input (OpenAI Whisper – STT)

Voice output (OpenAI TTS – 6 voices)

Seamless chat ↔ voice switching

## 📅 Appointment Management

Book, view, cancel, and reschedule appointments

Real-time doctor availability

Automatic email notifications

## 🩺 Doctor Discovery

Search by specialization

Doctor profiles (experience, fees, schedules)

AI-based doctor recommendations

## 📧 Notifications

HTML email confirmations

Doctor & patient alerts

SMTP-based email service

## 🛠 Tech Stack

Backend

FastAPI

LangChain + LangGraph

OpenAI (GPT-4, Whisper, TTS)

Database

MySQL

Frontend

HTML, CSS, JavaScript

Web Audio API

# 📁 Project Structure

healthcare-appointment-system/
├── main.py              # FastAPI app & routes
├── workflow.py          # LangGraph agent workflow
├── tools.py             # AI tools (booking, search, etc.)
├── database.py          # MySQL operations
├── voice_service.py     # STT & TTS
├── send_email.py        # Email notifications
├── healthcare.sql       # Database schema
├── requirements.txt
├── .env.example
└── interface/
    └── index.html       # Web UI (chat + voice)


