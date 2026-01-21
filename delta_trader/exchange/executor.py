"""
Order execution wrapper.
Handles order placement with proper error handling and logging.
"""

from typing import Dict, Optional
import time


class OrderExecutor:
    """
    Handles order execution with safety checks and logging.
    """

    def __init__(self, client):
        self.client = client

    def execute_market_order(
        self,
        symbol: str,
        side: str,
        size: float,
        reduce_only: bool = False
    ) -> Optional[Dict]:
        """
        Execute market order with error handling.

        Args:
            symbol: Trading symbol
            side: 'buy' or 'sell'
            size: Order size
            reduce_only: If True, only reduces position

        Returns:
            Order response dict or None if failed
        """
        try:
            print(f"Executing {side} market order: {symbol} size={size:.6f}")

            order = self.client.place_market_order(symbol, side, size)

            if order:
                print(f"  Order placed successfully: ID={order.get('id', 'N/A')}")
                return order
            else:
                print(f"  Order placement failed")
                return None

        except Exception as e:
            print(f"  Error executing order: {e}")
            return None

    def execute_limit_order(
        self,
        symbol: str,
        side: str,
        size: float,
        price: float
    ) -> Optional[Dict]:
        """Execute limit order."""
        try:
            print(f"Executing {side} limit order: {symbol} size={size:.6f} @ {price:.4f}")

            order = self.client.place_limit_order(symbol, side, size, price)

            if order:
                print(f"  Order placed successfully: ID={order.get('id', 'N/A')}")
                return order
            else:
                print(f"  Order placement failed")
                return None

        except Exception as e:
            print(f"  Error executing limit order: {e}")
            return None

    def execute_stop_order(
        self,
        symbol: str,
        side: str,
        size: float,
        stop_price: float
    ) -> Optional[Dict]:
        """Execute stop order."""
        try:
            print(f"Executing {side} stop order: {symbol} size={size:.6f} stop @ {stop_price:.4f}")

            order = self.client.place_stop_order(symbol, side, size, stop_price)

            if order:
                print(f"  Stop order placed successfully: ID={order.get('id', 'N/A')}")
                return order
            else:
                print(f"  Stop order placement failed")
                return None

        except Exception as e:
            print(f"  Error executing stop order: {e}")
            return None

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        try:
            result = self.client.cancel_order(order_id)
            print(f"Order {order_id} cancelled")
            return True
        except Exception as e:
            print(f"Error cancelling order {order_id}: {e}")
            return False

    def cancel_all_orders(self, symbol: str = None) -> bool:
        """Cancel all open orders for a symbol."""
        try:
            result = self.client.cancel_all_orders(symbol)
            print(f"All orders cancelled for {symbol if symbol else 'all symbols'}")
            return True
        except Exception as e:
            print(f"Error cancelling all orders: {e}")
            return False

    def get_order_status(self, order_id: str) -> Optional[Dict]:
        """Get order status."""
        try:
            return self.client.get_order(order_id)
        except Exception as e:
            print(f"Error getting order status: {e}")
            return None

    def wait_for_fill(self, order_id: str, timeout: int = 30) -> bool:
        """
        Wait for order to fill.

        Returns:
            True if filled, False if timeout or error
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                order = self.get_order_status(order_id)

                if order:
                    status = order.get("state", "").lower()

                    if status in ["filled", "closed"]:
                        print(f"Order {order_id} filled")
                        return True
                    elif status in ["cancelled", "rejected"]:
                        print(f"Order {order_id} {status}")
                        return False

                time.sleep(1)

            except Exception as e:
                print(f"Error checking order status: {e}")
                time.sleep(1)

        print(f"Order {order_id} fill timeout")
        return False
