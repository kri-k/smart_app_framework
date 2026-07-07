"""
Описание функциональности устройства.
"""
from typing import Optional, Union
from pydantic import BaseModel, Field

from nlpf_statemachine.models.enums import DeviceFeaturesAppTypes


class DeviceFeatures(BaseModel):
    """
    # Описание модели DeviceFeatures.
    """

    appTypes: Optional[list[Union[DeviceFeaturesAppTypes, str]]] = Field(default=None)
    """
    Типы смартапов, которые поддерживает устройство.

    Возможные значения:

    * DIALOG;
    * WEB_APP;
    * APK;
    * CHAT_APP.
    * EMBEDDED_APP
    * ...
    """
    clientFlags: Optional[dict] = Field(default={})
    """Описание клиентских флагов"""
