from abc import ABC, abstractmethod
from datetime import date


class Event:

    def __init__(self, date: date, payload: dict, event_type: str):

        self.date = date
        self.payload = payload
        self.event_type = event_type


class Scheduler(ABC):

    @abstractmethod
    def generate(self, start: date, end: date) -> list[Event]:
        pass