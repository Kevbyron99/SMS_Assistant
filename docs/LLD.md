# Implementation Checklist

## Core Infrastructure (Complete)
- [x] Set up Flask application with Twilio webhook
- [x] Implement basic message handling
- [x] Configure environment variables
- [x] Set up logging system

## Message Parser (Complete)
- [x] Implement basic message parsing
- [x] Set up OpenAI integration
- [x] Create intent classification system
- [x] Implement command routing

## Memory System (Airtable) (Mostly Complete)
- [x] Set up Airtable base
- [x] Implement conversation storage
- [x] Create context retrieval system
- [ ] Build preference learning system

## Weather Service (Priority 1)
- [ ] Connect to OpenWeather API
- [ ] Implement location-based weather queries
- [ ] Create weather forecast formatting
- [ ] Add temperature unit preferences (C/F)
- [ ] Support for current conditions vs. forecasts

## Transport Service (Priority 2)
- [ ] Research and select alternative to Darwin API
- [ ] Set up Transport API authentication
- [ ] Implement station/stop lookup for Urmston
- [ ] Create departure board functionality
- [ ] Support route planning queries
- [ ] Add service disruption alerts

## Shift Tracking System (Priority 3)
- [ ] Design Airtable base for shift storage
- [ ] Create shift data input methods
- [ ] Implement shift query functionality
- [ ] Add reminders for upcoming shifts
- [ ] Support weekly schedule summarization

## Movie Recommendations (Priority 4)
- [ ] Set up TMDB API integration
- [ ] Implement genre-based recommendations
- [ ] Create popular/trending movie queries
- [ ] Support rating-based filtering
- [ ] Add personalized recommendations based on history

## Email Service (Priority 5)
- [ ] Research secure email API options
- [ ] Implement IMAP/Gmail authentication
- [ ] Create inbox summary functionality
- [ ] Support email search and reading
- [ ] Add email flagging/categorization
- [ ] Implement security best practices

## General Knowledge Enhancement
- [ ] Refine OpenAI Assistant prompting
- [ ] Create specialized prompts for recipes
- [ ] Improve context handling for multi-turn conversations
- [ ] Implement knowledge domain routing

## Security & Error Handling
- [x] Implement Twilio request validation
- [x] Set up API key management
- [x] Create error handling system
- [ ] Implement rate limiting
- [ ] Add API fallback mechanisms
- [ ] Improve error reporting and recovery

## Testing & Quality Assurance
- [ ] Create test cases for each service
- [ ] Implement unit tests for critical components
- [ ] Set up integration testing
- [ ] Add load/performance testing
- [ ] Create documentation for end users

## Future Enhancements (Backlog)
- [ ] Calendar integration
- [ ] Shopping list management
- [ ] Voice message transcription
- [ ] Image recognition capabilities
- [ ] Smart home device control
- [ ] Health data tracking

---

# Low-Level Design: WhatsApp Personal Assistant

## 1. Component Breakdown

### 1.1 Message Handler
```python
# app.py
@app.route("/webhook", methods=['POST'])
def webhook():
    # Validate Twilio request
    # Parse incoming message
    # Route to appropriate handler
    # Return formatted response
```

### 1.2 Message Parser
```python
# services/message_parser.py
def parse_message(message: str) -> dict:
    # Use NLP to understand intent
    # Extract key information
    # Route to appropriate handler
```

### 1.3 Service Handlers

#### Weather Handler
```python
# handlers/weather.py
def handle_weather_request(location: str) -> str:
    # Validate location
    # Call OpenWeather API
    # Format response
```

#### Movie Handler
```python
# handlers/movies.py
def handle_movie_request(criteria: str) -> str:
    # Parse movie criteria
    # Query TMDB API
    # Format recommendations
```

#### Email Handler
```python
# handlers/email.py
def handle_email_request(command: str) -> str:
    # Gmail OAuth2/App Password auth
    # Connect via IMAP (imap.gmail.com:993)
    # Execute Gmail operations
    # Handle email data securely
    # Support Gmail-specific features
```

#### Transport Handler
```python
# handlers/transport.py
class TransportHandler:
    def __init__(self, tfgm_api_key: str, rail_api_key: str):
        self.tfgm_api_key = tfgm_api_key
        self.rail_api_key = rail_api_key
        self.manchester_stations = ["MAN", "MCV", "MCO", "SFD"]  # Station codes
        
    async def get_nearby_stops(self, lat: float, lon: float) -> List[Dict]:
        """Get nearby bus/train stops"""
        return [{"id": "stop_id", "name": "stop_name", "distance": "distance_meters"}]
        
    async def get_departures(self, stop_id: str) -> List[Dict]:
        """Get real-time departures from stop"""
        return [{"line": "line_number", "destination": "dest", "time": "departure_time"}]
        
    async def get_journey(self, from_stop: str, to_stop: str) -> Dict:
        """Plan journey between stops"""
        return {"duration": "mins", "changes": "num_changes", "steps": ["step1", "step2"]}
        
    async def get_service_alerts(self) -> List[str]:
        """Get service disruption info"""
        return ["Alert 1", "Alert 2"]
    
    def format_response(self, data: Dict) -> str:
        """Format response for WhatsApp"""
        return "Next bus: Route 123 arriving in 5 minutes"
```

#### Shift Handler
```python
# handlers/shift.py
def handle_shift_request(query: str, user_id: str) -> str:
    # Parse shift query
    # Query Airtable for shifts
    # Format shift schedule response
```

```python
class ShiftEntry:
    date: datetime
    start_time: datetime
    end_time: datetime
    location: str
    notes: Optional[str]
```

#### Image Processing Handler
```python
# handlers/image_processor.py
def handle_image_request(image_url: str, query_type: str) -> str:
    # Download image from WhatsApp/Twilio
    # Perform OCR on image
    # Parse schedule/rota data
    # Store extracted data in Airtable
    # Return confirmation or extracted info
```

```python
class ImageData:
    image_url: str
    processed_text: str
    data_type: str  # 'rota', 'schedule', etc.
    extracted_data: Dict
    timestamp: datetime
```

#### AI Conversation Handler
```python
# handlers/ai_conversation.py
def handle_ai_request(query: str, context: List[Dict]) -> str:
    # Prepare conversation context
    # Call OpenAI API
    # Format complex response
    # Update conversation memory
```

## 2. Data Models

### 2.1 Chat History Service
```python
class ChatMemorySystem:
    def save_interaction(self, data: Dict):
        """
        Store chat interaction with metadata
        - sender: str
        - message: str
        - response: str
        - intent: str
        - context: Dict
        - timestamp: datetime
        - metadata: Dict
        """
        pass

    def get_relevant_history(self, 
        sender: str, 
        intent: str = None, 
        keyword: str = None,
        limit: int = 10
    ) -> List[Dict]:
        """Get contextually relevant history"""
        pass

    def get_user_preferences(self, sender: str) -> Dict:
        """Extract learned preferences from history"""
        pass

    def summarize_context(self, history: List[Dict]) -> str:
        """Create AI-readable context from history"""
        pass

class ConversationManager:
    def __init__(self, memory_system: ChatMemorySystem):
        self.memory = memory_system
        
    async def process_message(self, 
        sender: str,
        message: str
    ) -> str:
        """
        1. Get relevant history
        2. Create context for AI
        3. Generate response
        4. Save interaction
        5. Return response
        """
        pass
```

### 2.2 Message Model
```python
class Message:
    sender: str
    content: str
    timestamp: datetime
    intent: str
    parameters: dict
```

### 2.2 Response Model
```python
class Response:
    message: str
    media: Optional[str]
    quick_replies: List[str]
```

## 3. API Integrations

### 3.1 OpenWeather API
- Endpoint: `/data/2.5/weather`
- Parameters: location, units
- Response: temperature, conditions, humidity

### 3.2 TMDB API
- Endpoint: `/movie/popular`
- Parameters: page, language
- Response: movie list, details

### 3.3 Email (IMAP)
- Connection: SSL/TLS
- Operations: READ, SEARCH
- Folder management

### 3.4 Transport APIs
- TfGM API
  - Endpoints: buses, trams, stations
  - Real-time departures
  - Service status
- National Rail API
  - Train schedules
  - Live departures
  - Station information

## 4. Error Handling

### 4.1 Error Types
```python
class ServiceError(Exception):
    service: str
    error_code: int
    message: str
```

### 4.2 Error Responses
```python
def handle_error(error: ServiceError) -> str:
    # Log error
    # Format user-friendly message
    # Return appropriate response
```

## 5. Configuration Management

### 5.1 Environment Variables
```python
# config.py
TWILIO_ACCOUNT_SID = os.environ['TWILIO_ACCOUNT_SID']
TWILIO_AUTH_TOKEN = os.environ['TWILIO_AUTH_TOKEN']
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
# Other API keys and configurations
```

## 6. Logging System

### 6.1 Log Structure
```python
class LogEntry:
    timestamp: datetime
    level: str
    service: str
    message: str
    metadata: dict
```

### 6.2 Log Handlers
```python
def log_request(request: dict):
    # Log request details
    # Track performance
    # Monitor errors
```

## 7. Testing Strategy

### 7.1 Unit Tests
```python
def test_message_parser():
    # Test intent detection
    # Test parameter extraction
    # Test routing logic
```

### 7.2 Integration Tests
```python
def test_weather_service():
    # Test API integration
    # Test response formatting
    # Test error handling
```

## 8. Deployment Configuration

### 8.1 Server Configuration
```python
# main.py
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
```

### 8.2 Dependencies
```toml
[tool.poetry.dependencies]
python = "^3.11"
flask = "^3.0.0"
twilio = "^9.0.0"
openai = "^1.0.0"
requests = "^2.31.0"