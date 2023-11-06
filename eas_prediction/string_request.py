#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .request import Request
from .request import Response


class StringRequest(Request):
    """
    Request contains raw string data
    """
    def __init__(self, request_data=None):
        self.request_data = '' if request_data is None else request_data

    def __str__(self):
        return self.request_data

    def to_string(self):
        """
        Get the request data in string format
        :return: the request data in format of string
        """
        return self.request_data

    def parse_response(self, response_data):
        """
        Parse the given response data in string format to the related StringResponse object
        :param response_data: the service response data in string format
        :return: the StringResponse object related the request
        """
        return StringResponse(response_data)


class StringResponse(Response):
    """
    Deserialize the response data to a structured object for users to read
    """
    def __init__(self, response_data=None):
        self.response_data = '' if response_data is None else response_data

    def __str__(self):
        return str(self.response_data)

    def to_string(self):
        return str(self.response_data)
