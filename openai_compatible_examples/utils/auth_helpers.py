import os
import time
import asyncio
import subprocess
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
        """Fetches the access token using gcloud command."""
        try:
            # Use shell=True on Windows if 'gcloud' is in PATH but not directly executable
            # For better cross-platform compatibility, avoid shell=True if possible
            # If gcloud is guaranteed to be in PATH, shell=False is safer.
            # Using shell=True for broader compatibility for now.
            result = subprocess.run(
                "gcloud auth print-access-token",
                capture_output=True,
                text=True,
                check=True,
                shell=True # Using shell=True for compatibility, consider security implications
            )
            key = result.stdout.strip()
            print("[Auth] Successfully fetched access token using gcloud.")
            print(f"[Auth] Fetched key: {key}")
            return key
        except FileNotFoundError:
            print("[Auth] Error: 'gcloud' command not found. Make sure Google Cloud SDK is installed and in PATH.")
            return None # Indicate failure to fetch key
        except subprocess.CalledProcessError as e:
            print(f"[Auth] Error executing gcloud command: {e}")
            print(f"[Auth] Stderr: {e.stderr.strip()}")
            return None # Indicate failure to fetch key
        except Exception as e:
            print(f"[Auth] An unexpected error occurred while fetching gcloud token: {e}")
            return None

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
            new_key = self._get_key_from_env()
            if new_key: # Only update if fetch was successful
                self._api_key = new_key
                self._last_fetch_time = datetime.now()
                print(f"[Auth] Refreshed API key at {self._last_fetch_time.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                print("[Auth] Failed to refresh API key.")
                # Decide how to handle failure: keep stale key? set to None?
                # For now, it keeps the potentially stale key or None if never set.
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
                # Note: _get_key_from_env uses subprocess.run, which is blocking.
                # In a high-concurrency async scenario, consider using asyncio.subprocess
                # for a truly non-blocking call. For infrequent token refreshes,
                # this might be acceptable.
                new_key = self._get_key_from_env()
                if new_key: # Only update if fetch was successful
                    self._api_key = new_key
                    self._last_fetch_time = datetime.now()
                    print(f"[Auth] Refreshed API key at {self._last_fetch_time.strftime('%Y-%m-%d %H:%M:%S')} (async)")
                else:
                    print("[Auth] Failed to refresh API key (async).")
                    # Decide how to handle failure: keep stale key? set to None?
                    # For now, it keeps the potentially stale key or None if never set.
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
    # assert key1 == key2 # Assertion might be flaky if token changes rapidly or errors occur

    # Simulate time passing
    print("Simulating expiry...")
    _key_manager._last_fetch_time = datetime.now() - timedelta(minutes=API_KEY_EXPIRY_MINUTES + 1)
    key3 = get_api_key()
    print(f"Third Key (should be new if refresh succeeded): {key3}")
    # assert key1 != key3 # Assertion depends on successful refresh and token change

    print("--- Async Test ---")
    async def run_async_test():
        akey1 = await get_api_key_async()
        print(f"Initial Async Key: {akey1}")
        await asyncio.sleep(1)
        akey2 = await get_api_key_async()
        print(f"Second Async Key (should be same): {akey2}")
        # assert akey1 == akey2 # Assertion might be flaky

        print("Simulating async expiry...")
        _key_manager._last_fetch_time = datetime.now() - timedelta(minutes=API_KEY_EXPIRY_MINUTES + 1)

        tasks = [get_api_key_async() for _ in range(3)]
        results = await asyncio.gather(*tasks)
        print(f"Concurrent Async Keys (should be same new key if refresh succeeded): {results}")
        # assert len(set(results)) == 1 # All should get the same refreshed key if successful
        # assert akey1 != results[0] # Assertion depends on successful refresh and token change

    asyncio.run(run_async_test()) 