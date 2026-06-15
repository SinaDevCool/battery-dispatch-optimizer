from abc import ABC, abstractmethod


class MarketAdapter(ABC):
    adapter_id = "base"
    live_submission = False

    @abstractmethod
    def submit_bids(self, bids, submitted_at):
        raise NotImplementedError



