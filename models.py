from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum, auto
from datetime import datetime

class UserState(Enum):
    WAIT_START = auto()
    WAIT_ACTION = auto()
    WAIT_PHOTO = auto()
    WAIT_MESSAGE = auto()
    WAIT_ADDRESS = auto()
    DONE = auto()

@dataclass
class UserData:
    photo_url: Optional[str] = None
    message: Optional[str] = None
    address: Optional[str] = None
    ticket_number: Optional[int] = None
    category: Optional[str] = None

class User:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.state = UserState.WAIT_START
        self.data = UserData()

    def update_state(self, new_state: UserState):
        self.state = new_state

    def update_data(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self.data, key):
                setattr(self.data, key, value)

    def reset(self):
        self.state = UserState.WAIT_START
        self.data = UserData()

@dataclass
class ReportData:
    ticket_number: int = None
    user_id: int = None
    photo_url: str = None
    photo_filename: str = None
    message: str = None
    address: str = None
    status: str = "новое"
    date: str = None
    category: str = None

    def __post_init__(self):
        if self.date is None:
            self.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

class Report:
    def __init__(self, user_id: int, data: dict = None):
        self.data = ReportData(user_id=user_id)
        if data:
            for key, value in data.items():
                if hasattr(self.data, key):
                    setattr(self.data, key, value)

    def to_dict(self) -> dict:
        return {k: v for k, v in self.data.__dict__.items() if v is not None} 