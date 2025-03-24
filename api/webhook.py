from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/', methods=['POST'])
def webhook():
    try:
        logger.info("Webhook received!")
        logger.info(f"Form data: {dict(request.form)}")
        
        # Create TwiML response
        resp = MessagingResponse()
        resp.message("Hello! Your message was received.")
        
        return str(resp), 200, {'Content-Type': 'text/xml'}
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        resp = MessagingResponse()
        resp.message("An error occurred")
        return str(resp), 200, {'Content-Type': 'text/xml'} 