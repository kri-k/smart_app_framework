import unittest
from unittest.mock import AsyncMock, Mock

from aiokafka import TopicPartition
from aiokafka.errors import KafkaError

from core.mq.kafka.kafka_consumer import KafkaConsumer


class TestKafkaConsumerErrors(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.consumer = KafkaConsumer.__new__(KafkaConsumer)
        self.consumer._consumer = Mock()
        self.consumer._error_callback = Mock()

    def test_subscribe_handles_aiokafka_error(self):
        error = KafkaError("subscription failed")
        self.consumer._consumer.subscribe.side_effect = error

        self.consumer.subscribe(["test-topic"])

        self.consumer._error_callback.assert_called_once_with(error)

    async def test_commit_handles_aiokafka_error(self):
        error = KafkaError("commit failed")
        self.consumer.autocommit_enabled = False
        self.consumer._consumer.commit = AsyncMock(side_effect=error)
        message = Mock(topic="test-topic", partition=1, offset=42)

        await self.consumer.commit_offset(message)

        self.consumer._consumer.commit.assert_awaited_once_with({TopicPartition("test-topic", 1): 43})
        self.consumer._error_callback.assert_called_once_with(error)
