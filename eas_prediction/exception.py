#!/usr/bin/env python
# -*- coding: utf-8 -*-


class PredictException(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message

    def __str__(self):
        return 'Code: %s, Message: %s' % (self.code, self.message)