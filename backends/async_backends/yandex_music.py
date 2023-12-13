import os
import traceback
import urllib
from typing import Dict, List, Callable
from urllib.parse import urlencode, urlparse, urlunparse, parse_qs

import mutagen
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3NoHeaderError, APIC, ID3
from yandex_music import Client, Track, DownloadInfo

from backends import AbstractBackendResult, AsyncAbstractBackend
from backends.exceptions import ObjectNotFound


class YandexMusicBackendResult(AbstractBackendResult):
    def __init__(self, link: str, file: str, title: str, track: Track):
        self.link = link
        self.file = file
        self.title = title
        self.track = track


class AsyncYandexMusicBackend(AsyncAbstractBackend):

    BACKEND_URIS = ["yandex"]

    def __init__(self, link: str, path: str):
        self.link = link
        self.token = os.environ.get("YANDEX_MUSIC_TOKEN")
        self.backend: Client = Client(token=self.token).init()
        self.path = path

    async def _get_file(self, track: Track) -> Dict:
        title = track.title
        artist = (
            str([artist["name"] for artist in track.artists])
            .replace("[", "")
            .replace("]", "")
            .replace("'", "")
        )
        self.file_path = os.path.join(self.path, f"{artist} - {title}.mp3")
        max_bitrate = self._get_max_bitrate()
        track.download(filename=self.file_path, bitrate_in_kbps=max_bitrate)
        await self._add_id3_tags(track=track)
        return dict(file_path=self.file_path, title=title, track=track)

    async def _add_id3_tags(self, track: Track):
        try:
            meta = EasyID3(self.file_path)
        except ID3NoHeaderError:
            meta: mutagen.File = mutagen.File(self.file_path, easy=True)
            meta.add_tags()
        meta["title"] = track.title
        meta["artist"] = (
            str([artist["name"] for artist in track.artists])
            .replace("[", "")
            .replace("]", "")
            .replace("'", "")
        )
        meta["album"] = (
            str([album["title"] for album in track.albums])
            .replace("[", "")
            .replace("]", "")
            .replace("'", "")
        )
        meta.save(self.file_path, v1=2)

        meta_pic = ID3(self.file_path)
        picture = track.download_cover_bytes()
        meta_pic["APIC"] = APIC(
            encoding=3, mime="image/jpeg", type=3, desc="Front cover", data=picture
        )
        meta_pic.save()

    def _get_max_bitrate(self) -> int:
        codecs: List[DownloadInfo] = self.backend.tracks_download_info(self.track_id)
        max_bitrate = 0
        for codec in codecs:
            if codec["bitrate_in_kbps"] > max_bitrate:
                max_bitrate = codec["bitrate_in_kbps"]
        return max_bitrate

    async def _find_object(self) -> Track:
        try:
            url = urlparse(self.link)
            self.track_id = int(os.path.split(url.path)[1])
            return self.backend.tracks([self.track_id])[0]
        except Exception:
            traceback.print_exc()
            raise ObjectNotFound

    async def get(self) -> YandexMusicBackendResult:
        track: Track = await self._find_object()
        downloaded: Dict = await self._get_file(track=track)
        return YandexMusicBackendResult(
            link=self.link,
            file=downloaded["file_path"],
            title=downloaded["title"],
            track=track,
        )

    async def get_link(self) -> str:
        track: Track = await self._find_object()
        infos: List[DownloadInfo] = track.get_download_info()
        max_bitrate = 0
        best = None
        for info in enumerate(infos):
            if info[1]["bitrate_in_kbps"] > max_bitrate:
                max_bitrate = info[1]["bitrate_in_kbps"]
                best = info[1]
        return best.get_direct_link()
