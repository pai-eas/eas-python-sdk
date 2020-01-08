#########
#  Author: Marcin Matlaszek <mmatlaszek@gmail.com>
#  Description: Implementation of WeightedRoundRobin algorithm.
########

import sys
import math
import fractions
import functools


class WRRScheduler:
    cw = 0
    i = -1
    data_set = []
    max_s = None
    gcd_s = None
    len_s = None

    def __init__(self, s=None):
        self._init_dataset(s)

    def _init_dataset(self, s):
        self.data_set = s
        if s is None or len(s) == 0:
            return
        self.max_s = max(s, key=lambda x: x[1])[1]
        if sys.version_info[0] < 3:
            self.gcd_s = functools.reduce(fractions.gcd, [weight for data, weight in s])
        else:
            self.gcd_s = functools.reduce(math.gcd, [weight for data, weight in s])
        self.len_s = len(s)

    def schedule(self):
        if self.data_set is None or len(self.data_set) == 0:
            return None
        while True:
            self.i = (self.i + 1) % self.len_s
            if self.i == 0:
                self.cw = self.cw - self.gcd_s
                if self.cw <= 0:
                    self.cw = self.max_s
                    if self.cw == 0:
                        return None
            if self.data_set[self.i][1] >= self.cw:
                return self.data_set[self.i]

    def set_data(self, s):
        self.reset()
        self._init_dataset(s)

    def reset(self):
        self.cw = 0
        self.i = -1
        self.data_set = []
        self.max_s = None
        self.gcd_s = None
        self.len_s = None

    def get_next(self, n=1):
        if n > 1:
            return [self.schedule() for i in range(0, n)]
        return self.schedule()
