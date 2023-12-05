from backends import AbstractBackendResult


class AsyncSaverBackend:
    def __init__(self, backend):
        self.backend = backend

    async def get(self) -> AbstractBackendResult:
        return await self.backend.get()
