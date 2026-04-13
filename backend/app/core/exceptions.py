class UpstreamServiceError(Exception):
    def __init__(self, service: str, message: str) -> None:
        self.service = service
        self.message = message
        super().__init__(f"{service}: {message}")
