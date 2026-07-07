"""
# Описание моделей для StaticStorage.
"""
from typing import Optional

from pydantic import BaseModel, Field

from .response import AssistantResponsePayload


class AssistantAnswer(AssistantResponsePayload):
    """
    # Описание модели AssistantAnswer.
    """

    answers: Optional[list[AssistantResponsePayload]]
    """Список ответов."""


class StaticStorageItem(AssistantResponsePayload):
    """
    # Описание модели StaticStorageItem.
    """

    joy: Optional[AssistantAnswer] = Field(default=None)
    """Ответы Джой."""
    sber: Optional[AssistantAnswer] = Field(default=None)
    """Ответы Сбера."""
    athena: Optional[AssistantAnswer] = Field(default=None)
    """Ответы Афины."""
    any: Optional[AssistantAnswer] = Field(default=None)
    """Дефолтные ответы."""


class StaticStorage(BaseModel):
    """
    # Описание модели StaticStorage.
    """

    data: dict[str, StaticStorageItem] = Field(default_factory=dict)
    """Словарь ответов ассистентов."""
