#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .weighted_round_robin import WRRScheduler
from threading import Lock
import time


class Endpoint(object):
    r_lock = Lock()
    w_lock = Lock()
    num_r = 0

    def __init__(self):
        self.endpoints = dict()
        self.scheduler = None

    def __r_lock_acquire(self):
        self.r_lock.acquire()
        self.num_r += 1
        if self.num_r == 1:
            self.w_lock.acquire()
        self.r_lock.release()

    def __r_lock_release(self):
        self.r_lock.acquire()
        self.num_r -= 1
        if self.num_r == 0:
            self.w_lock.release()
        self.r_lock.release()

    def __w_lock_acquire(self):
        self.w_lock.acquire()

    def __w_lock_release(self):
        self.w_lock.release()

    def set_endpoints(self, endpoints):
        self.__w_lock_acquire()
        self.endpoints = endpoints
        self.scheduler = WRRScheduler(endpoints)
        self.__w_lock_release()

    def sync(self):
        pass

    def get(self):
        while True:
            if self.scheduler is not None:
                break
            time.sleep(0.1)

        self.__r_lock_acquire()
        ep = self.scheduler.get_next()[0]
        self.__r_lock_release()
        return ep['ip'] + ':' + str(ep['port'])
