from abc import ABC, abstractmethod


class AbstractBackendResult(ABC):
    pass


class SyncAbstractBackend(ABC):
    @abstractmethod
    def get(self) -> AbstractBackendResult:
        pass


class AsyncAbstractBackend(ABC):
    @abstractmethod
    async def get(self) -> AbstractBackendResult:
        pass
