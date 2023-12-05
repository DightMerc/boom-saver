import os
import random
import time
import uuid
from typing import Dict

import instaloader
import requests
from instaloader import Instaloader, Post

from backends import SyncAbstractBackend, AbstractBackendResult
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


class SyncInstagramBackend(SyncAbstractBackend):

    BACKEND_URIS = ["instagram"]

    def __init__(self, link: str, path: str):
        self.link = link
        self.backend: Instaloader = Instaloader(
            rate_controller=lambda ctx: MyRateController(ctx)
        )
        self.path = path

    def _get_file(self, post) -> Dict:
        if post.is_video:
            response = requests.get(post.video_url)
            self.file_path = os.path.join(self.path, f"{str(uuid.uuid4())}.mp4")
            open(self.file_path, "wb").write(response.content)
            return dict(file_path=self.file_path)
        else:
            raise UnsupportedMediaType

    def _find_object(self) -> Post:
        try:
            post: Post = Post.from_shortcode(
                self.backend.context, self.link.split("/")[-2]
            )
            return post
        except Exception:
            raise ObjectNotFound

    def get(self) -> InstagramBackendResult:
        post: Post = self._find_object()
        downloaded: Dict = self._get_file(post=post)
        return InstagramBackendResult(
            link=self.link,
            file=downloaded["file_path"],
        )
