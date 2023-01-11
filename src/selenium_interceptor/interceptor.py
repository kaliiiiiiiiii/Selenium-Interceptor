import time


class cdp_listener(object):
    from typing import Dict

    def __init__(self, driver):
        self.listener = {}
        self.driver = driver
        self.my_headers = None
        self.thread = None
        self.has_started = None

    async def async_helper(self):
        async with self.driver.bidi_connection() as connection:
            session, devtools = connection.session, connection.devtools

            my_listener = await self.listener["listener"](connection=connection)
            async for event in my_listener:
                try:
                    await session.execute(await self.listener["at_event"](event=event, connection=connection))
                except Exception as e:
                    if -32602 in e.__dict__.values():
                        print(e)  # 'Invalid InterceptionId.'
                    else:
                        raise e

    def trio_helper(self):
        import trio
        self.has_started = True
        trio.run(self.async_helper)

    def start_threaded(self, listener: Dict[str, callable] = {}):
        if listener:
            self.listener = listener

        import threading
        thread = threading.Thread(target=self.trio_helper)
        self.thread = thread
        thread.start()

        while True:
            time.sleep(0.1)
            if self.has_started:
                break

        return thread

    def connection_refused(self, event, connection):
        self.print_event(event)

        session, devtools = connection.session, connection.devtools
        # show_image(event.request.url)
        return devtools.fetch.fail_request(request_id=event.request_id,
                                           error_reason=devtools.network.ErrorReason.CONNECTION_REFUSED)

    async def get_response_body(self, connection, request_id):
        session, devtools = connection.session, connection.devtools
        await session.execute(devtools.fetch.get_response_body(request_id))

    async def modify_headers(self, event, connection):
        self.print_event(event)

        session, devtools = connection.session, connection.devtools

        headers = event.request.headers.to_json()

        try:
            headers.update(self.my_headers)
        except TypeError as e:
            print(e)
            raise TypeError("Define headers using cdp_listener.specify_headers.\n")
        my_headers = []
        for item in headers.items():
            my_headers.append(devtools.fetch.HeaderEntry.from_json({"name": item[0], "value": item[1]}))

        return devtools.fetch.continue_request(request_id=event.request_id, headers=my_headers)

    def specify_headers(self, headers: Dict[str, str]):
        self.my_headers = headers

    def decode_body(body: str, response, encoding="utf-8"):
        import base64
        import json
        if body:
            decoded = base64.b64decode(body).decode(encoding=encoding, errors="replace")
            rep_type = response.resource_type.name
            if rep_type == "XHR":
                try:
                    decoded = json.loads(decoded)
                except Exception as e:
                    print(e)
            return decoded
        else:
            return body

    def encode_body(decoded: str or dict, encoding="utf-8"):
        import base64
        import json
        if decoded:
            if not type(decoded) is str:
                decoded = json.dumps(decoded)
            encoded = base64.b64encode(decoded.encode(encoding=encoding, errors="replace")).decode(encoding=encoding)
            return encoded
        else:
            return decoded

    async def all_images(self, connection):
        session, devtools = connection.session, connection.devtools
        pattern = map(devtools.fetch.RequestPattern.from_json, [{"resourceType": "Image"}])
        pattern = list(pattern)
        await session.execute(devtools.fetch.enable(patterns=pattern))

        return session.listen(devtools.fetch.RequestPaused)

    async def all_requests(self, connection):
        session, devtools = connection.session, connection.devtools
        pattern = map(devtools.fetch.RequestPattern.from_json, [{"urlPattern": "*"}])
        pattern = list(pattern)
        await session.execute(devtools.fetch.enable(patterns=pattern))

        return session.listen(devtools.fetch.RequestPaused)

    def show_image(self, url: str):  # show image from URL
        from PIL import Image
        from io import BytesIO
        import requests
        try:
            response = requests.get(url)
            img = Image.open(BytesIO(response.content))
            img.show()
        except Exception as e:
            print(e)

    def print_event(self, event):
        print({"type": event.resource_type.to_json(), "frame_id": event.frame_id, "url": event.request.url})

    def terminate_all(self):
        from selenium_interceptor.scripts.multi_thread import terminate_thread
        terminate_thread(self.thread)
        self.thread.join()
        self.has_started = False
        self.driver.quit()
