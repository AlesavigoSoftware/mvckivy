from time import sleep, time
from kivy import Config
from typing import Callable, Iterator, Optional
import json
import requests
from kivy.network.urlrequest import g_requests
from kivy.network.urlrequest import UrlRequestRequests as BaseUrlRequestRequests
from kivy.weakmethod import WeakMethod

from utility.logger import logger


class ResultCodeException(Exception):
    pass


class UrlRequestRequests(BaseUrlRequestRequests):
    def __init__(
        self,
        base_url: str,
        endpoint: str,
        params: Optional[dict] = None,
        is_streaming: bool = False,
        post_req_json: Optional[dict] = None,
        files: Optional[dict] = None,
        on_stream_chunk: Optional[Callable] = None,
        jsonify_stream_chunk: bool = False,
        chunk_polling_frequency_hz: Optional[int] = None,
        **kwargs,
    ):
        self.params = params if params is not None else dict()
        self._json = post_req_json if post_req_json is not None else dict()
        self.files = files if files is not None else dict()
        self.is_streaming = is_streaming or bool(on_stream_chunk)
        self.on_stream_chunk = WeakMethod(on_stream_chunk) if on_stream_chunk else None
        self.jsonify_stream_chunk = jsonify_stream_chunk
        self.__current_chunk = dict()
        self.__available_result_codes = [
            "success",
            "error",
            "progress",
            "streaming",
            "killed",
            "finished",
        ]
        self.chunk_polling_frequency_hz = chunk_polling_frequency_hz
        self.__last_timestamp: float = 0.0
        super().__init__(url=f"{base_url}{endpoint}", **kwargs)

    def run(self):
        q = self._queue.appendleft
        url = self.url
        req_body = self.req_body
        req_headers = self.req_headers or {}

        user_agent = self._user_agent
        cookies = self._cookies

        if user_agent:
            req_headers.setdefault("User-Agent", user_agent)

        elif Config.has_section("network") and "useragent" in Config.items("network"):
            useragent = Config.get("network", "useragent")
            req_headers.setdefault("User-Agent", useragent)

        if cookies:
            req_headers.setdefault("Cookie", cookies)

        try:
            result, resp = self._fetch_url(url, req_body, req_headers, q)
            if self.decode:
                result = self.decode_result(result, resp)
        except Exception as e:
            q(("error", None, e))
        else:
            if not self._cancel_event.is_set():
                q(("success", resp, result))

                if self.on_stream_chunk or self.is_streaming:
                    self._trigger_result()  # to dispatch successful request
                    self._stream_data(q, result)

            else:
                q(("killed", None, None))

        # using trigger can result in a missed on_success event
        self._trigger_result()

        # clean ourself when the queue is empty
        while len(self._queue):
            sleep(0.1)
            self._trigger_result()

        # ok, authorize the GC to clean us.
        if self in g_requests:
            g_requests.remove(self)

    def _fetch_url(self, url, body, headers, q):
        # Parse and fetch the current url
        trigger = self._trigger_result
        chunk_size = self._chunk_size
        report_progress = self.on_progress is not None
        file_path = self.file_path

        if self._debug:
            logger.debug("UrlRequest: {0} Fetch url <{1}>".format(id(self), url))
            logger.debug("UrlRequest: {0} - body: {1}".format(id(self), body))
            logger.debug("UrlRequest: {0} - headers: {1}".format(id(self), headers))

        req, resp = self.call_request(body, headers)

        if report_progress or file_path is not None:
            total_size = self.get_total_size(resp)

            # before starting the download, send a fake progress to permit the
            # user to initialize his ui
            if report_progress:
                q(("progress", resp, (0, total_size)))

            if file_path is not None:
                with open(file_path, "wb") as fd:
                    bytes_so_far, result = self.get_chunks(
                        resp, chunk_size, total_size, report_progress, q, trigger, fd=fd
                    )
            else:
                bytes_so_far, result = self.get_chunks(
                    resp, chunk_size, total_size, report_progress, q, trigger
                )

            # ensure that results are dispatched for the last chunk,
            # avoid trigger
            if report_progress:
                q(("progress", resp, (bytes_so_far, total_size)))
                trigger()
        else:
            result = self.get_response(resp)
            try:
                if isinstance(result, bytes):
                    result = result.decode("utf-8")
            except UnicodeDecodeError:
                # if it's an image? decoding would not work
                pass

        self.close_connection(req)

        # return everything
        return result, resp

    def _dispatch_chunk(self, q) -> None:
        if self.chunk_polling_frequency_hz is not None and (
            round(time() - self.__last_timestamp, 3)
            < 1 / self.chunk_polling_frequency_hz
        ):
            return

        q(("streaming", None, self.__current_chunk))
        self._trigger_result()
        self.__last_timestamp = time()

    def _stream_data(self, q, result) -> None:
        self.__last_timestamp = time()

        try:
            telem_iter: Iterator = result.iter_lines()
        except Exception as ex:
            q(("error", None, ex))
            self._trigger_result()
            return

        while not self._cancel_event.is_set():
            try:
                # Waits for the next chunk from a server
                self.__current_chunk = next(telem_iter)
            except StopIteration:
                q(("finished", None, None))
                self._trigger_result()
                return

            self._dispatch_chunk(q)

        q(("killed", None, None))
        self._trigger_result()

    def _dispatch_result(self, dt):
        while True:
            # Read the result pushed on the queue, and dispatch to the client
            try:
                result, resp, data = self._queue.pop()
            except IndexError:
                return

            if result not in self.__available_result_codes:
                raise ResultCodeException(
                    f'Current result code "{result}" not in {self.__available_result_codes}'
                )

            if resp:
                # Small workaround in order to prevent the situation mentioned
                # in the comment below
                final_cookies = ""
                parsed_headers = []
                for key, value in self.get_all_headers(resp):
                    if key == "Set-Cookie":
                        final_cookies += "{};".format(value)
                    else:
                        parsed_headers.append((key, value))
                parsed_headers.append(("Set-Cookie", final_cookies[:-1]))

                # XXX usage of dict can be dangerous if multiple headers
                # are set even if it's invalid. But it look like it's ok
                # ?  http://stackoverflow.com/questions/2454494/..
                # ..urllib2-multiple-set-cookie-headers-in-response
                self._resp_headers = dict(parsed_headers)
                self._resp_status = self.get_status_code(resp)

            if result == "success":
                status_class = self.get_status_code(resp) // 100

                if status_class in (1, 2):
                    if self._debug:
                        logger.debug(
                            "UrlRequest: {0} Download finished with "
                            "{1} datalen".format(id(self), data)
                        )
                    self._is_finished = True
                    self._result = data
                    if self.on_success:
                        func = self.on_success()
                        if func:
                            func(self, data)

                elif status_class == 3:
                    if self._debug:
                        logger.debug(
                            "UrlRequest: {} Download " "redirected".format(id(self))
                        )
                    self._is_finished = True
                    self._result = data
                    if self.on_redirect:
                        func = self.on_redirect()
                        if func:
                            func(self, data)

                elif status_class in (4, 5):
                    if self._debug:
                        logger.debug(
                            "UrlRequest: {} Download failed with "
                            "http error {}".format(id(self), self.get_status_code(resp))
                        )
                    self._is_finished = True
                    self._result = data
                    if self.on_failure:
                        func = self.on_failure()
                        if func:
                            func(self, data)

            elif result == "error":
                if self._debug:
                    logger.debug(
                        "UrlRequest: {0} Download error " "<{1}>".format(id(self), data)
                    )
                self._is_finished = True
                self._error = data
                if self.on_error:
                    func = self.on_error()
                    if func:
                        func(self, data)

            elif result == "progress":
                if self._debug:
                    logger.debug(
                        "UrlRequest: {0} Download progress "
                        "{1}".format(id(self), data)
                    )
                if self.on_progress:
                    func = self.on_progress()
                    if func:
                        func(self, data[0], data[1])

            elif result == "streaming":
                stream_chunk = json.loads(data) if self.jsonify_stream_chunk else data

                if self.on_stream_chunk:
                    func = self.on_stream_chunk()
                    if func:
                        func(self, stream_chunk)

            elif result == "killed":
                if self._debug:
                    logger.debug("UrlRequest: Cancelled by user")
                if self.on_cancel:
                    func = self.on_cancel()
                    if func:
                        func(self)

            if result not in ["progress", "streaming"] and self.on_finish:
                if self._debug:
                    logger.debug("UrlRequest: Request is finished")
                func = self.on_finish()
                if func:
                    func(self)

    def get_response(self, resp):
        return resp

    def call_request(self, body, headers):
        timeout = self._timeout
        ca_file = self.ca_file
        verify = self.verify
        url = self._requested_url
        auth = self._auth

        req = requests
        kwargs = dict()

        body = body if body is not None else json.dumps(self._json)

        # get method
        if self._method is None:
            method = "get" if body is None else "post"
        else:
            method = self._method.lower()

        req_call = getattr(req, method)

        if auth:
            kwargs["auth"] = auth

        if self.params:
            kwargs["params"] = self.params

        if self._json:
            kwargs["json"] = self._json

        if self.is_streaming:
            kwargs["stream"] = self.is_streaming

        if self.files:
            kwargs["files"] = self.files

        # send request
        response = req_call(
            url,
            data=body,
            headers=headers,
            timeout=timeout,
            verify=verify,
            cert=ca_file,
            **kwargs,
        )

        return None, response
