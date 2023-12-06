import os
import time
import traceback
import uuid
from sys import stderr
from typing import Dict, List

import httpx
import stem
from instaloader import Instaloader, Post
from stem import Signal
from stem.control import Controller

from backends import AbstractBackendResult, AsyncAbstractBackend
from backends.exceptions import ObjectNotFound, UnsupportedMediaType

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC


class InstagramBackendResult(AbstractBackendResult):
    def __init__(self, link: str, file: str):
        self.link = link
        self.file = file


class AsyncInstagramBackend(AsyncAbstractBackend):

    BACKEND_URIS = ["instagram"]

    def __init__(self, link: str, path: str):
        self.link = link
        self.path = path

    async def _get_file(self, post) -> Dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(post)
            self.file_path = os.path.join(self.path, f"{str(uuid.uuid4())}.mp4")
            open(self.file_path, "wb").write(response.content)
            return dict(file_path=self.file_path)

    async def _find_object(self) -> str:
        try:
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()), options=options
            )

            url = "https://www.instagram.com/reel/C0ZZ5NPIXqR/?igshid=MzRlODBiNWFlZA%3D%3D"

            driver.get(url)
            try:
                video: WebElement = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "video"))
                )
                url = video.get_property("src")
            finally:
                driver.quit()
            return url

        except Exception:
            traceback.print_exc()
            raise ObjectNotFound

    async def get(self) -> InstagramBackendResult:
        post: str = await self._find_object()
        downloaded: Dict = await self._get_file(post=post)
        return InstagramBackendResult(
            link=self.link,
            file=downloaded["file_path"],
        )
