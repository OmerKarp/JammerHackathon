#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 OmerKarp.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

# delay = 20,000 in 1 MHz -> 20 ms delay


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
    def __init__(self, f1=400,f2=400,delay=1024):
        gr.sync_block.__init__(self,
            name="delay_attack",
            in_sig=[np.complex64],
            out_sig=[np.complex64])

        self.delay = int(delay)
        self.buffer = np.zeros(int(delay), dtype=np.complex64)
        self.index = 0

    def work(self, input_items, output_items):
        in0 = input_items[0]
        out = output_items[0]

        for i in range(len(in0)):
            out[i] = self.buffer[self.index]
            self.buffer [self.index] = in0[i]

            self.index += 1
            if self.index >= self.delay:
                self.index = 0

        return len(output_items[0])
