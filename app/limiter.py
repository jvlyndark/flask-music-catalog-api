from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# In-memory storage is per-process only, so each gunicorn worker tracks limits
# independently. A real deployment would use Redis as the storage backend so
# limits are shared across all workers and instances.
limiter = Limiter(key_func=get_remote_address)
