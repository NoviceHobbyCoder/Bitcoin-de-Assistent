import logging

class StochasticOscillatorCalculator:
    def __init__(self, period=14):
        self.period = period

    def calculate_stochastic_oscillator(self, prices):
        if len(prices) < self.period:
            logging.warning("Not enough data to calculate Stochastic Oscillator.")
            return None

        highest_high = max(prices[-self.period:])
        lowest_low = min(prices[-self.period:])
        current_close = prices[-1]

        if highest_high == lowest_low:
            return 100  # Avoid division by zero

        stochastic_oscillator = ((current_close - lowest_low) / (highest_high - lowest_low)) * 100
        logging.info(f"Calculated Stochastic Oscillator: {stochastic_oscillator}")
        return stochastic_oscillator