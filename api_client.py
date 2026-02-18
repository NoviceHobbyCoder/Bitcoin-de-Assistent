from hmac import new as hmac_new
from hashlib import md5, sha256
import hashlib 
import hmac 
import time
import requests
import json
import threading 
from datetime import datetime
from urllib.parse import urlencode

class BitcoinDeApiClient:
    def __init__(self, api_key, api_secret, api_basic, logger):
        self.api_key = api_key
        self.api_secret = api_secret
        self.api_basic = api_basic
        self.logger = logger
        self.base_url = "https://api.bitcoin.de/v4"

    def log_message(self, message, level="DEBUG"):
        """Helper method to log messages using the provided logger"""
        if hasattr(self.logger, level.lower()):
            getattr(self.logger, level.lower())(message)

    def get_basic_rates(self, trading_pair):
        """Get rates using Basic API"""
        try:
            url = f"{self.base_url}/{trading_pair}/basic/rate.json"
            params = {'apikey': self.api_basic}
            
            self.logger.info(f"Fetching rates for {trading_pair}")
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            self.logger.info(f"Rates response: {json.dumps(data, indent=2)}")
            
            # Add trading pair to response for identification
            if 'data' in data:
                data['data']['trading_pair'] = trading_pair
            return data
            
        except Exception as e:
            self.logger.error(f"Error fetching basic rates: {str(e)}")
            if hasattr(e, 'response'):
                self.logger.error(f"Response content: {e.response.text}")
            raise

    def make_api_request(self, endpoint, params=None):
        try:
            endpoint = endpoint.lstrip('/')
            url = f"{self.base_url}/{endpoint}"
            nonce = str(int(datetime.now().timestamp() * 1000000))
    
            # Always use empty string MD5 hash for GET requests
            md5_hash = 'd41d8cd98f00b204e9800998ecf8427e'
    
            # Create HMAC input data
            hmac_data = '#'.join([
                'GET',  # Always GET
                url,
                self.api_key,
                nonce,
                md5_hash
            ])
    
            self.logger.info("=== GET Request Details ===")
            self.logger.debug(f"Endpoint: {endpoint}")
            self.logger.debug(f"Full URL: {url}")
            self.logger.debug(f"Nonce: {nonce}")
            self.logger.debug(f"MD5 hash: {md5_hash}")
            self.logger.debug(f"HMAC data: {hmac_data}")
    
            # Create HMAC-SHA256 signature
            signature = hmac.new(
                self.api_secret.encode('utf-8'),
                hmac_data.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
    
            self.logger.debug(f"Generated signature: {signature}")
    
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-API-KEY': self.api_key,
                'X-API-NONCE': nonce,
                'X-API-SIGNATURE': signature
            }
    
            self.logger.debug("Headers:")
            for key, value in headers.items():
                self.logger.debug(f"{key}: {value}")
    
            if params:
                self.logger.debug(f"Query parameters: {params}")
    
            # Enable requests debug logging
            import http.client as http_client
            http_client.HTTPConnection.debuglevel = 1
    
            # Make GET request
            response = requests.get(url, headers=headers, params=params)
    
            # Reset debug level
            http_client.HTTPConnection.debuglevel = 0
    
            # Log response details
            self.logger.info("=== Response Details ===")
            self.logger.info(f"Status code: {response.status_code}")
            self.logger.debug(f"Response headers: {dict(response.headers)}")
            
            try:
                response_json = response.json()
                self.logger.info(f"Response body: {json.dumps(response_json, indent=2)}")
            except json.JSONDecodeError:
                self.logger.debug(f"Raw response body: {response.text}")
    
            response.raise_for_status()
            return response.json()
    
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                self.logger.error(f"Error response: {e.response.text}")
            raise
       
    def create_signature(self, method, endpoint, nonce, params=None):
        try:
            # Ensure endpoint doesn't start with slash
            endpoint = endpoint.lstrip('/')
    
            # Construct the full URI
            uri = f"{self.base_url}/{endpoint}"
    
            # For POST requests with params, create MD5 hash of URL-encoded params
            if method == "POST" and params:
                # Sort parameters
                sorted_params = dict(sorted(params.items()))
                
                # Create URL-encoded string with proper encoding
                encoded_params = []
                for key, value in sorted_params.items():
                    # Properly encode the key (especially for array-style parameters)
                    encoded_key = key.replace('[', '%5B').replace(']', '%5D')
                    
                    if isinstance(value, (list, tuple)):
                        formatted_value = str(value[0])
                    elif isinstance(value, float):
                        formatted_value = str(value)
                    else:
                        formatted_value = str(value)
                    
                    # URL encode the value
                    encoded_value = requests.utils.quote(formatted_value)
                    encoded_params.append(f"{encoded_key}={encoded_value}")
                
                url_encoded_query = '&'.join(encoded_params)
                self.logger.debug(f"URL-encoded query for MD5: {url_encoded_query}")
                md5_hash = hashlib.md5(url_encoded_query.encode('utf-8')).hexdigest()
            else:
                md5_hash = 'd41d8cd98f00b204e9800998ecf8427e'
    
            # Create HMAC input data
            hmac_data = '#'.join([
                method,
                uri,
                self.api_key,
                nonce,
                md5_hash
            ])
    
            self.logger.debug(f"HMAC data: {hmac_data}")
    
            # Create HMAC-SHA256 signature
            signature = hmac.new(
                self.api_secret.encode('utf-8'),
                hmac_data.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
    
            self.logger.debug(f"Generated signature: {signature}")
            return signature
    
        except Exception as e:
            self.logger.error(f"Error creating signature: {str(e)}")
            raise
     
    def make_post_request(self, endpoint, params):
        try:
            method = 'POST'
            nonce = str(int(datetime.now().timestamp() * 1000000))
            
            # Prepare the complete form data first
            form_data = {
                'max_amount_currency_to_trade': str(params['max_amount']),
                'min_amount_currency_to_trade': str(params['max_amount']),  # Same as max by default
                'price': str(params['price']),
                'type': params['type'],
                'new_order_for_remaining_amount': '1',
                'only_kyc_full': '1'
            }
            
            # Add optional parameters
            if 'end_datetime' in params:
                form_data['end_datetime'] = params['end_datetime']
            if 'min_trust_level' in params:
                form_data['min_trust_level'] = params['min_trust_level']
            if 'payment_option' in params:
                form_data['payment_option'] = str(params['payment_option'])
            if 'sepa_option' in params:
                form_data['sepa_option'] = str(params['sepa_option'])
            if 'seat_of_bank' in params:
                if isinstance(params['seat_of_bank'], (list, tuple)):
                    for i, country in enumerate(params['seat_of_bank']):
                        form_data[f'seat_of_bank[{i}]'] = country
                else:
                    form_data['seat_of_bank[0]'] = params['seat_of_bank']
            
            # Sort form data alphabetically
            sorted_form_data = dict(sorted(form_data.items()))
            
            # Get signature using all parameters
            signature = self.create_signature(
                method=method,
                endpoint=endpoint,
                nonce=nonce,
                params=sorted_form_data  # Use all sorted parameters for signature
            )
            
            request_uri = f"{self.base_url}/{endpoint}"
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-API-KEY': self.api_key,
                'X-API-NONCE': nonce,
                'X-API-SIGNATURE': signature
            }
            
            self.logger.debug("Request details:")
            self.logger.debug(f"URI: {request_uri}")
            self.logger.debug("Headers:")
            for key, value in headers.items():
                self.logger.debug(f"{key}: {value}")
            self.logger.debug(f"Form data (sorted): {sorted_form_data}")
            
            # Enable requests debug logging
            import http.client as http_client
            http_client.HTTPConnection.debuglevel = 1
            
            # Make request with sorted form data
            response = requests.post(request_uri, headers=headers, data=sorted_form_data)
            
            # Reset debug level
            http_client.HTTPConnection.debuglevel = 0
            
            # Log response details
            self.logger.info("=== Response Details ===")
            self.logger.info(f"Status code: {response.status_code}")
            self.logger.debug(f"Response headers: {dict(response.headers)}")
            
            try:
                response_json = response.json()
                self.logger.info(f"Response body: {json.dumps(response_json, indent=2)}")
            except json.JSONDecodeError:
                self.logger.debug(f"Raw response body: {response.text}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                self.logger.error(f"Error response: {e.response.text}")
            raise
     
    def create_order(self, trading_pair, type, max_amount_currency_to_trade, price, 
                    end_datetime=None, min_trust_level=None,
                    payment_option=None, sepa_option=None,
                    seat_of_bank=None):
        """Create a new order on Bitcoin.de"""
        endpoint = f"{trading_pair}/orders"
        
        # Build parameters
        params = {
            "type": type,
            "max_amount": float(max_amount_currency_to_trade),
            "price": float(price)
        }
        
        # Add optional parameters if provided
        if end_datetime:
            params["end_datetime"] = end_datetime
        if min_trust_level:
            params["min_trust_level"] = min_trust_level
        if payment_option is not None:
            params["payment_option"] = int(payment_option)
        if sepa_option is not None:
            params["sepa_option"] = int(sepa_option)
        if seat_of_bank:
            params["seat_of_bank"] = seat_of_bank
    
        try:
            self.logger.info(f"Creating order for {trading_pair}: {json.dumps(params, indent=2)}")
            response = self.make_post_request(endpoint, params)
            
            if response is None:
                self.logger.error("Received None response from API")
                raise ValueError("Received None response from API")
            
            self.logger.info(f"API response: {json.dumps(response, indent=2)}")
            return response
                
        except Exception as e:
            self.logger.error(f"Failed to create order: {str(e)}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                self.logger.error(f"API Error Response: {e.response.text}")
            raise
                 
    def get_account_info(self):
        """Get account information using Full API"""
        try:
            self.log_message("Fetching account info...")
            return self.make_api_request('account')  # Removed method="GET"
        except Exception as e:
            self.log_message(f"Error fetching account info: {str(e)}", level="ERROR")
            raise

    def get_orders(self):
        """
        Get all active orders
        GET https://api.bitcoin.de/v4/orders
        """
        try:
            # Use make_api_request method
            response = self.make_api_request('orders')
            
            if response and 'orders' in response:
                self.logger.info(f"Successfully retrieved {len(response['orders'])} orders")
                return response
            else:
                self.logger.warning("No orders data in response")
                return {"orders": []}
                
        except Exception as e:
            self.logger.error(f"Error getting orders: {str(e)}")
            return {"orders": []}
    
    def delete_order(self, trading_pair, order_id):
        """
        Delete a specific order
        DELETE https://api.bitcoin.de/v4/:trading_pair/orders/:order_id
        """
        try:
            endpoint = f"{trading_pair}/orders/{order_id}"
            endpoint = endpoint.lstrip('/')
            url = f"{self.base_url}/{endpoint}"
            nonce = str(int(datetime.now().timestamp() * 1000000))
    
            # Always use empty string MD5 hash for DELETE requests
            md5_hash = 'd41d8cd98f00b204e9800998ecf8427e'
    
            # Create HMAC input data
            hmac_data = '#'.join([
                'DELETE',  # Use DELETE method
                url,
                self.api_key,
                nonce,
                md5_hash
            ])
    
            self.logger.info("=== DELETE Request Details ===")
            self.logger.debug(f"Endpoint: {endpoint}")
            self.logger.debug(f"Full URL: {url}")
            self.logger.debug(f"Nonce: {nonce}")
            self.logger.debug(f"MD5 hash: {md5_hash}")
            self.logger.debug(f"HMAC data: {hmac_data}")
    
            # Create HMAC-SHA256 signature
            signature = hmac.new(
                self.api_secret.encode('utf-8'),
                hmac_data.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
    
            self.logger.debug(f"Generated signature: {signature}")
    
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-API-KEY': self.api_key,
                'X-API-NONCE': nonce,
                'X-API-SIGNATURE': signature
            }
    
            self.logger.debug("Headers:")
            for key, value in headers.items():
                self.logger.debug(f"{key}: {value}")
    
            # Enable requests debug logging
            import http.client as http_client
            http_client.HTTPConnection.debuglevel = 1
    
            # Make DELETE request
            response = requests.delete(url, headers=headers)
    
            # Reset debug level
            http_client.HTTPConnection.debuglevel = 0
    
            # Log response details
            self.logger.info("=== Response Details ===")
            self.logger.info(f"Status code: {response.status_code}")
            self.logger.debug(f"Response headers: {dict(response.headers)}")
            
            try:
                response_json = response.json()
                self.logger.info(f"Response body: {json.dumps(response_json, indent=2)}")
            except json.JSONDecodeError:
                self.logger.debug(f"Raw response body: {response.text}")
    
            response.raise_for_status()
            return response.json()
    
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                self.logger.error(f"Error response: {e.response.text}")
            raise
      
    def validate_credentials(self) -> bool:
        """Validate API credentials"""
        return bool(self.api_key and self.api_secret)

    def take_post_request(self, endpoint, params):
        try:
            method = 'POST'
            nonce = str(int(datetime.now().timestamp() * 1000000))
        
            # Prepare the complete form data first
            form_data = {
                'amount_currency_to_trade': str(params['amount_currency_to_trade']),
                'type': params['type']
            }
        
            # Add optional parameters
            if 'payment_option' in params:
                form_data['payment_option'] = str(params['payment_option'])

            # Sort form data alphabetically
            sorted_form_data = dict(sorted(form_data.items()))

            # Get signature using all parameters
            signature = self.create_signature(
                method=method,
                endpoint=endpoint,
                nonce=nonce,
                params=sorted_form_data  # Use all sorted parameters for signature
            )

            request_uri = f"{self.base_url}/{endpoint}"

            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-API-KEY': self.api_key,
                'X-API-NONCE': nonce,
                'X-API-SIGNATURE': signature
            }

            self.logger.info("=== Request details ===")
            self.logger.debug(f"URI: {request_uri}")
            self.logger.debug("Headers:")
            for key, value in headers.items():
                self.logger.debug(f"{key}: {value}")
            self.logger.debug(f"Form data (sorted): {sorted_form_data}")

            # Enable requests debug logging
            import http.client as http_client
            http_client.HTTPConnection.debuglevel = 1

            # Make request with sorted form data
            response = requests.post(request_uri, headers=headers, data=sorted_form_data)

            # Reset debug level
            http_client.HTTPConnection.debuglevel = 0

            # Log response details
            self.logger.info("=== Response Details ===")
            self.logger.info(f"Status code: {response.status_code}")
            self.logger.debug(f"Response headers: {dict(response.headers)}")

            try:
                response_json = response.json()
                self.logger.info(f"Response body: {json.dumps(response_json, indent=2)}")
            except json.JSONDecodeError:
                self.logger.debug(f"Raw response body: {response.text}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                self.logger.error(f"Error response: {e.response.text}")
            raise   
    
        # Kaufen
    def take_order(self, trading_pair, order_id, type, amount_currency_to_trade, payment_option=None):
        """Take an order on Bitcoin.de"""
        endpoint = f"{trading_pair}/trades/{order_id}"

        # Build parameters
        params = {
            "type": type,
            "amount_currency_to_trade": float(amount_currency_to_trade)
        }

        # Add optional parameters if provided  
        if payment_option is not None:
            params["payment_option"] = int(payment_option)

        try:
            self.logger.info(f"Taking order {trading_pair}: {json.dumps(params, indent=2)}")
            response = self.take_post_request(endpoint, params)

            if response is None:
                self.logger.error("Received None response from API")
                raise ValueError("Received None response from API")

            self.logger.info(f"API response: {json.dumps(response, indent=2)}")
            return response

        except Exception as e:
            self.logger.error(f"Failed to take order: {str(e)}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                self.logger.error(f"API Error Response: {e.response.text}")
            raise

        # Verkaufen
    def take_buy_order(self, trading_pair, order_id, amount_currency_to_trade, payment_option=None):
        """Take a buy order on Bitcoin.de"""
        endpoint = f"{trading_pair}/trades/{order_id}"
    
        # Set default payment_option to 2 if not provided
        if payment_option is None:
            payment_option = 2
    
        # Build parameters
        params = {
            "type": "buy",
            "amount_currency_to_trade": float(amount_currency_to_trade),
            "payment_option": int(payment_option)
        }
    
        try:
            self.logger.info(f"Taking buy order {trading_pair}: {json.dumps(params, indent=2)}")
            response = self.take_post_request(endpoint, params)
    
            if response is None:
                self.logger.error("Received None response from API")
                raise ValueError("Received None response from API")
    
            self.logger.info(f"API response: {json.dumps(response, indent=2)}")
            return response
    
        except Exception as e:
            self.logger.error(f"Failed to take buy order: {str(e)}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                self.logger.error(f"API Error Response: {e.response.text}")
            raise

    def make_api_request_ledger(self, endpoint, params=None):
        try:
            endpoint = endpoint.lstrip('/')
            url = f"{self.base_url}/{endpoint}"
            nonce = str(int(datetime.now().timestamp() * 1000000))
    
            # Always use empty string MD5 hash for GET requests
            md5_hash = 'd41d8cd98f00b204e9800998ecf8427e'
    
            # URL encode the parameters
            if params:
                query_string = urlencode(params)
                url = f"{url}?{query_string}"
    
            # Create HMAC input data
            hmac_data = '#'.join([
                'GET',  # Always GET
                url,
                self.api_key,
                nonce,
                md5_hash
            ])
    
            self.logger.info("=== GET Request Details ===")
            self.logger.debug(f"Endpoint: {endpoint}")
            self.logger.debug(f"Full URL: {url}")
            self.logger.debug(f"Nonce: {nonce}")
            self.logger.debug(f"MD5 hash: {md5_hash}")
            self.logger.debug(f"HMAC data: {hmac_data}")
    
            # Create HMAC-SHA256 signature
            signature = hmac.new(
                self.api_secret.encode('utf-8'),
                hmac_data.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
    
            self.logger.debug(f"Generated signature: {signature}")
    
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-API-KEY': self.api_key,
                'X-API-NONCE': nonce,
                'X-API-SIGNATURE': signature
            }
    
            self.logger.debug("Headers:")
            for key, value in headers.items():
                self.logger.debug(f"{key}: {value}")
    
            if params:
                self.logger.debug(f"Query parameters: {params}")
    
            # Enable requests debug logging
            import http.client as http_client
            http_client.HTTPConnection.debuglevel = 1
    
            # Make GET request
            response = requests.get(url, headers=headers)
    
            # Reset debug level
            http_client.HTTPConnection.debuglevel = 0
    
            # Log response details
            self.logger.info("=== Response Details ===")
            self.logger.info(f"Status code: {response.status_code}")
            self.logger.debug(f"Response headers: {dict(response.headers)}")
            
            try:
                response_json = response.json()
                self.logger.info(f"Response body: {json.dumps(response_json, indent=2)}")
            except json.JSONDecodeError:
                self.logger.debug(f"Raw response body: {response.text}")
    
            response.raise_for_status()
            return response_json
    
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                self.logger.error(f"Error response: {e.response.text}")
            raise

    def get_all_account_ledgers(self, currencies, datetime_start='2013-01-20T15:00:00+02:00', type='all', page=1):
        """Get account ledger for all specified currencies using Full API"""
        all_entries = {}
        for currency in currencies:
            try:
                endpoint = f"{currency}/account/ledger"
                self.logger.debug(f"Fetching account ledger for {currency}")

                # Build query parameters
                params = {
                    'datetime_start': datetime_start,
                    'type': type,
                    'page': page
                }

                currency_entries = []
                current_page = page
                last_page = None

                while last_page is None or current_page <= last_page:
                    params['page'] = current_page
                    response = self.make_api_request_ledger(endpoint, params)
                    
                    if 'account_ledger' in response:
                        currency_entries.extend(response['account_ledger'])
                    
                    if 'page' in response:
                        current_page = response['page']['current']
                        last_page = response['page']['last']
                        current_page += 1
                    else:
                        break
                
                all_entries[currency] = currency_entries
            except Exception as e:
                self.logger.error(f"Error fetching account ledger for {currency}: {str(e)}")
                if hasattr(e, 'response'):
                    self.logger.error(f"Response: {e.response.text}")
                raise
        return all_entries