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
        self.preamble_value = 1
        self.one_bit = np.concatenate((np.ones(round(2*t*fs)), -1 * np.ones(round(t*fs))))
        self.zero_bit = np.concatenate((np.ones(round(t*fs)), -1 * np.ones(round(2*t*fs))))
        self.samples_queue = deque([self.preamble_value]*self.preamble_length + self.enqueue_from_string(msg, fs, t).tolist())

    def work(self, input_items, output_items):
        out = output_items[0]

        out_len = len(out[:])
        #print(out_len)
        for i in range(out_len):
            try:
                out[i] = self.samples_queue.popleft()
            except:
                out[i] = 0

        return len(output_items[0])


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