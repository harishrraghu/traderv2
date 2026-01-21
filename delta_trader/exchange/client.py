"""
Delta Exchange API wrapper.
Reference: https://docs.delta.exchange/

Implements authentication and all necessary endpoints for trading.
"""

import time
import hmac
import hashlib
import requests
from typing import Optional, Dict, Any, List
import json


class DeltaExchangeClient:
    """
    Delta Exchange API client.

    Authentication:
    - Signature = HMAC-SHA256(secret, method + timestamp + path + query + body)
    - Headers: api-key, timestamp, signature
    """

    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://testnet-api.delta.exchange" if testnet else "https://api.delta.exchange"
        self.session = requests.Session()

    def _generate_signature(self, method: str, endpoint: str, payload: str = "") -> tuple:
        """Generate HMAC SHA256 signature for Delta API."""
        timestamp = str(int(time.time()))
        signature_data = method + timestamp + endpoint + payload
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            signature_data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return timestamp, signature

    def _request(self, method: str, endpoint: str, params: dict = None, data: dict = None, authenticated: bool = False) -> dict:
        """Make request to Delta API."""
        url = f"{self.base_url}{endpoint}"

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # Prepare payload
        payload = ""
        if data:
            payload = json.dumps(data)

        # Add query string to endpoint for signature
        query_string = ""
        if params:
            query_string = "?" + "&".join([f"{k}={v}" for k, v in params.items()])

        # Generate signature if authenticated
        if authenticated and self.api_key and self.api_secret:
            timestamp, signature = self._generate_signature(method, endpoint + query_string, payload)
            headers["api-key"] = self.api_key
            headers["timestamp"] = timestamp
            headers["signature"] = signature

        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                data=payload,
                timeout=30
            )

            # Check for errors
            if response.status_code >= 400:
                error_msg = f"API Error {response.status_code}: {response.text}"
                raise Exception(error_msg)

            return response.json()

        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {str(e)}")

    # === PUBLIC ENDPOINTS ===

    def get_products(self) -> List[Dict]:
        """Get all tradeable products/contracts."""
        result = self._request("GET", "/v2/products")
        return result.get("result", [])

    def get_ticker(self, symbol: str) -> Dict:
        """Get current ticker for a symbol."""
        result = self._request("GET", f"/v2/tickers/{symbol}")
        return result.get("result", {})

    def get_orderbook(self, symbol: str, depth: int = 20) -> Dict:
        """Get order book."""
        params = {"depth": depth}
        result = self._request("GET", f"/v2/l2orderbook/{symbol}", params=params)
        return result.get("result", {})

    def get_candles(self, symbol: str, resolution: str, start: int, end: int) -> List:
        """
        Get OHLCV candles.
        Resolution: 1m, 5m, 15m, 30m, 1h, 2h, 4h, 1d, 1w
        Start/End: Unix timestamps
        """
        params = {
            "resolution": resolution,
            "start": start,
            "end": end
        }
        result = self._request("GET", f"/v2/history/candles", params={**params, "symbol": symbol})
        return result.get("result", [])

    def get_funding_rate(self, symbol: str) -> Dict:
        """Get current funding rate."""
        try:
            ticker = self.get_ticker(symbol)
            return {
                "funding_rate": ticker.get("funding_rate", 0),
                "predicted_funding_rate": ticker.get("predicted_funding_rate", 0)
            }
        except:
            return {"funding_rate": 0, "predicted_funding_rate": 0}

    # === PRIVATE ENDPOINTS (require auth) ===

    def get_balance(self) -> Dict:
        """Get wallet balance."""
        result = self._request("GET", "/v2/wallet/balances", authenticated=True)
        return result.get("result", {})

    def get_positions(self) -> List[Dict]:
        """Get all open positions."""
        result = self._request("GET", "/v2/positions", authenticated=True)
        return result.get("result", [])

    def get_position(self, symbol: str) -> Optional[Dict]:
        """Get position for specific symbol."""
        positions = self.get_positions()
        for pos in positions:
            if pos.get("product", {}).get("symbol") == symbol:
                return pos
        return None

    def place_market_order(self, symbol: str, side: str, size: float) -> Dict:
        """
        Place market order.
        side: 'buy' or 'sell'
        """
        data = {
            "product_symbol": symbol,
            "size": size,
            "side": side,
            "order_type": "market_order"
        }
        result = self._request("POST", "/v2/orders", data=data, authenticated=True)
        return result.get("result", {})

    def place_limit_order(self, symbol: str, side: str, size: float, price: float) -> Dict:
        """Place limit order."""
        data = {
            "product_symbol": symbol,
            "size": size,
            "side": side,
            "order_type": "limit_order",
            "limit_price": str(price)
        }
        result = self._request("POST", "/v2/orders", data=data, authenticated=True)
        return result.get("result", {})

    def place_stop_order(self, symbol: str, side: str, size: float, stop_price: float) -> Dict:
        """Place stop market order."""
        data = {
            "product_symbol": symbol,
            "size": size,
            "side": side,
            "order_type": "stop_market_order",
            "stop_price": str(stop_price)
        }
        result = self._request("POST", "/v2/orders", data=data, authenticated=True)
        return result.get("result", {})

    def cancel_order(self, order_id: str) -> Dict:
        """Cancel an order."""
        result = self._request("DELETE", f"/v2/orders/{order_id}", authenticated=True)
        return result.get("result", {})

    def cancel_all_orders(self, symbol: str = None) -> Dict:
        """Cancel all open orders."""
        data = {}
        if symbol:
            data["product_symbol"] = symbol
        result = self._request("DELETE", "/v2/orders/all", data=data, authenticated=True)
        return result.get("result", {})

    def get_order(self, order_id: str) -> Dict:
        """Get order status."""
        result = self._request("GET", f"/v2/orders/{order_id}", authenticated=True)
        return result.get("result", {})

    def get_open_orders(self, symbol: str = None) -> List[Dict]:
        """Get all open orders."""
        params = {}
        if symbol:
            params["product_symbol"] = symbol
        result = self._request("GET", "/v2/orders", params=params, authenticated=True)
        return result.get("result", [])
