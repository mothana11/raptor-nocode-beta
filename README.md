Enhanced Travel Chatbot – Project Summary
Purpose
A full-stack travel assistant leveraging FastAPI, React/TypeScript, LangGraph reasoning and live supplier APIs (Amadeus flights, Booking.com hotels). The bot understands text, voice, images and file uploads, returns real flight and hotel offers, and can hold, modify or cancel mock bookings in a Redis-backed store.
Key Capabilities
• Flight search, hotel search and booking holds with realistic data
• Optional car rental, activities, insurance, visa info, currency rates, weather and alerts (12 tools total)
• Booking management: status checks, reschedule, cancel with fee rules
• Persistent user profiles, preferences and conversation history in SQLite
• Input modes: text, Web-Speech voice, file and image attachments
• LangGraph ReAct workflow to decide when to call tools; no hard-coded responses

Tech Stack
Backend: Python 3.9+, FastAPI, LangGraph, LangChain, Redis, SQLite
Frontend: React 18, Vite, TypeScript, Tailwind, Web Speech API
APIs required: OpenAI, Amadeus (production credentials), RapidAPI Booking-com

Quick Installation (demo defaults)

Clone repository and run ./quick-start.sh (Unix) – script installs Python and Node modules, seeds demo data and starts services.
Manually, create a Python virtual environment in backend/, install requirements.txt, add .env with OPENAI_API_KEY, AMADEUS_CLIENT_ID, AMADEUS_CLIENT_SECRET and RAPID_API_KEY, then run
python -m uvicorn main:app --reload --port 8000
In frontend/, run npm install then npm run dev and open http://localhost:5173.
Core API Endpoints
POST /chat send user message (text or JSON with file refs)
GET /health health and configuration status
GET /conversations/{id}/history full message history
GET /bookings list user bookings
GET /bookings/{reference} single booking details
Project Structure
backend/ FastAPI app, LangGraph workflow, tool definitions, database
frontend/ React client
uploads/ temporary file storage (local; swap for cloud in production)

Notes for Review
• The Amadeus base URL is production (https://api.amadeus.com). Sandbox returns canned data—avoid for demos.
• All date normalisation and airport-code resolution is handled by a GPT-4o-mini helper; no regex.
• Logging is verbose at DEBUG for API traffic; switch to INFO in production and remove key prefixes.
• Authentication is placeholder; integrate real auth before deployment.
• File storage is local and public; add scanning and private buckets for production use.

