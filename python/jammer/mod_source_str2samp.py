#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 oron.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy as np
from collections import deque
from gnuradio import gr

class mod_source_str2samp(gr.sync_block):
    """
    docstring for block mod_source_str2samp
    """
    def __init__(self, t=1,fs=1000,msg="hello"):
        gr.sync_block.__init__(self,
            name="mod_source_str2samp",
            in_sig=None,
            out_sig=[np.float32, ])
            
        self.t = t
        self.fs = fs
        self.msg = msg
        self.preamble_length = round(fs*t*1)
        self.counter = 0
        self.one_bit = np.concatenate((np.ones(round(2*t*fs)), -1 * np.ones(round(t*fs))))
        self.zero_bit = np.concatenate((np.ones(round(t*fs)), -1 * np.ones(round(2*t*fs))))
        self.waiting_period = 0.5

        # Barker-11 stretched to sample_per_pulse samples per chip
        barker11 = np.array([1, 1, 1, -1, -1, -1, 1, -1, -1, 1, -1], dtype=np.float32)
        self.preamble = np.repeat(barker11, self.preamble_length)  # each chip = one pulse width

        self.samples_queue = deque(
            self.preamble.tolist() + self.enqueue_from_string(msg, fs, t).tolist()
        )

    def work(self, input_items, output_items):
        out = output_items[0]

        out_len = len(out[:])

        for i in range(out_len):
            if len(self.samples_queue) > 0:
                out[i] = self.samples_queue.popleft()
            else:
                out[i] = 0
                self.counter += 1
                if self.counter > (self.fs * self.waiting_period):
                    self.counter = 0
                    self.add_msg_to_queue()

        return len(output_items[0])
    
    def add_msg_to_queue(self):
        self.samples_queue.extend(self.preamble.tolist() + self.enqueue_from_string(self.msg, self.fs, self.t).tolist())

    def symbol_1(self,fs,t):
        symbol = self.one_bit
        return symbol

    def symbol_0(self,fs, t):
        symbol = self.zero_bit
        return symbol

    def enqueue_from_string(self,msg, fs, t):
        list_bits = ''.join(format(ord(char), '08b') for char in msg)
        samples = np.array([])

        for bit in list_bits:
            if bit=='1':
                samples = np.append(samples,self.symbol_1(fs,t))

            else:
                samples = np.append(samples,self.symbol_0(fs,t))    

        return samples