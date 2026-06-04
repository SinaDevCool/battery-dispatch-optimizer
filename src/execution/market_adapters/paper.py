from src.execution.market_adapters.base import MarketAdapter
from src.execution.pretrade_proposal import numeric


class PaperMarketAdapter(MarketAdapter):
    adapter_id = "paper"
    live_submission = False

    def submit_bids(self, bids, submitted_at):
        fills = []

        for index, bid in enumerate(bids):
            volume_mwh = numeric(bid.get("energy_mwh") or bid.get("volume_mwh"))
            fill_price = numeric(
                bid.get("limit_price_eur_mwh")
                or bid.get("price_limit_eur_mwh")
            )
            notional = volume_mwh * fill_price
            bid_id = bid.get("bid_id") or bid.get("order_id")

            fills.append(
                {
                    "paper_fill_id": f"paper-fill-{index + 1:03d}",
                    "bid_id": bid_id,
                    "order_id": bid.get("order_id"),
                    "delivery_time": bid.get("delivery_time"),
                    "delivery_start": bid.get("delivery_start"),
                    "delivery_end": bid.get("delivery_end"),
                    "market": bid.get("market"),
                    "market_product_id": bid.get("market_product_id"),
                    "side": bid.get("side"),
                    "requested_volume_mwh": round(volume_mwh, 4),
                    "filled_volume_mwh": round(volume_mwh, 4),
                    "limit_price_eur_mwh": round(fill_price, 2),
                    "fill_price_eur_mwh": round(fill_price, 2),
                    "notional_eur": round(notional, 2),
                    "status": "paper_filled",
                    "submission_status": "paper_filled",
                    "submitted_at": submitted_at,
                    "liquidity_assumption": "full_fill_at_limit_price",
                }
            )

        return {
            "adapter_id": self.adapter_id,
            "status": "paper_filled",
            "fills": fills,
            "live_submission": self.live_submission,
        }
