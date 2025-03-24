import os
import logging
import aiohttp
import json
import datetime
from typing import Dict, Any
from .base_handler import BaseHandler

logger = logging.getLogger(__name__)

class TransportHandler(BaseHandler):
    def __init__(self):
        super().__init__()
        # Use the TransportAPI key
        self.api_key = os.getenv('TRANSPORT_API_KEY')
        self.app_id = os.getenv('TRANSPORT_APP_ID', 'personal-assistant')
        self.base_url = "https://transportapi.com/v3/uk"
        self.default_station = os.getenv('DEFAULT_STATION', 'Urmston')
        
        # Enable simulation for testing/development
        sim_value = os.getenv('TRANSPORT_SIMULATION', 'true')
        self.simulation_mode = sim_value.lower() in ['true', '1', 'yes']
        logger.info(f"Transport simulation mode: {sim_value} -> {self.simulation_mode}")
        
        # Map of station names to 3-letter CRS codes
        self.station_codes = {
            # Manchester area
            "urmston": "URM",
            "manchester": "MAN",  # Manchester Piccadilly
            "manchester piccadilly": "MAN",
            "manchester oxford road": "MCO",
            "manchester victoria": "MCV",
            "stockport": "SPT",
            "altrincham": "ALT",
            "trafford park": "TRA",
            "bolton": "BON",
            "wigan": "WGN",  # Wigan North Western
            
            # Liverpool area
            "liverpool": "LIV",  # Liverpool Lime Street
            "liverpool south parkway": "LPY",
            "birkenhead": "BKQ",  # Birkenhead Central
            
            # London area
            "london": "EUS",  # London Euston (as a default for London)
            "london euston": "EUS",
            "london kings cross": "KGX",
            "london paddington": "PAD",
            "london waterloo": "WAT",
            "london bridge": "LBG",
            
            # Other major cities
            "birmingham": "BHM",  # Birmingham New Street
            "leeds": "LDS",
            "york": "YRK",
            "sheffield": "SHF",
            "nottingham": "NOT",
            "newcastle": "NCL",
            "edinburgh": "EDB",
            "glasgow": "GLC",  # Glasgow Central
            
            # Cheshire
            "chester": "CTR",
            "warrington": "WAC",  # Warrington Central
            "crewe": "CRE",
            "macclesfield": "MAC"
        }
        
        # Validate API key
        if not self.api_key and not self.simulation_mode:
            logger.error("TRANSPORT_API_KEY not found in environment variables and simulation mode is off")
        else:
            if self.simulation_mode:
                logger.info("TransportHandler initialized in SIMULATION MODE")
            else:
                logger.info(f"TransportHandler initialized with API key and APP_ID: {self.app_id}")

    def _get_station_code(self, station_name: str) -> str:
        """Convert a station name to its 3-letter CRS code"""
        station_lower = station_name.lower()
        
        # Try direct lookup
        if station_lower in self.station_codes:
            return self.station_codes[station_lower]
        
        # Try partial matches
        for name, code in self.station_codes.items():
            if name in station_lower or station_lower in name:
                return code
        
        # Default fallback for unknown stations
        if station_lower == self.default_station.lower():
            return "URM"  # Urmston
        
        # Return as-is if it looks like a station code already (3 letters)
        if len(station_name) == 3 and station_name.isalpha():
            return station_name.upper()
            
        # Default
        logger.warning(f"Unknown station: {station_name}, defaulting to Manchester")
        return "MAN"  # Default to Manchester Piccadilly

    def _get_simulated_response(self, from_station: str, to_station: str, from_code: str, to_code: str) -> Dict[str, Any]:
        """Generate a simulated response for testing without a real API"""
        logger.info(f"Generating simulated response for {from_station} to {to_station}")
        
        # Get current time
        now = datetime.datetime.now()
        current_hour = now.hour
        current_minute = now.minute
        
        # Generate realistic departure times starting from current time
        departures = []
        
        # Common train operators for routes
        operators = {
            # Manchester local routes
            "URM-MCO": "Northern",
            "URM-MAN": "Northern",
            "SPT-MAN": "Northern",
            "MAN-MCO": "Northern",
            "MCO-MAN": "Northern",
            "ALT-MAN": "Northern",
            "BON-MAN": "Northern",
            
            # TransPennine routes
            "MAN-LIV": "TransPennine Express",
            "MAN-LDS": "TransPennine Express",
            "MAN-YRK": "TransPennine Express",
            "MAN-NCL": "TransPennine Express",
            "LIV-MAN": "TransPennine Express",
            
            # Avanti routes
            "MAN-EUS": "Avanti West Coast",
            "EUS-MAN": "Avanti West Coast",
            "LIV-EUS": "Avanti West Coast",
            "EUS-LIV": "Avanti West Coast",
            "BHM-EUS": "Avanti West Coast",
            
            # LNER routes
            "KGX-YRK": "LNER",
            "KGX-NCL": "LNER",
            "KGX-EDB": "LNER",
            
            # CrossCountry routes
            "BHM-MAN": "CrossCountry",
            "BHM-NOT": "CrossCountry",
            "BHM-SHF": "CrossCountry",
            
            # Default by region
            "default": "Northern"
        }
        
        # Train types by route
        train_types = {
            # Local services
            "URM-MCO": ["Stopping Service", "Local Service"],
            "URM-MAN": ["Stopping Service", "Local Service"],
            "MCO-MAN": ["Stopping Service", "Local Service"],
            "SPT-MAN": ["Stopping Service", "Local Service"],
            
            # Intercity services
            "MAN-EUS": ["Intercity", "Express Service"],
            "EUS-MAN": ["Intercity", "Express Service"],
            "LIV-EUS": ["Intercity", "Express Service"],
            "KGX-YRK": ["Intercity", "Express Service"],
            "KGX-NCL": ["Intercity", "Express Service"],
            "KGX-EDB": ["Intercity", "Express Service"],
            
            # Regional services
            "MAN-LIV": ["Express Service", "Fast Service"],
            "MAN-LDS": ["Express Service", "Fast Service"],
            "MAN-SHF": ["Express Service", "Fast Service"],
            "MAN-YRK": ["Express Service", "Fast Service"],
            
            # Default services
            "default": ["Local Service", "Stopping Service"]
        }
        
        # Define common intervals between trains for different routes
        intervals = {
            # Local services - more frequent
            "URM-MCO": [15, 20, 30],  # Minutes between trains
            "URM-MAN": [15, 20, 30],
            "MCO-MAN": [10, 15, 20],
            "SPT-MAN": [15, 20, 30],
            
            # Intercity services - less frequent
            "MAN-EUS": [30, 60, 90],
            "EUS-MAN": [30, 60, 90],
            "LIV-EUS": [30, 60, 90],
            "KGX-YRK": [30, 60],
            "KGX-NCL": [60, 90],
            "KGX-EDB": [60, 120],
            
            # Regional services - medium frequency
            "MAN-LIV": [15, 30, 45],
            "MAN-LDS": [30, 45, 60],
            "MAN-SHF": [30, 45, 60],
            
            # Default
            "default": [20, 30, 40]
        }
        
        # Get the relevant operator and train type
        route_key = f"{from_code}-{to_code}"
        operator = operators.get(route_key, operators["default"])
        
        # Get available train types for this route
        available_types = train_types.get(route_key, train_types["default"])
        
        # Get intervals for this route
        route_intervals = intervals.get(route_key, intervals["default"])
        
        # Generate base departure time (rounded to nearest 5 minutes)
        base_minute = (current_minute // 5) * 5
        next_departure_mins = base_minute + 5
        
        # Generate simulated departures
        for i in range(5):
            # Calculate departure time using realistic intervals
            if i == 0:
                departure_minutes = next_departure_mins % 60
                departure_hours = current_hour + (next_departure_mins // 60)
            else:
                # Use route-specific intervals
                interval = route_intervals[i % len(route_intervals)]
                next_departure_mins += interval
                departure_minutes = next_departure_mins % 60
                departure_hours = (current_hour + (next_departure_mins // 60)) % 24
            
            # Create formatted time
            scheduled_time = f"{departure_hours:02d}:{departure_minutes:02d}"
            
            # Randomly determine if train is delayed
            is_delayed = (i % 3 == 0)  # Every third train has a delay
            
            if is_delayed:
                delay_minutes = 5 + (i * 2) % 10  # Varied delays: 5, 7, 9, 11, 3 minutes
                expected_minutes = (departure_minutes + delay_minutes) % 60
                expected_hours = (departure_hours + ((departure_minutes + delay_minutes) // 60)) % 24
                expected_time = f"{expected_hours:02d}:{expected_minutes:02d}"
                status = "Delayed"
            else:
                expected_time = scheduled_time
                status = "On time"
                
            # Platform is usually consistent for a route
            platform = str(1 + (hash(route_key) % 4))  # Platforms 1-4 based on route
            
            # Select a train type for this service
            train_type = available_types[i % len(available_types)]
            
            # For simulation purposes, add a note that this is simulated data
            sim_note = "[Simulated Data]"
            
            departures.append({
                "aimed_departure_time": scheduled_time,
                "expected_departure_time": expected_time,
                "platform": platform,
                "status": status,
                "operator_name": f"{operator} {sim_note}",
                "destination_name": self._get_full_station_name(to_code),
                "train_uid": f"T{i+1}000",
                "service": "passenger",
                "train_type": train_type,
                "is_simulated": True
            })
        
        response = {
            'success': True,
            'response': self._format_train_departures(departures, from_station, to_station)
        }
        
        return response
    
    def _get_full_station_name(self, station_code: str) -> str:
        """Convert a station code back to a readable name"""
        for name, code in self.station_codes.items():
            if code == station_code:
                # Capitalize words for display
                return ' '.join(word.capitalize() for word in name.split())
        return station_code  # Return code if name not found

    def _format_train_departures(self, departures, from_station, to_station):
        """Format departures into a user-friendly text response"""
        if not departures:
            return f"No trains found from {from_station} to {to_station} at this time."
            
        response_text = f"🚂 Next trains from {from_station} to {to_station}:\n\n"
        
        for i, train in enumerate(departures[:5]):  # Limit to 5 trains
            scheduled = train.get('aimed_departure_time', 'Unknown')
            expected = train.get('expected_departure_time', scheduled)
            platform = train.get('platform', 'TBC')
            status = train.get('status', 'On time')
            operator = train.get('operator_name', 'Unknown')
            train_type = train.get('train_type', 'Service')
            
            response_text += f"Train {i+1}:\n"
            response_text += f"Scheduled: {scheduled}\n"
            response_text += f"Expected: {expected}\n"
            response_text += f"Platform: {platform}\n"
            response_text += f"Status: {status}\n"
            response_text += f"Operator: {operator}\n"
            response_text += f"Type: {train_type}\n\n"
        
        return response_text

    async def handle(self, message: str, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Extract location from message or use default
            from_station = self.default_station
            to_station = "Manchester"  # Default destination
            
            # Enhanced message parsing for locations
            message_lower = message.lower()
            
            # Pattern: "trains/buses from X to Y"
            if "from " in message_lower and " to " in message_lower:
                parts = message_lower.split("from ")
                if len(parts) > 1:
                    location_parts = parts[1].split(" to ")
                    if len(location_parts) > 1:
                        from_station = location_parts[0].strip()
                        # Get first word or whole phrase if it's in quotes
                        to_text = location_parts[1].strip()
                        if '"' in to_text:
                            # Extract text between quotes
                            quote_parts = to_text.split('"')
                            if len(quote_parts) > 1:
                                to_station = quote_parts[1].strip()
                        else:
                            # Just get the first word or until punctuation
                            to_words = to_text.split()
                            to_station = to_words[0].rstrip(',.?!')
            
            # Pattern: "How do I get to X from Y?"
            elif " to " in message_lower and " from " in message_lower:
                if message_lower.find(" to ") < message_lower.find(" from "):
                    to_part = message_lower.split(" to ")[1].split(" from ")[0].strip()
                    from_part = message_lower.split(" from ")[1].strip().split()[0].rstrip(',.?!')
                    
                    if to_part:
                        to_station = to_part
                    if from_part:
                        from_station = from_part
            
            # Pattern: "trains to X" (using default origin)
            elif " to " in message_lower and "from" not in message_lower:
                to_part = message_lower.split(" to ")[1].strip().split()[0].rstrip(',.?!')
                if to_part:
                    to_station = to_part
            
            # Special case for Oxford Road
            if "oxford road" in message_lower:
                to_station = "manchester oxford road"
            
            logger.info(f"Parsed locations - From: {from_station} To: {to_station}")
            
            # Convert station names to CRS codes
            from_code = self._get_station_code(from_station)
            to_code = self._get_station_code(to_station)
            
            logger.info(f"Station codes - From: {from_code} To: {to_code}")
            
            # If in simulation mode, return simulated data
            if self.simulation_mode:
                logger.info("Using simulation mode for response")
                return self._get_simulated_response(from_station, to_station, from_code, to_code)
            
            # Otherwise, proceed with real API call
            if not self.api_key:
                logger.error("Invalid or missing Transport API key")
                return {
                    'success': False,
                    'error': 'Transport API not configured correctly. Please check configuration.'
                }
            
            # Construct the API URL for train departures
            # Follow the exact format from the TransportAPI documentation
            request_url = f"{self.base_url}/train/station/{from_code}/live.json"
            
            # Set up request parameters exactly as required by the API
            request_params = {
                "app_id": self.app_id,
                "app_key": self.api_key,
                "calling_at": to_code,
                "darwin": "true",
                "train_status": "passenger"
            }
            
            logger.info(f"Making request to Transport API: {request_url}")
            logger.info(f"Using app_id: {self.app_id}")
            logger.info(f"API params: {request_params}")
            
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                try:
                    async with session.get(
                        request_url,
                        params=request_params,
                        ssl=True
                    ) as response:
                        response_text = await response.text()
                        logger.info(f"Transport API response status: {response.status}")
                        logger.debug(f"Response text: {response_text[:200]}")
                        
                        if response.status != 200:
                            error_msg = f"API Error: Status {response.status}"
                            if response_text:
                                try:
                                    error_data = json.loads(response_text)
                                    if 'error' in error_data:
                                        error_msg += f" - {error_data['error']}"
                                except:
                                    error_msg += f" - {response_text[:200]}..."
                            
                            logger.error(error_msg)
                            return {
                                'success': False,
                                'error': error_msg
                            }
                        
                        data = await response.json()
                        logger.info(f"Transport API response received successfully")
                        
                        # Check if we have departure data
                        if not data or 'departures' not in data or 'all' not in data['departures']:
                            return {
                                'success': True,
                                'response': f"No train departures found from {from_station} to {to_station} at this time."
                            }
                        
                        # Process departure data
                        departures = data['departures']['all']
                        if not departures:
                            return {
                                'success': True,
                                'response': f"No direct trains found from {from_station} to {to_station} at this time."
                            }
                        
                        # Format the response using the shared formatter
                        return {
                            'success': True, 
                            'response': self._format_train_departures(departures, from_station, to_station)
                        }
                
                except aiohttp.ClientError as e:
                    error_msg = f"Network Error: {str(e)}"
                    logger.error(error_msg)
                    return {'success': False, 'error': error_msg}
                
        except Exception as e:
            error_msg = f"Transport Handler Error: {str(e)}"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}

    def format_response(self, data: Dict[str, Any]) -> str:
        if data.get('success'):
            return data['response']
        return f"Sorry, I couldn't get train information at this time: {data.get('error')}"