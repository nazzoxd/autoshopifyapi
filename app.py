# app.py

from flask import Flask, request, jsonify
import asyncio
import re
from index import process_card, fetchProducts
from utils import Utils

app = Flask(__name__)

# Proxy class to match the format expected by the `autosh` module.
class Proxy:
    def __init__(self, proxy_string):
        # Expected format: user:pass@ip:port
        if '@' in proxy_string:
            self.proxy = proxy_string
        else:
            # If no auth, just use the server part
            self.proxy = proxy_string

# Site class to match the format expected by the `autosh` module.
class Site:
    def __init__(self, url, variant_id=None):
        self.url = url
        self.variant_id = variant_id

@app.route('/autosh/site=<path:site>')
def process_card_endpoint(site):
    try:
        # 1. Get and Validate Card Information
        cc = request.args.get('cc')
        if not cc:
            return jsonify({"error": "Card information is required in the 'cc' query parameter."}), 400

        card_parts = cc.split('|')
        if len(card_parts) != 4:
            return jsonify({"error": "Invalid card format. Expected format: card_number|month|year|cvv"}), 400
        
        card_number, month, year, cvv = card_parts
        
        # Validate card number using the Luhn algorithm
        if not Utils.luhn_check(card_number):
            return jsonify({"error": "Invalid card number"}), 400
        
        # Validate month
        if not month.isdigit() or not (1 <= int(month) <= 12):
            return jsonify({"error": "Invalid month. Must be a number between 1 and 12."}), 400
            
        # Validate year
        if not year.isdigit() or len(year) not in [2, 4]:
            return jsonify({"error": "Invalid year. Must be 2 or 4 digits."}), 400
            
        # Validate CVV
        if not cvv.isdigit() or len(cvv) not in [3, 4]:
            return jsonify({"error": "Invalid CVV. Must be 3 or 4 digits."}), 400
        
        # 2. Prepare for Processing
        # Create a new asyncio event loop for the asynchronous process
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Hardcoded proxy for the request
        proxy_string = "http://user-Mdw5TwO58ewqByFP-type-residential-country-US-city-New_York:9GFLalL6ZKPZraFe@geo.g-w.info:10080"
        proxy = Proxy(proxy_string)
        proxies = [proxy]
        
        # 3. Parse Site and Variant ID
        # The site URL is passed in the path, e.g., /autosh/site=https://example.com
        # We also check for a query parameter `?variant_id=...`
        site_url = site
        variant_id = request.args.get('variant_id') # Check for variant_id in query params
        
        # Create a site object for the `autosh` module
        site_obj = Site(site_url, variant_id)
        
        # 4. Run the Core Processing Logic
        # Call the main `process_card` function from the `autosh` module
        result = loop.run_until_complete(process_card(card_number, month, year, cvv, site_obj, proxies))
        
        # 5. Format and Return the Result
        # The `process_card` function is expected to return a tuple, e.g., (success_bool, message_string, details_dict)
        if isinstance(result, tuple) and len(result) >= 2:
            if result[0]:  # If the first element (success flag) is True
                response_data = {
                    "status": "success",
                    "message": result[1],
                    "details": result[2] if len(result) > 2 else None
                }
                return jsonify(response_data)
            else: # If the success flag is False
                response_data = {
                    "status": "error",
                    "message": result[1],
                    "details": result[2] if len(result) > 2 else None
                }
                return jsonify(response_data), 400
        else:
            # Handle unexpected return types from the core function
            return jsonify({
                "status": "error",
                "message": "An unknown error occurred during processing."
            }), 500
            
    except Exception as e:
        # Catch any other exceptions and return a server error
        return jsonify({"error": f"An internal server error occurred: {str(e)}"}), 500

if __name__ == '__main__':
    # Load necessary resources (e.g., user agents) before starting the server
    Utils.load_resources()
    
    # Run the Flask application
    # host='0.0.0.0' makes it accessible from other devices on the network
    app.run(debug=True, host='0.0.0.0', port=5000)
