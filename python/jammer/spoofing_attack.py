#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 oron.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy as np
from gnuradio import gr
from scipy.signal import firwin, lfilter
from collections import deque

class spoofing_attack(gr.sync_block):
    """
    docstring for block spoofing_attack
    """
    def __init__(self, t=1,fs=1000,msg="hello",timeout=0.2):
        gr.sync_block.__init__(self,
            name="spoofing_attack",
            in_sig=None,
            out_sig=[np.float32, ])
        self.t         = t
        self.fs        = fs
        self.msg       = msg
        self.timeout   = timeout
        self.fc        = 1000
        self.bandwidth = 200
        self.amplitude = 100

        # Build one_bit and zero_bit symbols
        self.one_bit  = np.concatenate((np.ones(round(2*t*fs)), -1 * np.ones(round(t*fs)))).astype(np.float32)
        self.zero_bit = np.concatenate((np.ones(round(t*fs)),   -1 * np.ones(round(2*t*fs)))).astype(np.float32)

        # Build Barker-11 preamble
        barker11       = np.array([1, 1, 1, -1, -1, -1, 1, -1, -1, 1, -1], dtype=np.float32)
        self.preamble  = np.repeat(barker11, round(fs * t))

        # Fill queue: noise → preamble → message
        self.samples_queue = deque()
        self.add_msg_to_queue()

    def work(self, input_items, output_items):
        out     = output_items[0]
        out_len = len(out)

        for i in range(out_len):
            if len(self.samples_queue) > 0:
                out[i] = self.samples_queue.popleft()
            else:
                out[i] = 0  # silence after message is done

        return out_len

    def add_msg_to_queue(self):
        # 1. Noise for timeout*2 seconds
        noise    = self.bandlimited_noise(self.fc, int(2 * self.timeout * self.fs)).tolist()
        # 2. Preamble
        preamble = self.preamble.tolist()
        # 3. Message
        msg      = self.enqueue_from_string(self.msg, self.fs, self.t).tolist()

        self.samples_queue.extend(noise + preamble + msg)
        print(f"Queue loaded: {int(2*self.timeout*self.fs)} noise samples + "
              f"{len(preamble)} preamble samples + "
              f"{len(msg)} message samples")

    def bandlimited_noise(self, center_freq, num_samples):
        # Real-valued noise only (float32 output)
        noise = np.random.normal(0, self.amplitude, num_samples).astype(np.float32)

        # Lowpass filter
        cutoff = np.clip((self.bandwidth / 2) / (self.fs / 2), 0.01, 0.99)
        taps   = firwin(101, cutoff)
        noise  = lfilter(taps, 1.0, noise).astype(np.float32)

        # For real signal: upconvert using cosine (real part of exp)
        t      = np.arange(num_samples) / self.fs
        noise *= np.cos(2 * np.pi * center_freq * t).astype(np.float32)

        return noise

    def enqueue_from_string(self, msg, fs, t):
        list_bits = ''.join(format(ord(char), '08b') for char in msg)
        samples   = np.array([], dtype=np.float32)

        for bit in list_bits:
            if bit == '1':
                samples = np.append(samples, self.one_bit)
            else:
                samples = np.append(samples, self.zero_bit)

        return samples