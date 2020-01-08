#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .exception import PredictException
from .weighted_round_robin import WRRScheduler
from threading import Lock
import time
import traceback


def endpoint_sort_func(x):
    return '%s:%s:%s' % (x[0]['ip'], x[0]['port'], x[1])

class Endpoint(object):
    r_lock = Lock()
    w_lock = Lock()
    num_r = 0

    def __init__(self, logger):
        self.endpoints = dict()
        self.scheduler = None
        self.logger = logger

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

    def __changed(self, endpoints):
        if len(self.endpoints) != len(endpoints):
            return True
        endpoints = sorted(endpoints, key=endpoint_sort_func)
        for idx, ep in enumerate(self.endpoints):
            old_endpoint = ep[0]
            old_weight = ep[1]
            cur_endpoint = endpoints[idx][0]
            cur_weight = endpoints[idx][1]
            if old_weight != cur_weight:
                return True
            if old_endpoint['ip'] != cur_endpoint['ip'] or old_endpoint['port'] != cur_endpoint['port']:
                return True
        return False

    def set_endpoints(self, endpoints):
        if self.scheduler is None:
            self.__w_lock_acquire()

            try:
                self.scheduler = WRRScheduler(endpoints)
                self.endpoints = sorted(endpoints, key=endpoint_sort_func)
            except Exception as e:
                traceback.print_stack()

            self.__w_lock_release()
            self.logger.info('Service endpoints initialized to: %s' % endpoints)
        elif self.__changed(endpoints):
            self.__w_lock_acquire()

            try:
                self.scheduler.set_data(endpoints)
                self.endpoints = sorted(endpoints, key=endpoint_sort_func)
            except Exception as e:
                traceback.print_stack()

            self.__w_lock_release()
            self.logger.info('Service endpoints changed to: %s' % endpoints)
        else:
            self.logger.debug('Service endpoints unchanged, skip it')

    def get_size(self):
        self.__r_lock_acquire()
        length = len(self.endpoints)
        self.__r_lock_release()
        return length

    def sync(self):
        pass

    def get(self):
        retry = 0
        while True:
            if self.scheduler is not None:
                break
            time.sleep(0.1)
            retry += 1
            if retry > 50: # 5s timeout
                raise PredictException(500, 'Get service backend timeout')
                break

        self.__w_lock_acquire()
        try:
            ep = self.scheduler.get_next()
            if ep is not None:
                ep = ep[0]
        # catch every unexpected exceptions in case of dead lock
        except Exception as e:
            ep = None
            traceback.print_stack()
            self.logger.error('Unexpected exception occured while getting item from WRR: %s' % str(e))
        self.__w_lock_release()

        if ep is None:
            raise PredictException(500, 'No backend found for the target service')

        return ep['ip'] + ':' + str(ep['port'])
