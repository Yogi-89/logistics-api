import os
import httpx
from typing import Optional, Dict, Any
import logging
from app.utils.exchange_rate import exchange_rate_provider

# Set up logging
logger = logging.getLogger(__name__)

class CryptoValidator:
    def __init__(self):
        self.api_key = os.getenv("ETHERSCAN_API_KEY") 
        self.my_wallet = os.getenv("MY_CRYPTO_WALLET", "0x47443cef765320f815c651fab1196c7ad55789a5").lower()
        self.usdc_contract = os.getenv("USDC_CONTRACT_BASE", "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913").lower()
        self.usdt_contract = os.getenv("USDT_CONTRACT_PLASMA", "0xc2132D05D31c914a87C6611C10748AEb04B58e8F").lower()
        
        # RPC Endpoints
        self.rpc_urls = {
            "base": "https://mainnet.base.org",
            "plasma": "https://rpc.plasma.to",
            "polygon": "https://polygon-rpc.com"
        }

        # Explorer API Endpoints (Etherscan-style)
        self.explorer_apis = {
            "base": f"https://api.etherscan.io/v2/api?chainid=8453&apikey={self.api_key}",
            "plasma": "https://api.plasmascan.to/api" 
        }

    async def verify_crypto_payment(self, tx_hash: str, expected_idr_amount: float, chain: str = 'base', symbol: str = 'USDC', expected_usd: Optional[float] = None) -> Dict[str, Any]:
        """
        Verifies a transaction using Explorer APIs (Primary) with RPC fallback.
        Supports Base V2 and Plasma (XPL) identical API structure.
        """
        chain_key = chain.lower()
        api_url = self.explorer_apis.get(chain_key)
        
        # Determine target amount
        if expected_usd is None:
            idr_per_usd = await exchange_rate_provider.get_idr_rate()
            target_amount = expected_idr_amount / idr_per_usd
        else:
            target_amount = expected_usd

        # Try Explorer API first
        if api_url:
            try:
                async with httpx.AsyncClient() as client:
                    params = {
                        "module": "proxy",
                        "action": "eth_getTransactionReceipt",
                        "txhash": tx_hash
                    }
                    response = await client.get(api_url, params=params, timeout=12.0)
                    data = response.json()
                    receipt = data.get("result")

                    if receipt and receipt != "null":
                        return self._process_receipt(receipt, target_amount, chain, symbol)
            except Exception as e:
                logger.warning(f"Explorer API failed for {chain}, trying RPC: {str(e)}")

        # Fallback to RPC
        return await self._verify_via_rpc(tx_hash, target_amount, chain, symbol)

    def _process_receipt(self, receipt: Dict[str, Any], target_amount: float, chain: str, symbol: str) -> Dict[str, Any]:
        """Common logic to parse receipt and apply tolerance."""
        if receipt.get("status") != "0x1":
            return {"status": "failed", "message": "Transaksi gagal di blockchain (Status 0x0)"}

        target_contract = self.usdc_contract if symbol.upper() == 'USDC' else self.usdt_contract
        transfer_event_sig = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
        
        actual_amount = 0
        for log in receipt.get("logs", []):
            if log["address"].lower() == target_contract.lower():
                topics = log.get("topics", [])
                if len(topics) >= 3 and topics[0].lower() == transfer_event_sig:
                    recipient = "0x" + topics[2][-40:].lower()
                    if recipient == self.my_wallet:
                        # Some APIs return data in 'data', others in 'value' (though proxy usually matches JSON-RPC logs)
                        amount_hex = log.get("data", "0x0")
                        actual_amount = int(amount_hex, 16) / 1_000_000
                        break

        if actual_amount == 0:
            return {"status": "failed", "message": f"Tidak ditemukan transfer {symbol} ke wallet kami."}

        # TOLERANCE LOGIC: ±0.05 USD
        diff = actual_amount - target_amount
        if diff < -0.05:
            return {
                "status": "failed", 
                "message": f"Jumlah {symbol} kurang. Diterima: {actual_amount:.2f}, Diharapkan: {target_amount:.2f} (Toleransi 0.05)"
            }
        
        return {
            "status": "success", 
            "message": "Pembayaran berhasil diverifikasi!",
            "amount_received": actual_amount,
            "chain": chain,
            "symbol": symbol
        }

    async def _verify_via_rpc(self, tx_hash: str, target_amount: float, chain: str, symbol: str) -> Dict[str, Any]:
        """RPC logic as robust fallback."""
        rpc_url = self.rpc_urls.get(chain.lower())
        if not rpc_url:
            return {"status": "error", "message": f"Blockchain {chain} tidak didukung (RPC missing)"}

        try:
            async with httpx.AsyncClient() as client:
                payload = {"jsonrpc": "2.0", "method": "eth_getTransactionReceipt", "params": [tx_hash], "id": 1}
                response = await client.post(rpc_url, json=payload, timeout=12.0)
                data = response.json()
                receipt = data.get("result")

                if not receipt:
                    return {"status": "pending", "message": "Transaksi belum ditemukan di blockchain (tunggu 1-2 menit)"}

                return self._process_receipt(receipt, target_amount, chain, symbol)
        except Exception as e:
            return {"status": "error", "message": f"Gagal menghubungi blockchain: {str(e)}"}

# Create singleton instance
validator = CryptoValidator()
