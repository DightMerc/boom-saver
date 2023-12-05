from backends import AbstractBackendResult


class SyncSaverBackend:
    def __init__(self, backend):
        self.backend = backend

    def get(self) -> AbstractBackendResult:
        return self.backend.get()
