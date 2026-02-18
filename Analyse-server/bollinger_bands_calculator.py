import logging
import numpy as np

class BollingerBandsCalculator:
    def __init__(self, period=20):
        self.period = period

    def calculate_bollinger_bands(self, prices):
        if len(prices) < self.period:
            logging.warning("Not enough data to calculate Bollinger Bands.")
            return None, None, None

        sma = np.mean(prices[-self.period:])
        std_dev = np.std(prices[-self.period:])
        upper_band = sma + (2 * std_dev)
        lower_band = sma - (2 * std_dev)

        logging.info(f"Calculated Bollinger Bands: SMA={sma}, Upper Band={upper_band}, Lower Band={lower_band}")
        return sma, upper_band, lower_band