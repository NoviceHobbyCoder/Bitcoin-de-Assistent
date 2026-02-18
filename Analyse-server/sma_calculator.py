import logging

class SmaCalculator:
    def __init__(self, period=21):
        self.period = period

    def calculate_sma(self, prices):
        if len(prices) < self.period:
            logging.warning("Not enough data to calculate SMA.")
            return None

        sma = sum(prices[-self.period:]) / self.period
        logging.info(f"Calculated SMA: {sma}")
        return sma