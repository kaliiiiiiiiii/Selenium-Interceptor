import time
import traceback


class cdp_listener(object):
    from typing import Dict

    def __init__(self, driver):
        self.session = None
        self.devtools = None
        self.listener = {}
        self.driver = driver
        self.my_headers = None
        self.thread = None
        self.is_running = None
        self.request_patterns = None
        self.all_requests = [{"urlPattern": "*"}]
        self.all_images = [{"resourceType": "Image"}]
        self.all_responses = [{"urlPattern": "*", "requestStage": "Response"}]

    async def async_helper(self):
        async with self.driver.bidi_connection() as connection:
            self.session, self.devtools = connection.session, connection.devtools

            my_listener = await self.listener["listener"](connection=connection)
            async for event in my_listener:
                try:
                    await self.session.execute(await self.listener["at_event"](event=event, connection=connection))
                except Exception as e:
                    if -32602 in e.__dict__.values():
                        traceback.print_exc()  # 'Invalid InterceptionId.'
                    else:
                        raise e

    def trio_helper(self):
        import trio
        self.is_running = True
        trio.run(self.async_helper)

    def start_threaded(self, listener: Dict[str, callable]):
        if listener:
            self.listener = listener

        import threading
        thread = threading.Thread(target=self.trio_helper)
        self.thread = thread
        thread.start()

        while True:
            time.sleep(0.1)
            if self.is_running:
                break

        return thread

    def connection_refused(self, event, connection):
        self.print_event(event)

        session, devtools = connection.session, connection.devtools
        # show_image(event.request.url)
        return devtools.fetch.fail_request(request_id=event.request_id,
                                           error_reason=devtools.network.ErrorReason.CONNECTION_REFUSED)

    async def get_response_body(self, request_id):
        if not self.devtools:
            raise RuntimeError(self.__module__ + "needs to be running for using this function.")
        try:
            body = await self.session.execute(self.devtools.fetch.get_response_body(request_id))
        except Exception as e:
            if -32000 in e.__dict__.values() or -32602 in e.__dict__.values():  # 'Can only get response body on requests captured after headers received.' or  'Invalid InterceptionId.'
                traceback.print_exc()
                body = [None, None]
            else:
                raise e
        return body

    async def modify_headers(self, event, connection):
        self.print_event(event)

        session, devtools = connection.session, connection.devtools

        headers = event.request.headers.to_json()

        try:
            headers.update(self.my_headers)
        except TypeError:
            traceback.print_exc()
            raise TypeError("Define headers using cdp_listener.specify_headers.\n")
        my_headers = []
        for item in headers.items():
            my_headers.append(devtools.fetch.HeaderEntry.from_json({"name": item[0], "value": item[1]}))

        return devtools.fetch.continue_request(request_id=event.request_id, headers=my_headers)

    def specify_headers(self, headers: Dict[str, str]):
        self.my_headers = headers

    def decode_body(self, body: str, response, encoding="utf-8"):
        import base64
        import json
        if body:
            decoded = base64.b64decode(body).decode(encoding=encoding, errors="replace")
            rep_type = response.resource_type.name
            if rep_type == "XHR":
                # noinspection PyBroadException
                try:
                    decoded = json.loads(decoded)
                except json.JSONDecodeError:  # wasn't json
                    pass
                except Exception:
                    traceback.print_exc()
            return decoded
        else:
            return body

    def encode_body(self, decoded: str or dict, encoding="utf-8"):
        import base64
        import json
        if decoded:
            if not type(decoded) is str:
                # noinspection PyMethodFirstArgAssignment
                decoded = json.dumps(decoded)
            encoded = base64.b64encode(decoded.encode(encoding=encoding, errors="replace")).decode(encoding=encoding)
            return encoded
        else:
            return decoded

    def specify_patterns(self, json_patterns: list):
        if not self.devtools:
            raise RuntimeError(self.__module__ + "needs to be running for using this function.")
        pattern = map(self.devtools.fetch.RequestPattern.from_json, json_patterns)
        pattern = list(pattern)
        self.request_patterns = pattern[:]
        return pattern[:]

    async def images(self, connection):
        session, devtools = connection.session, connection.devtools
        pattern = self.specify_patterns(self.all_images)
        await session.execute(devtools.fetch.enable(patterns=pattern))

        return session.listen(devtools.fetch.RequestPaused)

    async def requests(self, connection):
        session, devtools = connection.session, connection.devtools
        pattern = self.specify_patterns(self.all_requests)
        await session.execute(devtools.fetch.enable(patterns=pattern))

        return session.listen(devtools.fetch.RequestPaused)

    async def responses(self, connection):
        session, devtools = connection.session, connection.devtools
        pattern = self.specify_patterns(self.all_responses)
        await session.execute(devtools.fetch.enable(patterns=pattern))

        return session.listen(devtools.fetch.RequestPaused)

    def show_image(self, url: str):  # show image from URL
        from PIL import Image
        from io import BytesIO
        import requests
        # noinspection PyBroadException
        try:
            response = requests.get(url)
            img = Image.open(BytesIO(response.content))
            img.show()
        except Exception:
            traceback.print_exc()

    def print_event(self, event):
        print({"type": event.resource_type.to_json(), "frame_id": event.frame_id, "url": event.request.url})

    def terminate_all(self):
        self.terminate_thread()
        self.driver.quit()

    def terminate_thread(self):
        from selenium_interceptor.scripts.multi_thread import terminate_thread
        terminate_thread(self.thread)
        self.thread.join()
        self.is_running = False
