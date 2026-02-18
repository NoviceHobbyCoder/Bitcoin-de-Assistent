import logging

class FibonacciCalculator:
    def calculate_fibonacci(self, prices):
        if len(prices) < 2:
            logging.warning("Not enough data to calculate Fibonacci levels.")
            return None

        high = max(prices)
        low = min(prices)

        fib_levels = {
            "23.6%": high - (high - low) * 0.236,
            "38.2%": high - (high - low) * 0.382,
            "50.0%": high - (high - low) * 0.500,
            "61.8%": high - (high - low) * 0.618,
            "78.6%": high - (high - low) * 0.786
        }

        logging.info(f"Calculated Fibonacci levels: {fib_levels}")
        return fib_levels