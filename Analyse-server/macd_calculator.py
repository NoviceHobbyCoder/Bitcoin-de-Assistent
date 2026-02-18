import logging
import numpy as np

class MacdCalculator:
    def __init__(self, short_period=12, long_period=26, signal_period=9):
        self.short_period = short_period
        self.long_period = long_period
        self.signal_period = signal_period

    def calculate_macd(self, prices):
        if len(prices) < self.long_period + self.signal_period:
            logging.warning("Not enough data to calculate MACD.")
            return None, None, None

        short_ema = self.calculate_ema(prices, self.short_period)
        long_ema = self.calculate_ema(prices, self.long_period)
        macd_line = short_ema[-len(long_ema):] - long_ema
        signal_line = self.calculate_ema(macd_line, self.signal_period)
        macd_histogram = macd_line[-len(signal_line):] - signal_line

        logging.info(f"Calculated MACD: MACD Line={macd_line[-1]}, Signal Line={signal_line[-1]}, Histogram={macd_histogram[-1]}")
        return macd_line[-1], signal_line[-1], macd_histogram[-1]

    def calculate_ema(self, prices, period):
        ema = [np.mean(prices[:period])]
        multiplier = 2 / (period + 1)
        for price in prices[period:]:
            ema.append((price - ema[-1]) * multiplier + ema[-1])
        return np.array(ema)