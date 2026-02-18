import requests
import json
import logging

class ApiClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.bitcoin.de/v4"

    def get_basic_rates(self, trading_pair):
        """Get rates using Basic API"""
        try:
            url = f"{self.base_url}/{trading_pair}/basic/rate.json"
            params = {'apikey': self.api_key}
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            logging.info(f"Fetched rates for {trading_pair}: {json.dumps(data, indent=2)}")
            return data
            
        except Exception as e:
            logging.error(f"Fehler beim Abrufen der Basisraten: {str(e)}")
            if hasattr(e, 'response'):
                logging.error(f"Antwortinhalt: {e.response.text}")
            raise