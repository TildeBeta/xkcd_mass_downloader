import asyncio
import os

import aiohttp


class Downloader:
    def __init__(self, directory='xkcd', *, loop=None):
        if not os.path.exists(directory):
            raise SystemExit('No such directory: {}'.format(directory))
        if not os.access(directory, os.W_OK):
            raise SystemExit('Directory {}: permission denied.'
                             .format(directory))
        self.directory = directory
        self.loop = loop if loop is not None else asyncio.get_event_loop()
        self.session = aiohttp.ClientSession(loop=self.loop)

    def __del__(self):
        self.session.close()

    async def get_json(self, num):
        if num < 0:
            return

        if num == 0:
            url = 'http://xkcd.com/info.0.json'
        else:
            url = 'http://xkcd.com/{}/info.0.json'.format(num)

        try:
            async with self.session.get(url) as resp:
                return await resp.json()
        except Exception as e:
            print('Unexpected error: {}: {}'.format(type(e).__name__, str(e)))

    async def download(self, num):
        # xkcd 404 doesn't exist, goes to 404 page
        if num == 404:
            return

        metadata = await self.get_json(num)

        if not metadata:
            print('???')

        img = metadata['img']
        ext = img.rsplit('.', 1)[1]
        known_extensions = ['png', 'jpg', 'jpeg', 'gif']

        if ext not in known_extensions:
            print('Unexpected extension: {} (comic num. {})'.format(ext, num))
            return

        async with self.session.get(img) as resp:
            with open('{}/{}.{}'.format(self.directory, num, ext), 'wb') as f:
                f.write(await resp.read())

    async def download_all(self):
        latest = await self.get_json(0)

        futures = []

        for i in range(1, latest['num'] + 1):
            futures.append(self.download(i))

        await asyncio.gather(*futures)


if __name__ == '__main__':
    downloader = Downloader()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(downloader.download_all())
