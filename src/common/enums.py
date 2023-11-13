from enum import Enum


class State(str, Enum):
    PUBLISHED = "PUBLISHED"
    RECEIVED = "RECEIVED"
    CONSUMED = "CONSUMED"
