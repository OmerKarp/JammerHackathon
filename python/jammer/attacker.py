#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 OmerKarp.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy as np
from gnuradio import gr
from gnuradio import gr
from gnuradio.filter import firdes
from gnuradio.fft import window

class attacker(gr.sync_block):
    """
    docstring for block attacker
    """
    def __init__(self, attack_type,freq_start,freq_end,fs,t,fc,attacker_gain):
        gr.sync_block.__init__(self,
            name="attacker",
            in_sig=[np.complex64],
            out_sig=[np.complex64])

        # which attack method
        self.attack_type = attack_type
        self.is_attacking = False

        # information for all the attacks
        self.freq_start = freq_start
        self.freq_end = freq_end
        self.fs = fs
        self.t = t
        self.fc = fc
        self.attacker_gain = attacker_gain

        # ----- barrage information -----
        # Validate inputs
        assert freq_end > freq_start, "end_freq must be greater than start_freq"
        assert abs(freq_start) <= fs / 2, "start_freq out of Nyquist range"
        assert abs(freq_end)   <= fs / 2, "end_freq out of Nyquist range"

        self._samp_rate  = fs
        self._amplitude  = 10

        # Compute bandpass filter taps
        self._taps = self._build_taps()
        # Internal filter state (overlap-save buffer)
        self._filter_state = np.zeros(len(self._taps) - 1, dtype=np.complex64)

        # ----- follow jammer information -----
        self.fft_size     = 1024
        self.num_buffers  = 10
        self.samp_rate    = 3.2e3
        self.threshold_db = 10
        self.bandwidth    = 200
        self.amplitude    = 100.0

        self.total_samples   = self.fft_size * self.num_buffers
        self.accumulated     = np.zeros(self.total_samples, dtype=np.complex64)
        self.sample_count    = 0
        self.jam_freq        = None  # last detected peak frequency

        self.gui_attack_console()

    def gui_attack_console(self):
        pass

    # ------------------------------------------------------------------
    # Create BPS to direct the noise
    # ------------------------------------------------------------------

    def _build_taps(self):
        """Build a complex bandpass FIR filter for [start_freq, end_freq]."""
        bandwidth    = self.freq_end - self.freq_start
        transition_bw = max(bandwidth * 0.1, 1e3)   # 10% of BW, min 1 kHz

        taps = firdes.complex_band_pass(
            gain=1.0,
            sampling_freq=self._samp_rate,
            low_cutoff_freq=self.freq_start,
            high_cutoff_freq=self.freq_end,
            transition_width=transition_bw,
            window=window.WIN_HAMMING
        )
        return np.array(taps, dtype=np.complex64)

    def _apply_filter(self, noise):
        """Manually apply FIR filter with state (overlap-save)."""
        # Prepend saved state so convolution is continuous across work() calls
        x = np.concatenate([self._filter_state, noise])
        filtered = np.convolve(x, self._taps, mode='valid')

        # Save last (len(taps)-1) samples as state for next call
        self._filter_state = x[-(len(self._taps) - 1):]
        return filtered.astype(np.complex64)

    # ------------------------------------------------------------------
    # Work function
    # ------------------------------------------------------------------

    def work(self, input_items, output_items):
        in0 = input_items[0]
        out = output_items[0]

        if not self.is_attacking:
            out[:] = np.zeros(np.size(out))
            return len(out)

        if self.attack_type == 'Barrage':
            return self.Barrage_attack(out)
        elif self.attack_type == 'Follow':
            return self.Follow_attack(in0, out)
        elif self.attack_type == 'Spoof':
            return self.Spoof_attack(in0,out)

        print("No such attack exist!")
        return len(output_items[0])

    def Barrage_attack(self, out):
        n = len(out)

        # 1. Generate complex white Gaussian noise
        #    Variance = 0.5 per component so total complex power = 1
        noise = (
            np.random.normal(0, 0.5, n) +
            1j * np.random.normal(0, 0.5, n)
        ).astype(np.complex64)

        # 2. Band-limit to [start_freq, end_freq]
        filtered = self._apply_filter(noise)

        # Trim/pad to exactly n samples (convolution may differ slightly)
        if len(filtered) >= n:
            filtered = filtered[:n]
        else:
            filtered = np.pad(filtered, (0, n - len(filtered)))

        # 3. Normalize and scale to target amplitude
        rms = np.sqrt(np.mean(np.abs(filtered) ** 2))
        if rms > 0:
            filtered = filtered / rms  # normalize to unit power
        filtered *= self._amplitude    # scale to desired amplitude

        out[:] = filtered
        return n

    def Spoof_attack(self, in0, out):
        pass