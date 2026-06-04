from src.execution.market_adapters.base import MarketAdapter
from src.execution.pretrade_proposal import numeric


class DemoMarketAdapter(MarketAdapter):
    adapter_id = "demo_market"
    live_submission = False

    def submit_bids(self, bids, submitted_at):
        submitted_bids = []

        for index, bid in enumerate(bids):
            submitted_bids.append(
                build_demo_submission_bid(
                    bid=bid,
                    index=index,
                    submitted_at=submitted_at,
                )
            )

        summary = summarize_submitted_bids(submitted_bids)

        return {
            "adapter_id": self.adapter_id,
            "status": "demo_settled",
            "submitted_at": submitted_at,
            "live_submission": self.live_submission,
            "summary": summary,
            "bids": submitted_bids,
        }


def build_demo_submission_bid(bid, index, submitted_at):
    bid_id = bid.get("bid_id") or bid.get("order_id") or f"bid-{index + 1:03d}"
    volume_mwh = numeric(
        bid.get("risk_adjusted_volume_mwh")
        or bid.get("energy_mwh")
        or bid.get("volume_mwh")
    )
    price = numeric(
        bid.get("risk_adjusted_limit_price_eur_mwh")
        or bid.get("limit_price_eur_mwh")
        or bid.get("price_limit_eur_mwh")
    )
    accepted = should_accept_bid(bid=bid, index=index)
    status = "awarded" if accepted else "rejected"

    return {
        **bid,
        "bid_id": bid_id,
        "demo_submission_id": f"demo-sub-{index + 1:03d}",
        "submitted_at": submitted_at,
        "submission_status": "accepted" if accepted else "rejected",
        "award_status": status,
        "accepted_volume_mwh": round(volume_mwh, 4) if accepted else 0.0,
        "award_price_eur_mwh": round(price, 2) if accepted else None,
        "award_notional_eur": round(volume_mwh * price, 2) if accepted else 0.0,
        "rejection_reason": None if accepted else "demo_market_price_not_crossed",
    }


def should_accept_bid(bid, index):
    confidence_band = bid.get("forecast_confidence_band")
    risk_status = bid.get("risk_status")

    if confidence_band == "low" or risk_status == "restricted":
        return False

    return index % 4 != 3


def summarize_submitted_bids(bids):
    accepted = [bid for bid in bids if bid.get("submission_status") == "accepted"]
    rejected = [bid for bid in bids if bid.get("submission_status") == "rejected"]
    awarded = [bid for bid in bids if bid.get("award_status") == "awarded"]

    return {
        "submitted_bid_count": len(bids),
        "accepted_bid_count": len(accepted),
        "rejected_bid_count": len(rejected),
        "awarded_bid_count": len(awarded),
        "notional_eur": round(
            sum(numeric(bid.get("award_notional_eur")) for bid in awarded),
            2,
        ),
    }
