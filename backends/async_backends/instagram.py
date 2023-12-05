import json
import os
import random
import time
import uuid
from typing import Dict

from redis import Redis

import httpx
import instaloader
import orjson
from instaloader import Instaloader, Post
from requests_tor import RequestsTor

from backends import AbstractBackendResult, AsyncAbstractBackend
from backends.exceptions import ObjectNotFound, UnsupportedMediaType


class InstagramBackendResult(AbstractBackendResult):
    def __init__(self, link: str, file: str):
        self.link = link
        self.file = file


class MyRateController(instaloader.RateController):
    def sleep(self, secs: float):
        time_to_sleep = random.randint(1, 3)
        print(f"Time to sleep: {time_to_sleep}")
        time.sleep(time_to_sleep)

    def count_per_sliding_window(self, query_type):
        return 20


class AsyncInstagramBackend(AsyncAbstractBackend):

    BACKEND_URIS = ["instagram"]

    def __init__(self, link: str, path: str):
        self.link = link
        self.redis = Redis(
            host=os.environ["REDIS_HOST"],
            port=int(os.environ["REDIS_PORT"]),
            db=int(os.environ["REDIS_DB"]),
        )
        self.backend: Instaloader = Instaloader(
            sleep=True,
            rate_controller=lambda ctx: MyRateController(ctx),
            download_geotags=False,
            download_comments=False,
            download_pictures=False,
            download_video_thumbnails=False,
            sanitize_paths=True,
            proxies=self._get_proxies(),
        )
        self.path = path

    def _get_proxies(self) -> Dict:
        proxies = self.redis.get("proxies")
        if not proxies:
            new_proxies = {}
            for port in range(9050, 9062):
                active = True
                if port == 9050:
                    active = False
                new_proxies[f"{port}"] = dict(active=active)

            self.redis.set("proxies", json.dumps(new_proxies))
            return {"https": f"socks4://localhost:9050"}
        else:
            ports: Dict = json.loads(proxies.decode("ascii"))
            for port in ports:
                if ports[port]["active"]:
                    ports[port]["active"] = False
                    self.redis.set("proxies", json.dumps(ports))
                    return {"https": f"socks4://localhost:{port}"}
            requestor = RequestsTor(tor_ports=(9050,), tor_cport=9051)
            requestor.new_id()
            new_proxies = {}
            for port in range(9050, 9062):
                active = True
                if port == 9050:
                    active = False
                new_proxies[f"{port}"] = dict(active=active)

            self.redis.set("proxies", json.dumps(new_proxies))
            return {"https": f"socks4://localhost:9050"}

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
            raise ObjectNotFound

    async def get(self) -> InstagramBackendResult:
        post: Post = await self._find_object()
        downloaded: Dict = await self._get_file(post=post)
        return InstagramBackendResult(
            link=self.link,
            file=downloaded["file_path"],
        )
