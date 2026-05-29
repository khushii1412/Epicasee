import time
import os
import json

# Simple in-memory cache dictionary
# Structure: { cache_key: { "data": value, "expires_at": timestamp } }
_cache = {}

# Disk cache directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(BASE_DIR, "data_processed", ".cache_persistent")

def _get_safe_filename(cache_key):
    import hashlib
    h = hashlib.md5(cache_key.encode('utf-8')).hexdigest()
    # Clean cache_key for safe readability in file explorer
    clean_prefix = "".join([c if c.isalnum() or c in ("-", "_") else "_" for c in cache_key[:30]])
    return f"{clean_prefix}_{h}.json"

def get_cached_or_compute(cache_key, compute_fn, ttl_seconds=600):
    """
    Returns cached value from memory or disk if exists and not expired,
    otherwise computes, stores in memory, and persists to disk.
    """
    now = time.time()
    
    # 1. Check in-memory cache
    if cache_key in _cache:
        entry = _cache[cache_key]
        if now < entry["expires_at"]:
            return entry["data"]
            
    # 2. Check disk cache
    os.makedirs(CACHE_DIR, exist_ok=True)
    filename = _get_safe_filename(cache_key)
    filepath = os.path.join(CACHE_DIR, filename)
    
    if os.path.exists(filepath):
        try:
            mtime = os.path.getmtime(filepath)
            # Check if file has expired
            if now - mtime < ttl_seconds:
                with open(filepath, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                # Populate in-memory cache
                _cache[cache_key] = {
                    "data": cached_data,
                    "expires_at": mtime + ttl_seconds
                }
                return cached_data
        except Exception as e:
            # If reading from disk failed, fallback to computing
            print(f"[CACHE WARNING] Failed to read disk cache for {cache_key}: {e}")
            
    # 3. Compute the new value
    computed_data = compute_fn()
    
    # 4. Store in-memory cache
    _cache[cache_key] = {
        "data": computed_data,
        "expires_at": now + ttl_seconds
    }
    
    # 5. Persist to disk cache
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(computed_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[CACHE WARNING] Failed to write disk cache for {cache_key}: {e}")
        
    return computed_data

