import os
import time
import traceback
import uuid
from typing import Dict, List

import httpx
import stem
from instaloader import Instaloader, Post
from redis import Redis
from stem import Signal
from stem.control import Controller

from backends import AbstractBackendResult, AsyncAbstractBackend
from backends.exceptions import ObjectNotFound, UnsupportedMediaType


class InstagramBackendResult(AbstractBackendResult):
    def __init__(self, link: str, file: str):
        self.link = link
        self.file = file


class AsyncInstagramBackend(AsyncAbstractBackend):

    BACKEND_URIS = ["instagram"]

    def __init__(self, link: str, path: str):
        self.link = link
        self.backend: Instaloader = Instaloader(
            sleep=True,
            download_geotags=False,
            download_comments=False,
            download_pictures=False,
            download_video_thumbnails=False,
            sanitize_paths=True,
            proxies=self._get_proxies(),
        )
        self.path = path

    def _get_proxies(self) -> List[Dict]:
        tor_host = os.environ["TOR_HOST"]
        control_port = stem.socket.ControlPort(tor_host, 9151)
        controller = Controller(control_port)
        controller.authenticate(password=os.environ["TOR_PASSWORD"])
        controller.signal(Signal.NEWNYM)
        print(
            f"TOR cport auth: {controller.is_authenticated()}. TOR NEW IDENTITY. Sleep 3 sec."
        )
        time.sleep(3)

        new_proxies = []
        for port in range(9050, 9062):
            proxy = {
                "http": f"socks4://{tor_host}:{port}",
                "https": f"socks4://{tor_host}:{port}",
            }
            new_proxies.append(proxy)
        return new_proxies

    async def _get_file(self, post) -> Dict:
        if post.is_video:
            async with httpx.AsyncClient() as client:
                response = await client.get(post.video_url)
                self.file_path = os.path.join(self.path, f"{str(uuid.uuid4())}.mp4")
                open(self.file_path, "wb").write(response.content)
                return dict(file_path=self.file_path)
        else:
            raise UnsupportedMediaType

    async def _find_object(self) -> Post:
        try:
            post: Post = Post.from_shortcode(
                self.backend.context, self.link.split("/")[-2]
            )
            return post
        except Exception:
            traceback.print_exc()
            raise ObjectNotFound

    async def get(self) -> InstagramBackendResult:
        post: Post = await self._find_object()
        downloaded: Dict = await self._get_file(post=post)
        return InstagramBackendResult(
            link=self.link,
            file=downloaded["file_path"],
        )
