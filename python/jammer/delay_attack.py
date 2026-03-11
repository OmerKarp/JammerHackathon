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
    Replay attack: records incoming signal, then retransmits it
    after a random delay (set once at start).
    """
    def __init__(self, f1=400, f2=400, delay=0.001, sample_rate=1e6):
        gr.sync_block.__init__(self,
            name="delay_attack",
            in_sig=[np.complex64],
            out_sig=[np.complex64])

        self.sample_rate = sample_rate

        # Random delay set ONCE at init, not every call
        rand_delay = delay + np.random.rand() * 2  # delay + 0 to 2 seconds random
        self.delay_samples = int(rand_delay * sample_rate)
        print(f"Replay delay: {rand_delay:.3f}s = {self.delay_samples} samples")

        # Pre-fill buffer with zeros (initial silence)
        self.buffer = np.zeros(self.delay_samples, dtype=np.complex64)

    def work(self, input_items, output_items):
        in0 = input_items[0]
        out = output_items[0]
        N   = len(in0)

        # Edge case: no delay or buffer too small → pass through
        if self.delay_samples == 0 or N > self.delay_samples:
            out[:] = in0
            return N

        # Prepend saved buffer to incoming samples
        combined = np.concatenate([self.buffer, in0])

        # Output is the oldest N samples (the delayed/replayed ones)
        out[:] = combined[:N]

        # Save the last delay_samples for next call
        self.buffer = combined[N:N + self.delay_samples]

        return N