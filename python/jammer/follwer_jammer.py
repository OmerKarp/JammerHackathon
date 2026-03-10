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

class follwer_jammer(gr.sync_block):
    """
    docstring for block follwer_jammer
    """
    def __init__(self, f1=400,f2=500):
        gr.sync_block.__init__(self,
            name="follwer_jammer",
            in_sig=[np.float32, ],
            out_sig=[np.float32, ])
        self.num_buffers=10
        self.threshold_db=10
        fft_size = 1024
        samp_rate = 3.2e3
        self.fft_size = fft_size
        self.samp_rate = samp_rate

        self.accumulated = np.array([], dtype=np.float32)
        self.buffers_collected = 0


    def work(self, input_items, output_items):
        in0 = input_items[0]
        out = output_items[0]
        out[:] = in0

        # Accumulate samples
        self.accumulated = np.concatenate([self.accumulated, in0])
        self.buffers_collected += 1

        # Wait until we have enough buffers
        if self.buffers_collected < self.num_buffers:
            return len(in0)

        # --- We have enough samples, run FFT ---
        samples = self.accumulated[:self.fft_size * self.num_buffers]

        # Window + FFT
        window = np.blackman(len(samples))
        fft_result = np.fft.fftshift(np.fft.fft(samples * window))
        power_db = 20 * np.log10(np.abs(fft_result) + 1e-12)

        # Find points 10 dB above the mean
        mean_db = np.mean(power_db)
        peaks_mask = power_db > (mean_db + self.threshold_db)
        peak_indices = np.where(peaks_mask)[0]

        # Map indices to frequencies
        freqs = np.fft.fftshift(np.fft.fftfreq(len(samples), 1 / self.samp_rate))


        if len(peak_indices) > 0:
            # Find the highest peak among all peaks
            highest_idx = peak_indices[np.argmax(power_db[peak_indices])]
            print(f"Highest peak at {freqs[highest_idx]/1e3:.3f} KHz | "
                f"{power_db[highest_idx]:.2f} dB | "
                f"{power_db[highest_idx] - mean_db:.2f} dB above mean")
            
            out[:] = np.cos(2*np.pi*np.abs(freqs[highest_idx]))
        else:
            print("No peaks found above threshold")

        # Reset for next round
        self.accumulated = np.array([], dtype=np.float32)
        self.buffers_collected = 0

        #output adttional signal to block the frequency
        # 

        

        return len(in0)
