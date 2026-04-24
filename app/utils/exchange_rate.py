import httpx
import time
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class ExchangeRateProvider:
    def __init__(self):
        self._cached_rate: Optional[float] = None
        self._last_update: float = 0
        self._cache_ttl: int = 3600  # 1 hour
        self._fallback_rate: float = float(os.getenv("USD_PRICE_IDR", "16000"))
        self._api_url = "https://api.coingecko.com/api/v3/simple/price?ids=usd-coin&vs_currencies=idr"

    async def get_idr_rate(self) -> float:
        """
        Fetches the current USDC/IDR rate from CoinGecko with caching.
        """
        current_time = time.time()
        
        # Return cached rate if still valid
        if self._cached_rate and (current_time - self._last_update < self._cache_ttl):
            return self._cached_rate

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self._api_url, timeout=10.0)
                response.raise_for_status()
                data = response.json()
                
                # CoinGecko response format: {"usd-coin": {"idr": 16250}}
                rate = float(data.get("usd-coin", {}).get("idr", 0))
                
                if rate > 0:
                    self._cached_rate = rate
                    self._last_update = current_time
                    logger.info(f"Updated USDC/IDR exchange rate: {rate}")
                    return rate
                else:
                    raise ValueError("Invalid rate received from API")

        except Exception as e:
            logger.error(f"Failed to fetch exchange rate from CoinGecko: {str(e)}. Using fallback.")
            # Use cached rate if available, even if expired, otherwise use fallback
            return self._cached_rate if self._cached_rate else self._fallback_rate

# Create singleton instance
exchange_rate_provider = ExchangeRateProvider()
