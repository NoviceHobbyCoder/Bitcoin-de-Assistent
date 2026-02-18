import logging

class RsiCalculator:
    def __init__(self, period=21):
        self.period = period

    def calculate_rsi(self, prices):
        if len(prices) < self.period:
            logging.warning("Not enough data to calculate RSI.")
            return None

        gains = []
        losses = []

        for i in range(1, len(prices)):
            change = prices[i] - prices[i - 1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(-change)

        avg_gain = sum(gains[-self.period:]) / self.period
        avg_loss = sum(losses[-self.period:]) / self.period

        if avg_loss == 0:
            logging.info("No losses, RSI is 100.")
            return 100  # Avoid division by zero, RSI is 100 if no losses

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        logging.info(f"Calculated RSI: {rsi}")
        return rsi

    def calculate_rsi_for_trading_pairs(self, trading_pair_data):
        rsi_values = {}
        for trading_pair, prices in trading_pair_data.items():
            rsi = self.calculate_rsi(prices)
            rsi_values[trading_pair] = rsi
        return rsi_values