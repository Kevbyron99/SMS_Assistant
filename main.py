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
    logger.info("\n=== WEBHOOK REQUEST RECEIVED ===")
    
    try:
        # Create a simple TwiML response first
        resp = MessagingResponse()
        
        # Log request details
        logger.info(f"Request Method: {request.method}")
        logger.info(f"Request URL: {request.url}")
        logger.info(f"Headers: {dict(request.headers)}")
        logger.info(f"Form Data: {dict(request.form)}")
        
        # Validate request if needed
        twilio_signature = request.headers.get('X-Twilio-Signature', 'Not Present')
        logger.info(f"Twilio Signature: {twilio_signature}")
        
        # Get the message content
        incoming_msg = request.form.get('Body', '')
        from_number = request.form.get('From', '')
        
        if not incoming_msg:
            resp.message("Sorry, I couldn't understand your message")
            return str(resp), 200, {'Content-Type': 'text/xml'}
            
        # Process the message
        try:
            parser = MessageParser()
            result = await parser.parse_message(incoming_msg, from_number)
            if asyncio.iscoroutine(result):
                result = await result
            
            response_text = result['parameters'] if isinstance(result['parameters'], str) else result['parameters'].get('ai_response', str(result['parameters']))
            resp.message(response_text)
            
        except Exception as e:
            logger.error(f"Message processing error: {str(e)}")
            resp.message("I'm having trouble processing your message. Please try again.")
        
        # Always return a valid TwiML response
        return str(resp), 200, {'Content-Type': 'text/xml'}
        
    except Exception as e:
        logger.error(f"\n=== WEBHOOK ERROR ===")
        logger.error(f"Error Type: {type(e).__name__}")
        logger.error(f"Error Message: {str(e)}")
        
        # Even on error, return a valid TwiML response
        error_resp = MessagingResponse()
        error_resp.message("An error occurred. Please try again later.")
        return str(error_resp), 200, {'Content-Type': 'text/xml'}

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

@app.route("/test", methods=['GET'])
def test():
    logger.info("Test endpoint hit")
    return {
        "status": "ok",
        "message": "Server is running",
        "twilio_configured": bool(account_sid and auth_token),
        "environment": os.getenv('ENVIRONMENT', 'development')
    }

@app.route("/test-post", methods=['POST'])
def test_post():
    logger.info("=== TEST POST ENDPOINT HIT ===")
    logger.info(f"Headers: {dict(request.headers)}")
    logger.info(f"Form Data: {dict(request.form)}")
    return {
        "status": "ok",
        "message": "POST request received",
        "headers": dict(request.headers),
        "form_data": dict(request.form)
    }

async def handle_sms_request(request):
    try:
        request_data = {
            'method': request.method,
            'url': request.url,
            'headers': dict(request.headers),
            'form_data': dict(request.form)
        }
        logger.info(f"=== Processing SMS Request ===")
        logger.info(f"Request Data: {request_data}")

        # Get the message details
        incoming_msg = request.form.get('Body', '')
        from_number = request.form.get('From', '')
        logger.info(f"Message Details - From: {from_number}, Body: {incoming_msg}")

        if not incoming_msg:
            logger.warning("No message body received")
            resp = MessagingResponse()
            resp.message("Sorry, I couldn't understand your message")
            return str(resp)

        # Parse message using OpenAI
        logger.info("Starting OpenAI message parsing")
        parser = MessageParser()
        result = await parser.parse_message(incoming_msg, from_number)
        if asyncio.iscoroutine(result):
            result = await result
        logger.info(f"OpenAI Parsing Result: {result}")
        
        # Create response
        resp = MessagingResponse()
        response_text = result['parameters'] if isinstance(result['parameters'], str) else result['parameters'].get('ai_response', str(result['parameters']))
        logger.info(f"Generated Response Text: {response_text}")
        
        # Store conversation in Airtable
        logger.info("Attempting to store conversation in Airtable")
        from services.airtable_service import AirtableService
        airtable = AirtableService()
        airtable_result = airtable.store_conversation(from_number, incoming_msg, response_text)
        logger.info(f"Airtable Storage Result: {airtable_result}")
        
        resp.message(response_text)
        final_response = str(resp)
        logger.info(f"Final Response XML: {final_response}")
        return final_response

    except Exception as e:
        logger.error(f"Handle SMS Request Error: {str(e)}")
        logger.error(f"Error Type: {type(e).__name__}")
        logger.error(f"Error Traceback: {str(e.__traceback__)}")
        return {"error": str(e)}, 500

# For local development
if __name__ == "__main__":
    port = int(os.getenv('PORT', 5000))
    print(f"\nServer starting on port {port}")
    print(f"Your Repl URL is: https://{os.environ.get('REPL_SLUG')}.{os.environ.get('REPL_OWNER')}.repl.co\n")
    app.run(host="0.0.0.0", port=port)