from datetime import datetime
from starlette.types import Receive, Scope, Send
from fastapi import WebSocket


class CustomWebSocket(WebSocket):
    def __init__(self, scope: Scope, receive: Receive, send: Send):
        super().__init__(scope, receive, send)
        self.time_created = datetime.utcnow()
