class BatteryOptimizer:

    def __init__(self, capacity_mwh, max_power_mw):

        self.capacity_mwh = capacity_mwh
        self.max_power_mw = max_power_mw

    def decide_action(self, price):

        if price < 50:
            return "charge"

        elif price > 120:
            return "discharge"

        else:
            return "hold"


if __name__ == "__main__":

    optimizer = BatteryOptimizer(
        capacity_mwh=200,
        max_power_mw=100
    )

    prices = [40, 70, 150]

    for price in prices:

        action = optimizer.decide_action(price)

        print(f"Price: {price} €/MWh -> Action: {action}")