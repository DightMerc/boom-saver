import os
from typing import Callable

from backends.async_backends.instagram import AsyncInstagramBackend
from backends.async_backends.yandex_music import AsyncYandexMusicBackend
from backends.async_backends.youtube import AsyncYoutubeBackend
from backends.exceptions import UnsupportedLinkOrigin
from backends.logs import logger

ASYNC_BACKENDS = [AsyncYandexMusicBackend, AsyncYoutubeBackend, AsyncInstagramBackend]


class AsyncBackendSelector:
    def __init__(self, link: str, path: str = os.environ["TEMP_DIR"]):
        self.link = link
        self.path = path

    @property
    async def backend(self):
        for backend in ASYNC_BACKENDS:
            for link_template in backend.BACKEND_URIS:
                if link_template in self.link:
                    logger.info(f"{backend.__name__} selected - {self.link}")
                    return backend(
                        link=self.link,
                        path=self.path,
                    )
        raise UnsupportedLinkOrigin
