class SocketMessage:
    def __init__(self, sender_addr, event, payload):
        self.sender_addr = sender_addr
        self.event = event
        self.payload = payload

