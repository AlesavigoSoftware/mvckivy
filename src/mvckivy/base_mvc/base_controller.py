from kivy.animation import Animation
from kivy.event import EventDispatcher
from typing import Callable

from mvckivy.uix.behaviors.mvc_behavior import MVCWidget
from mvckivy import logger
from mvckivy.network import UrlRequestRequests
from mvckivy.network.decorators import call_after


class DispatchException(Exception):
    pass


class BaseController(MVCWidget):
    __events__ = ("on_app_start", "on_app_exit")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._to_cancel_requests: list[UrlRequestRequests] = []

    def dispatch_to_model(
        self,
        animate: bool = False,
        parallel: bool = False,
        duration: float = 1,
        transition: str = "in_quad",
        force_dispatch: bool = False,
        custom_model: None | EventDispatcher = None,
        nested_assignment: bool = False,
        **kwargs,
    ):
        """
        Dispatch properties to the target model with optional animation.

        This method updates properties on the provided model (or self.model by default) using either a direct
        assignment or an animated transition. When animation is enabled via the ``animate`` flag, property updates
        are passed to an Animation instance which is then started on the target model. The method supports both
        sequential and parallel animations. In parallel mode, all animations are merged using the bitwise AND operator.
        Additionally, the method can handle nested assignments when property values are provided as tuples.

        Parameters
        ----------
        animate : bool, optional
            If True, perform the update using an animation. Otherwise, update properties immediately.
            Default is False.
        parallel : bool, optional
            When animate is True, if True, combine individual property animations in parallel.
            Default is False.
        duration : float, optional
            The duration of the animation (in seconds) when animate is True.
            Default is 1.
        transition : str, optional
            The transition (easing) function to be used for the animation.
            Default is 'in_quad'.
        force_dispatch : bool, optional
            If True, forces the dispatch of the property after updating its value.
            Default is False.
        custom_model : None | EventDispatcher
            The target model instance where properties will be updated. If not provided, the method uses
            ``self.model``.
        nested_assignment : bool, optional
            If True, allows nested property assignment when a property value is provided as a tuple.
            For tuple values, if the tuple length is 2, the first element is considered an attribute key,
            and the second the value to be set on that nested attribute.
            Default is False.
        **kwargs
            A set of key-value pairs corresponding to the property names and the new values to assign.
            When animate is True, these kwargs are passed to the Animation constructor.

        Raises
        ------
        DispatchException
            If animation is enabled with parallel mode and a nested assignment is attempted (i.e. when a tuple
            value is provided while nested_assignment is True), a DispatchException is raised.

        Returns
        -------
        None
        """
        if not custom_model:
            custom_model = self.model

        if animate:
            anim = None

            if parallel:
                for key, value in kwargs.items():
                    if isinstance(value, tuple) and nested_assignment:
                        raise DispatchException(
                            f"Animations are not supported for nested assignment: {key}: {value}"
                        )

                    if anim is not None:
                        anim = anim & Animation(
                            **{key: value}, d=duration, t=transition
                        )
                    else:
                        anim = Animation(**{key: value}, d=duration, t=transition)
            else:
                anim = Animation(**kwargs, d=duration, t=transition)

            anim.start(custom_model)

        else:

            for key, value in kwargs.items():

                prop = custom_model.property(key)

                if isinstance(value, tuple) and nested_assignment:
                    attr = getattr(custom_model, key, None)
                    if attr and len(value) == 2:
                        attr[value[0]] = value[1]
                else:
                    prop.set(custom_model, value)

                if force_dispatch:
                    prop.dispatch(custom_model)

    def make_request(
        self,
        endpoint: str,
        params: None | dict = None,
        is_streaming: bool = False,
        post_req_json: None | dict = None,
        files: None | dict = None,
        jsonify_stream_chunk: bool = False,
        chunk_polling_frequency_hz: None | int = None,
        on_success=None,
        on_redirect=None,
        on_failure=None,
        on_error=None,
        on_stream_chunk: Callable | None = None,  # doesn't log
        on_cancel=None,  # doesn't log
        on_finish=None,  # doesn't log
        on_progress=None,  # doesn't log
        decode=False,  # Turned off
        req_body=None,
        req_headers=None,
        chunk_size=8192,
        timeout=None,
        method=None,
        debug=False,
        file_path=None,
        ca_file=None,
        verify=True,
        proxy_host=None,
        proxy_port=None,
        proxy_headers=None,
        user_agent=None,
        cookies=None,
        auth=None,
    ) -> UrlRequestRequests:
        """
        Initiates and returns a configured URL request.

        This method constructs a UrlRequestRequests object using the provided parameters and options.
        It supports both regular and streaming requests, and allows the caller to specify a variety of
        callbacks for handling the different stages and outcomes of the request such as success, redirect,
        failure, error, streaming, progress, cancellation, and finish events. The callbacks are wrapped
        with the ``@call_after`` decorator, ensuring that they are executed after the corresponding event.
        For streaming requests, the request instance is appended to an internal cancellation list.

        Parameters
        ----------
        endpoint : str
            The API endpoint (appended to the base URL) to which the request is sent.
        params : dict, optional
            Dictionary of URL parameters to include in the request. Defaults to None.
        is_streaming : bool, optional
            If True, the request will handle streaming responses. Defaults to False.
        post_req_json : dict, optional
            JSON data to be sent in the body of a POST request. Defaults to None.
        files : dict, optional
            A dictionary of files to be uploaded with the request. Defaults to None.
        jsonify_stream_chunk : bool, optional
            If True, each chunk received during streaming will be converted to JSON. Defaults to False.
        chunk_polling_frequency_hz : int, optional
            Frequency (in Hertz) for polling data chunks in streaming mode. Defaults to None.

        Callback Parameters
        -------------------
        on_success : callable, optional
            Callback function executed on successful response.
        on_redirect : callable, optional
            Callback function executed when a redirect response is received.
        on_failure : callable, optional
            Callback function executed on a failed request response.
        on_error : callable, optional
            Callback function executed when an error occurs during the request.
        on_stream_chunk : callable, optional
            Callback function for each stream chunk received. (Does not perform any logging.)
        on_cancel : callable, optional
            Callback function executed if the request is cancelled. (Does not perform any logging.)
        on_finish : callable, optional
            Callback function executed after the request is finished. (Does not perform any logging.)
        on_progress : callable, optional
            Callback function to report progress during the request. (Does not perform any logging.)

        Additional Request Options
        --------------------------
        decode : bool, optional
            If True, decode the response data; this feature is turned off by default. Defaults to False.
        req_body : any, optional
            The body of the request.
        req_headers : any, optional
            Headers to include in the request.
        chunk_size : int, optional
            The size (in bytes) of each chunk for streaming responses. Defaults to 8192.
        timeout : any, optional
            The maximum time to wait for the request to complete.
        method : any, optional
            The HTTP method to use (e.g., "GET", "POST"). Defaults to None.
        debug : bool, optional
            If True, enables debugging mode. Defaults to False.
        file_path : any, optional
            File path for operations involving file data.
        ca_file : any, optional
            Path to a CA certificate file for SSL verification.
        verify : bool, optional
            Whether to verify SSL certificates. Defaults to True.
        proxy_host : any, optional
            Proxy host address.
        proxy_port : any, optional
            Proxy port number.
        proxy_headers : any, optional
            Headers to include when using a proxy.
        user_agent : any, optional
            User-Agent string for the request.
        cookies : any, optional
            Cookies to be sent with the request.
        auth : any, optional
            Authentication credentials for the request.

        Returns
        -------
        UrlRequestRequests
            A configured instance of UrlRequestRequests ready to be executed.

        Notes
        -----
        The internal helper callbacks (_on_success, _on_redirect, _on_failure, _on_error,
        _on_stream_chunk, _on_cancel, _on_finish, and _on_progress) wrap the provided callbacks using
        the ``@call_after`` decorator. Logging is performed for the error, failure, success, and redirect
        events. The other callbacks serve to extend functionality without directly logging their events.
        If the request is a streaming request, the instance is added to an internal list used to
        track requests that may need to be cancelled.

        """

        @call_after(on_error)
        def _on_error(request, error) -> None:
            logger.error(error)

        @call_after(on_failure)
        def _on_failure(request, result) -> None:
            logger.warning(result)

        @call_after(on_success)
        def _on_success(request, result) -> None:
            logger.info(result)

        @call_after(on_redirect)
        def _on_redirect(request, result):
            logger.info(result)

        @call_after(on_finish)
        def _on_finish(request):
            pass

        @call_after(on_cancel)
        def _on_cancel(request):
            pass

        @call_after(on_stream_chunk)
        def _on_stream_chunk(request, stream_chunk):
            pass

        @call_after(on_progress)
        def _on_progress(request, current_size, total_size):
            pass

        req = UrlRequestRequests(
            base_url=self.app.model.gs_base_url,
            endpoint=endpoint,
            params=params,
            is_streaming=is_streaming,
            post_req_json=post_req_json,
            files=files,
            jsonify_stream_chunk=jsonify_stream_chunk,
            chunk_polling_frequency_hz=chunk_polling_frequency_hz,
            on_success=_on_success,
            on_redirect=_on_redirect,
            on_failure=_on_failure,
            on_error=_on_error,
            on_progress=_on_progress,
            on_cancel=_on_cancel,
            on_finish=_on_finish,
            on_stream_chunk=_on_stream_chunk,
            req_body=req_body,
            req_headers=req_headers,
            chunk_size=chunk_size,
            timeout=timeout,
            method=method,
            decode=decode,
            debug=debug,
            file_path=file_path,
            ca_file=ca_file,
            verify=verify,
            proxy_host=proxy_host,
            proxy_port=proxy_port,
            proxy_headers=proxy_headers,
            user_agent=user_agent,
            cookies=cookies,
            auth=auth,
        )

        if is_streaming:
            self._to_cancel_requests.append(req)

        return req

    def on_app_start(self):
        pass

    def on_app_exit(self):
        for req in self._to_cancel_requests:
            req.cancel()
