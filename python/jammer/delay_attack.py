#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 OmerKarp.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

# delay = 0.02 at 1 MHz sample rate -> 20 ms delay (20,000 samples)


import numpy as np
from gnuradio import gr

class delay_attack(gr.sync_block):
    """
    docstring for block delay_attack
    [A B C D E]
    if delay = 3
    [0 0 0 A B]
    and the next call will be
    [D E . . .]
    """
    def __init__(self, f1=400, f2=400, delay=0.001, sample_rate=1e6):
        gr.sync_block.__init__(self,
            name="delay_attack",
            in_sig=[np.complex64],
            out_sig=[np.complex64])

        delay_samples = int(delay * sample_rate)
        self.delay = delay_samples
        self.buffer = np.zeros(delay_samples, dtype=np.complex64)
        self.index = 0

    def work(self, input_items, output_items):
        in0 = input_items[0]
        out = output_items[0]
        N = len(in0)

        indices = (self.index + np.arange(N)) % self.delay
        out[:] = self.buffer[indices]
        self.buffer[indices] = in0
        self.index = (self.index + N) % self.delay

        return N
