import os


class Settings:
    RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    EMBEDDING_RESULT_TTL = int(os.getenv("EMBEDDING_RESULT_TTL", 86400))
    EMBEDDING_COMPLETE_EXCHANGE = os.getenv("FIXR_RABBITMQ_EXCHANGE", "fixr.exchange")
    RABBITMQ_QUEUE = os.getenv("FIXR_RABBITMQ_REQUEST_QUEUE", "embedding.request")
    EMBEDDING_COMPLETED_BINDING = os.getenv(
        "FIXR_RABBITMQ_COMPLETED_ROUTING_KEY", "embedding.completed"
    )
    EMBEDDING_FAILED_BINDING = os.getenv(
        "FIXR_RABBITMQ_REQUEST_FAILED_ROUTING_KEY", "embedding.failed"
    )
    DUPLICATE_SEARCH_RADIUS_METERS = float(
        os.getenv("DUPLICATE_SEARCH_RADIUS_METERS", "50")
    )
    DUPLICATE_CANDIDATE_LIMIT = int(os.getenv("DUPLICATE_CANDIDATE_LIMIT", "5"))

    DISTANCE_SIMILARITY_SCORE_WEIGHT=float(os.getenv("DISTANCE_SIMILARITY_SCORE_WEIGHT", "0.4"))
    VISUAL_SIMILARITY_SCORE_WEIGHT=float(os.getenv("VISUAL_SIMILARITY_SCORE_WEIGHT", "0.6"))
    EXPONENTIAL_DECAY_RATE=float(os.getenv("EXPONENTIAL_DECAY_RATE", "89"))


settings = Settings()
