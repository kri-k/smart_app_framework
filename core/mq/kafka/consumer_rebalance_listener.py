from __future__ import annotations

from typing import TYPE_CHECKING

from aiokafka.abc import ConsumerRebalancelistener

if TYPE_CHECKING:
    from typing import Callable
    from kafka import TopicPartition
    from aiokafka import AIOKafkaConsumer


class CoreConsumerRebalancelistener(ConsumerRebalancelistener):
    def __init__(self, consumer: AIOKafkaConsumer,
                 on_assign_callback: Callable[[AIOKafkaConsumer, list[TopicPartition]], None]):
        self._consumer = consumer
        self._on_assign_callback = on_assign_callback

    def on_partitions_assigned(self, assigned: list[TopicPartition]):
        self._on_assign_callback(self._consumer, assigned)

    def on_partitions_revoked(self, revoked):
        pass
