"""The model call: request building, the Bedrock client wrapper and recorded fixtures."""


class ModelError(Exception):
    """A failed model call; `code` is one of `demotrace_shared.errors.ErrorCode`."""

    def __init__(self, code, detail: str = "", request_id: str | None = None):
        super().__init__(f"{code}: {detail}" if detail else str(code))
        self.code = code
        self.detail = detail
        self.request_id = request_id
