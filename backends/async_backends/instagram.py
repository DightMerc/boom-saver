import os
import uuid
from typing import Dict, Callable

import httpx
from instaloader import Instaloader, Post

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
        self.backend: Instaloader = Instaloader()
        self.path = path

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
