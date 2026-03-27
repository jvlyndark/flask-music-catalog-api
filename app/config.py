import os


class Config:
    # All configuration is pulled from the environment so the same image can
    # run in dev, staging, and production without code changes.
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/musiccatalog")
    TESTING = False


class TestingConfig(Config):
    TESTING = True
    # Tests point at a separate database so they never touch seeded data.
    MONGO_URI = os.environ.get("MONGO_URI_TEST", "mongodb://localhost:27017/musiccatalog_test")


config_map = {
    "development": Config,
    "testing": TestingConfig,
    "production": Config,
}
