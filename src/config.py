import os
class Settings:
    RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

    # Fixr exchange will have 2 exchanges binded to it namely fixr.embedding.requested and fixr.embedding.completed
    # Core application publishes embedding tasks to embedding.requested
    # Core application receieves notifications on embedding.completed
    EMBEDDING_COMPLETE_EXCHANGE = os.getenv("EMBEDDING_COMPLETED_QUEUE", "fixr.exchange")
    RABBITMQ_QUEUE = os.getenv("FIXR_RABBITMQ_REQUEST_QUEUE", "embedding.request")
    EMBEDDING_COMPLETED_BINDING=os.getenv("FIXR_RABBITMQ_COMPLETED_ROUTING_KEY", "embedding.completed")
    EMBEDDING_FAILED_BINDING=os.getenv("FIXR_RABBITMQ_REQUEST_FAILED_ROUTING_KEY", "embedding.failed")
    EMBEDDING_RESULT_TTL = int(os.getenv("EMBEDDING_RESULT_TTL", 86400))
settings = Settings()

