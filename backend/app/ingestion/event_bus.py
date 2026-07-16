"""
Ingestion event bus.

Production mode: publishes/consumes real Kafka topics (KAFKA_BOOTSTRAP_SERVERS)
so that each data source (news, AIS, sanctions, prices) can run as an
independent producer service and the Orchestrator consumes off a single
`sentinel.raw-events` topic — this is the pattern you'd run at real scale
with multiple ingestion workers across a cluster.

Local/offline fallback: an in-process asyncio.Queue standing in for the topic,
so the full pipeline (ingest -> orchestrate -> agents -> websocket) still runs
end-to-end without a Kafka cluster available. Same publish()/consume() interface
either way.
"""
import os
import json
import logging
import asyncio

logger = logging.getLogger("sentinel.ingestion.bus")

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
RAW_EVENTS_TOPIC = "sentinel.raw-events"

_mode = "memory"
_producer = None
_local_queue: "asyncio.Queue" = asyncio.Queue()

if KAFKA_BOOTSTRAP_SERVERS:
    try:
        from aiokafka import AIOKafkaProducer  # noqa: F401
        _mode = "kafka"
        logger.info("Ingestion bus configured for KAFKA at %s", KAFKA_BOOTSTRAP_SERVERS)
    except ImportError:
        logger.warning("aiokafka not installed; falling back to in-process queue.")
        _mode = "memory"
else:
    logger.info("KAFKA_BOOTSTRAP_SERVERS not set; ingestion bus running in-process.")


async def _get_kafka_producer():
    global _producer
    from aiokafka import AIOKafkaProducer
    if _producer is None:
        _producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
        await _producer.start()
    return _producer


async def publish_event(event: dict):
    """Publish a normalized event dict onto the bus (real Kafka topic, or local queue)."""
    if _mode == "kafka":
        producer = await _get_kafka_producer()
        await producer.send_and_wait(RAW_EVENTS_TOPIC, json.dumps(event).encode("utf-8"))
    else:
        await _local_queue.put(event)
    logger.info("Published event %s (%s) to bus [%s]", event.get("id"), event.get("event_type"), _mode)


async def consume_events(handler):
    """
    Long-running consumer loop. `handler` is an async callable(event: dict).
    In Kafka mode this subscribes to RAW_EVENTS_TOPIC; in memory mode it
    drains the local asyncio.Queue. Intended to be launched as a background
    task at app startup (see app/main.py).
    """
    if _mode == "kafka":
        from aiokafka import AIOKafkaConsumer
        consumer = AIOKafkaConsumer(
            RAW_EVENTS_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id="sentinel-orchestrator",
        )
        await consumer.start()
        try:
            async for msg in consumer:
                event = json.loads(msg.value.decode("utf-8"))
                await handler(event)
        finally:
            await consumer.stop()
    else:
        while True:
            event = await _local_queue.get()
            await handler(event)
