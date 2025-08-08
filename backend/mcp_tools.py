# mcp_tools.py - REAL MCP TOOLS with Mock Payment Processing
import os
import json
import requests
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from openai import OpenAI
import hashlib
import random
import string
import re

logger = logging.getLogger(__name__)

# Initialize real API clients
AMADEUS_CLIENT_ID = os.getenv("AMADEUS_CLIENT_ID")
AMADEUS_CLIENT_SECRET = os.getenv("AMADEUS_CLIENT_SECRET")
RAPID_API_KEY = os.getenv("RAPID_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI for intelligent processing
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
print("DEBUG  ‣ OPENAI_API_KEY starts with:", OPENAI_API_KEY[:10] if OPENAI_API_KEY else "None")



import json, logging
from datetime import datetime

def _translate_flight_query(
    origin: str,
    destination: str,
    dep_text: str,
    ret_text: Optional[str] = None
) -> tuple[str, str, str, Optional[str]]:
    """
    1) Normalize free-form → IATA + ISO dates via GPT
    2) Bump any date < today into next year
    """
    if not openai_client:
        return origin[:3].upper(), destination[:3].upper(), dep_text, ret_text

    today = datetime.utcnow().date()
    prompt = f"""
Assume today's date is {today.isoformat()}.
Return EXACTLY this JSON shape:
  {{ "origin":"IATA","destination":"IATA","departure":"YYYY-MM-DD","return":"YYYY-MM-DD or null" }}

• If user omitted the year, pick the next occurrence (>= today).
• Only ISO dates, only 3-letter IATA codes.

Origin text      : {origin}
Destination text : {destination}
Departure text   : {dep_text}
Return text      : {ret_text or ""}
"""
    logging.debug("💬 _translate_flight_query prompt:\n" + prompt.strip())

    rsp = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        max_tokens=40,
        messages=[{"role": "user", "content": prompt.strip()}]
    )

    raw = rsp.choices[0].message.content.strip()
    if raw.startswith("```"):
        import re
        raw = re.sub(r"^```(?:json)?\s*", "", raw)      # strip opening fence
        raw = re.sub(r"\s*```$", "", raw)               # strip closing fence

    try:
        data = json.loads(raw)
    except Exception as e:
        logger.warning("⚠️  JSON parsing failed: %s – falling back.", e)
        return (
            origin[:3].upper(),
            destination[:3].upper(),
            dep_text,
            ret_text,
        )
    logging.debug("🧠 GPT returned normalization: " + json.dumps(data))

    for key in ("departure", "return"):
        d_str = data.get(key)
        if d_str and d_str.lower() != "null":
            d = datetime.fromisoformat(d_str).date()
            if d < today:
                bumped = d.replace(year=today.year + 1)
                data[key] = bumped.isoformat()
                logging.debug(f"⏫ Bumped {key} from {d.isoformat()} → {bumped.isoformat()}")

    return (
        data["origin"].upper(),
        data["destination"].upper(),
        data["departure"],
        data.get("return")
    )


def _validate_iata(code: str) -> str:
    """
    Ensure `code` is a real 3-letter airport:
    - if already 3 alpha chars, pass through
    - otherwise call Amadeus /v1/reference-data/locations autocomplete
    """
    code = code.strip().upper()
    if len(code) == 3 and code.isalpha():
        return code

    token = amadeus_api.get_token()
    if not token:
        raise ValueError("Amadeus credentials missing")

    url = f"{amadeus_api.base_url}/v1/reference-data/locations"
    resp = requests.get(
        url,
        params={"keyword": code, "subType": "AIRPORT"},
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    if resp.status_code == 200:
        items = resp.json().get("data", [])
        if items:
            return items[0]["iataCode"]

    raise ValueError(f"Unknown airport '{code}'")



class AmadeusAPI:
    """Real Amadeus API integration for flights"""
    
    def __init__(self):
        self.token = None
        self.token_expiry = 0
        self.base_url = "https://test.api.amadeus.com"
        self.token_url = "https://test.api.amadeus.com/v1/security/oauth2/token"
    
    def get_token(self) -> Optional[str]:
        import time
        # cache check
        if self.token and time.time() < self.token_expiry:
            return self.token

        if not AMADEUS_CLIENT_ID or not AMADEUS_CLIENT_SECRET:
            logger.error("Amadeus credentials not configured in ENV")
            return None

        try:
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            data = {
                "grant_type": "client_credentials",
                "client_id": AMADEUS_CLIENT_ID,
                "client_secret": AMADEUS_CLIENT_SECRET
            }
            resp = requests.post(self.token_url, headers=headers, data=data, timeout=15)
            logger.debug(f"Amadeus token endpoint responded {resp.status_code}: {resp.text}")
            if resp.status_code == 200:
                js = resp.json()
                self.token = js["access_token"]
                self.token_expiry = time.time() + js.get("expires_in", 1799)
                logger.info("✅ Amadeus token obtained")
                return self.token
            else:
                logger.error(f"❌ Amadeus token request failed: {resp.status_code} {resp.reason}")
                return None
        except Exception as e:
            logger.exception("❌ Error getting Amadeus token")
            return None
    
    def search_flights_real(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        adults: int = 1
    ) -> Dict:
        """
        Search for real flights using Amadeus API.
        1) Normalize free-form → IATA + ISO dates via GPT
        2) Validate IATA codes via autocomplete
        3) Call Amadeus flight-offers
        """
        # ── 1) normalize via GPT ─────────────────────────────────
        logging.debug(f"🔄 Translating query: {origin}, {destination}, {departure_date}, {return_date}")
        origin, destination, departure_date, return_date = _translate_flight_query(
            origin, destination, departure_date, return_date
        )
        logging.debug(f"→ Translated to: {origin}, {destination}, {departure_date}, {return_date}")

        # ── 2) validate IATA codes ───────────────────────────────
        try:
            origin = _validate_iata(origin)
            destination = _validate_iata(destination)
            logging.debug(f"✓ Valid IATA: {origin}, {destination}")
        except ValueError as ve:
            logging.error(f"✖ IATA validation error: {ve}")
            return {"error": str(ve)}

        # ── 3) actual Amadeus call ───────────────────────────────
        token = self.get_token()
        if not token:
            return {"error": "Amadeus API not configured"}

        params = {
            "originLocationCode": origin,
            "destinationLocationCode": destination,
            "departureDate": departure_date,
            "adults": adults,
            "currencyCode": "USD",
            "max": 10
        }
        if return_date:
            params["returnDate"] = return_date

        endpoint = f"{self.base_url}/v2/shopping/flight-offers"
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(endpoint, headers=headers, params=params, timeout=15)

        if resp.status_code != 200:
            logging.error(f"❌ Amadeus {resp.status_code} {resp.reason} – {resp.text}")
            return {"error": f"Amadeus {resp.status_code}: {resp.text}"}

        return resp.json()
            
class BookingAPI:
    """Real hotel search using Booking.com via RapidAPI"""
    
    def search_hotels_real(self, location: str, check_in: str, check_out: str,
                           guests: int = 1, rooms: int = 1) -> Dict:


        check_in  = _translate_flight_query("","",check_in)[2]   # reuse date normaliser
        check_out = _translate_flight_query("","",check_out)[2]

        """Search real hotels using Booking.com API"""
        if not RAPID_API_KEY:
            return {"error": "RapidAPI key not configured"}
        
        try:
            # First, search for destination
            dest_url = "https://booking-com15.p.rapidapi.com/api/v1/hotels/searchDestination"
            headers = {
                'x-rapidapi-key': RAPID_API_KEY,
                'x-rapidapi-host': "booking-com15.p.rapidapi.com"
            }
            
            dest_response = requests.get(
                dest_url,
                headers=headers,
                params={"query": location},
                timeout=10
            )
            
            if dest_response.status_code != 200:
                return {"error": f"Location search failed: {dest_response.status_code}"}
            
            dest_data = dest_response.json()
            if not dest_data.get("data"):
                return {"error": f"No locations found for: {location}"}
            
            dest_id = dest_data["data"][0]["dest_id"]
            
            # Search hotels
            search_url = "https://booking-com15.p.rapidapi.com/api/v1/hotels/searchHotels"
            
            search_response = requests.get(
                search_url,
                headers=headers,
                params={
                    "dest_id": dest_id,
                    "search_type": "CITY",
                    "arrival_date": check_in,
                    "departure_date": check_out,
                    "adults": guests,
                    "room_qty": rooms,
                    "page_number": "1",
                    "units": "metric",
                    "temperature_unit": "c",
                    "languagecode": "en-us",
                    "currency_code": "USD"
                },
                timeout=15
            )
            
            if search_response.status_code == 200:
                return search_response.json()
            else:
                return {"error": f"Hotel search failed: {search_response.status_code}"}
                
        except Exception as e:
            logger.error(f"Hotel search error: {e}")
            return {"error": str(e)}

# Initialize API clients
amadeus_api = AmadeusAPI()
booking_api = BookingAPI()


def get_airport_code_intelligent(city_name: str) -> str:
    """Use LLM to intelligently convert city to airport code"""
    if not openai_client:
        return city_name[:3].upper()
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "system",
                "content": "You are an airport code expert. Return ONLY the 3-letter IATA code."
            }, {
                "role": "user",
                "content": f"What is the main airport code for {city_name}? Reply with ONLY the 3-letter code, nothing else."
            }],
            max_tokens=10,
            temperature=0
        )
        code = response.choices[0].message.content.strip().upper()
        if len(code) == 3:
            return code
        return city_name[:3].upper()
    except:
        return city_name[:3].upper()

def generate_booking_reference() -> str:
    """Generate a realistic booking reference"""
    prefix = random.choice(['AA', 'DL', 'UA', 'BA', 'LH', 'AF', 'HTL', 'BKG'])
    numbers = ''.join(random.choices(string.digits, k=6))
    return f"{prefix}{numbers}"

def generate_mock_booking_response(*_):
    """
    Legacy placeholder removed: returns an empty dict so no fake totals,
    policies or prices can slip into user-visible text.
    """
    return {}

@tool
def search_flights(origin: str,
                   destination: str,
                   departure_date: str,
                   return_date: Optional[str] = None,
                   passengers: int = 1) -> Dict:
    """
    Live flight-offer search (Amadeus).  Returns **raw API JSON** so the
    assistant can format it any way it likes.
    """
    # normalise + validate
    origin, destination, departure_date, return_date = _translate_flight_query(
        origin, destination, departure_date, return_date
    )
    origin, destination = _validate_iata(origin), _validate_iata(destination)

    return amadeus_api.search_flights_real(
        origin, destination, departure_date, return_date, passengers
    )



@tool
def search_hotels(location: str,
                  check_in: str,
                  check_out: str,
                  guests: int = 1,
                  rooms: int = 1) -> Dict:
    """
    Live hotel search (Booking.com via RapidAPI).  Returns **raw API JSON**.
    """
    return booking_api.search_hotels_real(
        location, check_in, check_out, guests, rooms
    )


import redis

REDIS_URL               = os.getenv("REDIS_URL", "redis://localhost:6379/0")
BOOKING_HOLD_EXPIRY_SEC = 7 * 24 * 3600          # 1 week

rds = redis.Redis.from_url(REDIS_URL, decode_responses=True)
log = logging.getLogger(__name__)


def _rand_ref(prefix: str) -> str:
    return f"{prefix}{''.join(random.choices(string.ascii_uppercase + string.digits, k=6))}"

def _store(ref: str, data: Dict, ttl: int = BOOKING_HOLD_EXPIRY_SEC) -> None:
    rds.set(ref, json.dumps(data), ex=ttl)

def _fetch(ref: str) -> Optional[Dict]:
    val = rds.get(ref)
    return json.loads(val) if val else None


@tool
def book_flight(flight_id: str,
                passenger_name: str,
                passenger_email: str,
                passenger_phone: Optional[str] = None) -> Dict:
    """
    Hold a flight offer.  No payment, no ticket issuance.
    """
    ref = _rand_ref("FL")
    payload = {
        "booking_reference": ref,
        "status":            "HELD_NO_PAYMENT",
        "held_at_utc":       datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "flight_id":         flight_id,
        "passenger": {
            "name":  passenger_name,
            "email": passenger_email,
            "phone": passenger_phone
        }
    }
    _store(ref, payload)
    return payload


@tool
def book_hotel(hotel_id: str,
               guest_name: str,
               guest_email: str,
               check_in: str,
               check_out: str,
               guests: int = 1) -> Dict:
    """
    Hold a hotel room.  No payment collected.
    """
    ref = _rand_ref("HT")
    payload = {
        "booking_reference": ref,
        "status":            "HELD_NO_PAYMENT",
        "held_at_utc":       datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "hotel_id":          hotel_id,
        "check_in":          check_in,
        "check_out":         check_out,
        "guests":            guests,
        "guest": {
            "name":  guest_name,
            "email": guest_email
        }
    }
    _store(ref, payload)
    return payload



@tool
def get_booking_details(booking_reference: str) -> Dict:
    """
    Fetch whatever we have stored for this reference.
    """
    data = _fetch(booking_reference)
    if not data:
        return {"error": f"Reference {booking_reference} not found"}
    return data


@tool
def cancel_booking(booking_reference: str,
                   reason: Optional[str] = None) -> Dict:
    """
    Mark a stored booking as CANCELLED.
    """
    data = _fetch(booking_reference)
    if not data:
        return {"error": f"Reference {booking_reference} not found"}

    data["status"]     = "CANCELLED"
    data["cancelled"]  = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    if reason:
        data["cancel_reason"] = reason
    _store(booking_reference, data)          # reset TTL
    return data


@tool
def reschedule_booking(booking_reference: str,
                       new_date: str,
                       booking_type: str = "flight") -> Dict:
    """
    Update departure / check-in date for the held booking.
    """
    data = _fetch(booking_reference)
    if not data:
        return {"error": f"Reference {booking_reference} not found"}

    if booking_type.lower() == "flight":
        data["new_departure"] = new_date
    else:
        data["new_check_in"]  = new_date
    data["status"] = "RESCHEDULE_REQUESTED"
    _store(booking_reference, data)
    return data



@tool
def create_itinerary(trip_name: str,
                     start_date: str,
                     end_date: str,
                     destinations: List[str]) -> Dict:
    """
    Just packages the request; GPT will turn this into nice prose.
    """
    return {
        "trip":      trip_name,
        "start":     start_date,
        "end":       end_date,
        "stops":     destinations
    }


def get_real_mcp_tools():
    """
    Import this in your workflow to expose the fixed tools.
    """
    return [
        search_flights,
        search_hotels,
        book_flight,
        book_hotel,
        get_booking_details,
        cancel_booking,
        reschedule_booking,
        create_itinerary,
    ]
