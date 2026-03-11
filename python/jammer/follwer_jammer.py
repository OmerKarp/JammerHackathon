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
    Detects the highest frequency peak and jams it with bandlimited noise
    """
    def __init__(self, f1=400e3, f2=500e3):
        gr.sync_block.__init__(self,
            name="follwer_jammer",
            in_sig=[np.complex64],
            out_sig=[np.complex64])

        self.f1 = f1
        self.f2 = f2
        self.fft_size     = 1024
        self.num_buffers  = 10
        self.samp_rate    = self.f2-self.f1
        self.threshold_db = 10
        self.bandwidth    = 20
        self.amplitude    = 100.0

        self.total_samples   = self.fft_size * self.num_buffers
        self.accumulated     = np.zeros(self.total_samples, dtype=np.complex64)
        self.sample_count    = 0
        self.jam_freq        = None  # last detected peak frequency

    def work(self, input_items, output_items):
        try:
            in0 = input_items[0]
            out = output_items[0]

            # --- Accumulate samples into pre-allocated buffer ---
            space_left = self.total_samples - self.sample_count
            to_copy    = min(len(in0), space_left)
            self.accumulated[self.sample_count:self.sample_count + to_copy] = in0[:to_copy]
            self.sample_count += to_copy

            # --- If we have a known jam freq, output noise while accumulating ---
            if self.jam_freq is not None:
                out[:] = self.bandlimited_noise(
                    center_freq=self.jam_freq,
                    num_samples=len(in0)
                )
            else:
                out[:] = 0

            # --- Not enough samples yet ---
            if self.sample_count < self.total_samples:
                return len(in0)

            # --- Enough samples: run FFT ---
            window     = np.blackman(self.total_samples)
            fft_result = np.fft.fftshift(np.fft.fft(self.accumulated * window))
            power_db   = 20 * np.log10(np.abs(fft_result) + 1e-12)
            freqs      = np.fft.fftshift(np.fft.fftfreq(self.total_samples, 1.0 / self.samp_rate))

            # --- Find highest peak above threshold ---
            mean_db      = np.mean(power_db)
            peak_indices = np.where(power_db > (mean_db + self.threshold_db))[0]

            if len(peak_indices) > 0:
                highest_idx    = peak_indices[np.argmax(power_db[peak_indices])]
                self.jam_freq  = freqs[highest_idx]
                # print(f"Jamming {self.jam_freq/1e3:.3f} KHz | "
                #       f"{power_db[highest_idx]:.2f} dB | "
                #       f"{power_db[highest_idx] - mean_db:.2f} dB above mean")
            else:
                print("No peaks found above threshold")
                self.jam_freq = None

            # --- Reset accumulation ---
            self.sample_count = 0

        except Exception as e:
            print(f"Error in work: {e}")

        return len(input_items[0])

    def bandlimited_noise(self, center_freq, num_samples):
        # Complex white noise
        #print(f"(+) center freq = {center_freq}, num_samples = {num_samples}")
        noise = (np.random.normal(0, self.amplitude, num_samples) +
                 1j * np.random.normal(0, self.amplitude, num_samples)).astype(np.complex64)

        # Lowpass filter to shape bandwidth (around DC first)
        cutoff = np.clip((self.bandwidth / 2) / (self.samp_rate / 2), 0.01, 0.99)
        taps   = firwin(101, cutoff)
        noise  = lfilter(taps, 1.0, noise).astype(np.complex64)

        # Upconvert to center_freq
        t      = np.arange(num_samples) / self.samp_rate
        noise *= np.exp(1j * 2 * np.pi * center_freq * t).astype(np.complex64)

        return noise