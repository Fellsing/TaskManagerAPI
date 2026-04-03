import redis
import os

REDIS_HOST = os.getenv("REDIS_URL", "redis")

try:
    redis_client = redis.Redis(host=REDIS_HOST, port=6379, db=0, decode_responses=True, socket_connect_timeout=2)
    redis_client.ping()
    print("Redis successfully working!")
except redis.ConnectionError:
    print("Cannot connect to Redis, Plase, check your docker-compose services settings.")


def get_redis():
    return redis_client