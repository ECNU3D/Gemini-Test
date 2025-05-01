import os
import time
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv() # Ensure environment variables are loaded

# Configuration
API_KEY_EXPIRY_MINUTES = 30

class ApiKeyManager:
    def __init__(self, expiry_minutes=API_KEY_EXPIRY_MINUTES):
        self._api_key = None
        self._last_fetch_time = None
        self._expiry_duration = timedelta(minutes=expiry_minutes)
        self._lock = asyncio.Lock() # Lock for async safety

    def _get_key_from_env(self):
        """Fetches the key from environment or generates a time-stamped dummy key."""
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            # Generate a dummy key that changes to show refresh visually
            key = f"dummy-key-{datetime.now().strftime('%H%M%S')}"
            # print(f"[Auth] Using time-stamped dummy API key: {key}") # Optional: for debugging
        # else:
            # print("[Auth] Using API key from environment.") # Optional: for debugging
        return key

    def _is_expired(self):
        """Checks if the current key is expired or not set."""
        if self._api_key is None or self._last_fetch_time is None:
            return True
        return datetime.now() > self._last_fetch_time + self._expiry_duration

    def get_key_sync(self):
        """Synchronous version to get the potentially refreshed API key."""
        # Basic check without lock first for performance
        if not self._is_expired():
            return self._api_key

        # If potentially expired, acquire lock equivalent (not strictly needed in sync, but maintains pattern)
        # In a real threaded scenario, a threading.Lock would be needed here.
        # For this simulation, simple check is sufficient.
        if self._is_expired():
            print("[Auth] API key expired or not set, refreshing...")
            self._api_key = self._get_key_from_env()
            self._last_fetch_time = datetime.now()
            print(f"[Auth] Refreshed API key at {self._last_fetch_time.strftime('%Y-%m-%d %H:%M:%S')}")
        return self._api_key

    async def get_key_async(self):
        """Asynchronous version to get the potentially refreshed API key."""
        # Basic check without lock first for performance
        if not self._is_expired():
            return self._api_key

        # If potentially expired, acquire lock to prevent race conditions during refresh
        async with self._lock:
            # Double check expiry after acquiring lock
            if self._is_expired():
                print("[Auth] API key expired or not set, refreshing (async)...")
                self._api_key = self._get_key_from_env()
                self._last_fetch_time = datetime.now()
                print(f"[Auth] Refreshed API key at {self._last_fetch_time.strftime('%Y-%m-%d %H:%M:%S')} (async)")
        return self._api_key

# Global instance
_key_manager = ApiKeyManager()

# Public functions
def get_api_key():
    """Gets the current (potentially refreshed) API key."""
    return _key_manager.get_key_sync()

async def get_api_key_async():
    """Gets the current (potentially refreshed) API key asynchronously."""
    return await _key_manager.get_key_async()

# Example usage (for testing the module directly)
if __name__ == "__main__":
    print("--- Sync Test ---")
    key1 = get_api_key()
    print(f"Initial Key: {key1}")
    time.sleep(2)
    key2 = get_api_key()
    print(f"Second Key (should be same): {key2}")
    assert key1 == key2

    # Simulate time passing
    print("Simulating expiry...")
    _key_manager._last_fetch_time = datetime.now() - timedelta(minutes=API_KEY_EXPIRY_MINUTES + 1)
    key3 = get_api_key()
    print(f"Third Key (should be new): {key3}")
    assert key1 != key3 # This might fail if the actual env key doesn't change

    print("--- Async Test ---")
    async def run_async_test():
        akey1 = await get_api_key_async()
        print(f"Initial Async Key: {akey1}")
        await asyncio.sleep(1)
        akey2 = await get_api_key_async()
        print(f"Second Async Key (should be same): {akey2}")
        assert akey1 == akey2

        print("Simulating async expiry...")
        _key_manager._last_fetch_time = datetime.now() - timedelta(minutes=API_KEY_EXPIRY_MINUTES + 1)

        tasks = [get_api_key_async() for _ in range(3)]
        results = await asyncio.gather(*tasks)
        print(f"Concurrent Async Keys (should be same new key): {results}")
        assert len(set(results)) == 1 # All should get the same refreshed key
        assert akey1 != results[0] # Should be different from the original key

    asyncio.run(run_async_test()) 