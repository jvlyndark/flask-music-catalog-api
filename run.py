import os
from app import create_app

env = os.environ.get("FLASK_ENV", "development")
app = create_app(env)

if __name__ == "__main__":
    # This entry point is for local dev only. The container uses gunicorn.
    app.run(host="0.0.0.0", port=8000, debug=(env == "development"))
