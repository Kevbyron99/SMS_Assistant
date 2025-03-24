import asyncio
from flask import Flask, request, abort
from twilio.twiml.messaging_response import MessagingResponse
from twilio.request_validator import RequestValidator
from services.message_parser import MessageParser
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def log_request(request_data: dict, level: str = "INFO"):
    """Structure and log request details"""
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'level': level,
        'service': 'SMS_Assistant',
        'request_data': request_data
    }
    if level == "ERROR":
        logger.error(log_entry)
    else:
        logger.info(log_entry)

# Create Flask app
app = Flask(__name__)

# Twilio credentials 
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
validator = RequestValidator(auth_token) if auth_token else None

def validate_twilio_request():
    if request.headers.get('X-Twilio-Signature') is None:
        # If no Twilio signature, assume it's a local test
        return True
        
    if not validator:
        logger.warning("No auth token set - skipping request validation")
        return True

    url = request.url
    signature = request.headers.get('X-Twilio-Signature', '')
    params = request.form

    valid = validator.validate(url, params, signature)
    if not valid:
        logger.error("Invalid Twilio signature")
    return valid

@app.route("/")
def home():
    return "Welcome to SMS Assistant!"

@app.route("/webhook", methods=['POST'])
async def webhook():
    return await handle_sms_request(request)

@app.route("/test-webhook", methods=['POST'])
async def test_webhook():
    try:
        from_number = request.form.get('From', 'test_user')
        message = request.form.get('Body', 'test_message')
        
        # Test Airtable directly
        from services.airtable_service import AirtableService
        airtable = AirtableService()
        result = airtable.store_conversation(from_number, message, "Test response")
        
        return {"status": "success", "airtable_result": result}
    except Exception as e:
        logger.exception("Test webhook error:")
        return {"status": "error", "message": str(e)}, 500

async def handle_sms_request(request):
    try:
        request_data = {
            'method': request.method,
            'url': request.url,
            'headers': dict(request.headers),
            'form_data': dict(request.form)
        }
        log_request(request_data)

        # Validate the request is from Twilio
        if not validate_twilio_request():
            log_request({'error': 'Request validation failed'}, level="ERROR")
            abort(403)

        # Get the message details
        incoming_msg = request.form.get('Body', '')
        from_number = request.form.get('From', '')

        log_request({'from': from_number, 'message': incoming_msg})

        if not incoming_msg:
            log_request({'warning': 'No message body received'}, level="WARNING")
            resp = MessagingResponse()
            resp.message("Sorry, I couldn't understand your message")
            return str(resp)

        # Parse message using OpenAI
        parser = MessageParser()
        from_number = request.form.get('From', 'default')
        result = await parser.parse_message(incoming_msg, from_number)
        if asyncio.iscoroutine(result):
            result = await result
        
        # Create response
        resp = MessagingResponse()
        response_text = result['parameters'] if isinstance(result['parameters'], str) else result['parameters'].get('ai_response', str(result['parameters']))
        
        # Store conversation in Airtable
        from services.airtable_service import AirtableService
        airtable = AirtableService()
        airtable.store_conversation(from_number, incoming_msg, response_text)
        
        resp.message(response_text)
        log_request({'response': response_text})
        return str(resp)

    except Exception as e:
        error_msg = f"Webhook error: {str(e)}"
        logger.exception(error_msg)
        log_request({'error': error_msg, 'traceback': str(e.__traceback__)}, level="ERROR")
        return {"error": error_msg}, 500

# For local development
if __name__ == "__main__":
    port = int(os.getenv('PORT', 5000))
    print(f"\nServer starting on port {port}")
    print(f"Your Repl URL is: https://{os.environ.get('REPL_SLUG')}.{os.environ.get('REPL_OWNER')}.repl.co\n")
    app.run(host="0.0.0.0", port=port)