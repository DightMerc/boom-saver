import os
import uuid
from typing import Dict

import requests
from instaloader import Instaloader, Post

from backends import SyncAbstractBackend, AbstractBackendResult
from backends.exceptions import ObjectNotFound, UnsupportedMediaType


class InstagramBackendResult(AbstractBackendResult):
    def __init__(self, link: str, file: str):
        self.link = link
        self.file = file


class SyncInstagramBackend(SyncAbstractBackend):

    BACKEND_URIS = ["instagram"]

    def __init__(self, link: str, path: str):
        self.link = link
        self.backend: Instaloader = Instaloader()
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
