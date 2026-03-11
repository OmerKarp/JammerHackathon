#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 OmerKarp.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy as np
import tkinter as tk
import threading
from gnuradio import gr
from gnuradio.filter import firdes
from gnuradio.fft import window
from scipy.signal import firwin, lfilter
from collections import deque

class attacker(gr.sync_block):
    """
    docstring for block attacker
    """
    def __init__(self, attack_type,freq_start,freq_end,fs,t,fc,attacker_gain,timeout,msg):
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
        self.timeout = timeout
        self.msg = msg

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
        self.samp_rate    = self.freq_end-self.freq_start
        self.threshold_db = 10
        self.bandwidth    = 200
        self.amplitude    = 100.0

        self.total_samples   = self.fft_size * self.num_buffers
        self.accumulated     = np.zeros(self.total_samples, dtype=np.complex64)
        self.sample_count    = 0
        self.jam_freq        = None  # last detected peak frequency

        self.preamble_length = round(fs*t*1)
        self.one_bit = np.concatenate((np.ones(round(2*t*fs)), -1 * np.ones(round(t*fs))))
        self.zero_bit = np.concatenate((np.ones(round(t*fs)), -1 * np.ones(round(2*t*fs))))
        barker11 = np.array([1, 1, 1, -1, -1, -1, 1, -1, -1, 1, -1], dtype=np.float32)
        self.preamble = np.repeat(barker11, self.preamble_length)  # each chip = one pulse width

        self.samples_queue = deque()
        self.add_msg_to_queue()

        self.gui_attack_console()

    def gui_attack_console(self):
        def run():
            MODES = [
                ("Barrage",       "Barrage"),
                ("Follow Jammer", "Follow"),
                ("Spoof",         "Spoof"),
            ]
            CIRCLE_R         = 12
            SELECTED_COLOR   = "#2196F3"
            UNSELECTED_COLOR = "#ffffff"
            OUTLINE_COLOR    = "#555555"

            root = tk.Tk()
            root.title("Attack Console")
            root.geometry("320x520")
            root.resizable(False, False)

            selected_mode = tk.StringVar(value=self.attack_type)
            status_var    = tk.StringVar(value="Idle")
            circles       = {}

            # ---- title ----
            tk.Label(root, text="Attack Type", font=("Helvetica", 12, "bold")).place(
                relx=0.08, rely=0.04, anchor="w")

            # ---- radio selectors ----
            radio_frame = tk.Frame(root)
            radio_frame.place(relx=0.08, rely=0.20, anchor="w")

            canvas = tk.Canvas(radio_frame, bg=root.cget("bg"), highlightthickness=0)
            canvas.pack()

            row_h, pad_x, label_offset = 40, 10, 30
            canvas.config(width=220, height=row_h * len(MODES))

            # ---- shared freq/amp panel (Barrage + Follow) ----
            freq_amp_frame = tk.Frame(root)
            freq_amp_params = [
                ("Start Freq (Hz)", str(int(self.freq_start))),
                ("End Freq (Hz)",   str(int(self.freq_end))),
                ("Amplitude",       str(self._amplitude)),
            ]
            freq_amp_entries = {}
            for row, (lbl, default) in enumerate(freq_amp_params):
                tk.Label(freq_amp_frame, text=lbl, font=("Helvetica", 10),
                         width=16, anchor="w").grid(row=row, column=0, pady=2)
                e = tk.Entry(freq_amp_frame, width=12, font=("Helvetica", 10))
                e.insert(0, default)
                e.grid(row=row, column=1, padx=(6, 0), pady=2)
                freq_amp_entries[lbl] = e

            # ---- spoof panel ----
            spoof_frame = tk.Frame(root)
            spoof_params = [
                ("Start Freq (Hz)", str(int(self.freq_start))),
                ("End Freq (Hz)",   str(int(self.freq_end))),
                ("Amplitude",       str(self._amplitude)),
                ("t (delay s)",     str(self.t)),
                ("fc (Hz)",         str(self.fc)),
            ]
            spoof_entries = {}
            for row, (lbl, default) in enumerate(spoof_params):
                tk.Label(spoof_frame, text=lbl, font=("Helvetica", 10),
                         width=16, anchor="w").grid(row=row, column=0, pady=2)
                e = tk.Entry(spoof_frame, width=12, font=("Helvetica", 10))
                e.insert(0, default)
                e.grid(row=row, column=1, padx=(6, 0), pady=2)
                spoof_entries[lbl] = e

            def hide_all_params():
                freq_amp_frame.place_forget()
                spoof_frame.place_forget()

            def select_mode(mode):
                selected_mode.set(mode)
                self.attack_type = mode
                for m, cid in circles.items():
                    canvas.itemconfig(cid, fill=SELECTED_COLOR if m == mode else UNSELECTED_COLOR)
                hide_all_params()
                if mode in ("Barrage", "Follow"):
                    freq_amp_frame.place(relx=0.08, rely=0.60, anchor="w")
                elif mode == "Spoof":
                    spoof_frame.place(relx=0.08, rely=0.60, anchor="w")

            for i, (label, mode) in enumerate(MODES):
                cy = i * row_h + row_h // 2
                cx = pad_x + CIRCLE_R
                cid = canvas.create_oval(
                    cx - CIRCLE_R, cy - CIRCLE_R, cx + CIRCLE_R, cy + CIRCLE_R,
                    fill=SELECTED_COLOR if mode == self.attack_type else UNSELECTED_COLOR,
                    outline=OUTLINE_COLOR, width=2
                )
                circles[mode] = cid
                canvas.create_text(cx + label_offset, cy, text=label, anchor="w",
                                   font=("Helvetica", 12))
                canvas.tag_bind(cid, "<Button-1>", lambda _, m=mode: select_mode(m))

            # show param panel for initial attack_type
            if self.attack_type in ("Barrage", "Follow"):
                freq_amp_frame.place(relx=0.08, rely=0.60, anchor="w")
            elif self.attack_type == "Spoof":
                spoof_frame.place(relx=0.08, rely=0.60, anchor="w")

            # ---- start / stop ----
            def on_start():
                mode = selected_mode.get()
                if not mode:
                    return
                if mode in ("Barrage", "Follow"):
                    try:
                        new_start = float(freq_amp_entries["Start Freq (Hz)"].get())
                        new_end   = float(freq_amp_entries["End Freq (Hz)"].get())
                        new_amp   = float(freq_amp_entries["Amplitude"].get())
                    except ValueError:
                        status_var.set("Invalid parameters")
                        return
                    self.freq_start = new_start
                    self.freq_end   = new_end
                    self._amplitude = new_amp
                    self.amplitude  = new_amp
                    if mode == "Barrage":
                        self._taps = self._build_taps()
                        self._filter_state = np.zeros(len(self._taps) - 1, dtype=np.complex64)
                    else:
                        # reset follow accumulation for new range
                        self.jam_freq     = None
                        self.sample_count = 0
                        self.accumulated  = np.zeros(self.total_samples, dtype=np.complex64)
                elif mode == "Spoof":
                    try:
                        self.freq_start = float(spoof_entries["Start Freq (Hz)"].get())
                        self.freq_end   = float(spoof_entries["End Freq (Hz)"].get())
                        self._amplitude = float(spoof_entries["Amplitude"].get())
                        self.t          = float(spoof_entries["t (delay s)"].get())
                        self.fc         = float(spoof_entries["fc (Hz)"].get())
                    except ValueError:
                        status_var.set("Invalid parameters")
                        return
                self.is_attacking = True
                status_var.set(f"Running: {mode}")

            def on_stop():
                self.is_attacking = False
                status_var.set("Stopped")

            ctrl = tk.Frame(root)
            ctrl.place(relx=0.08, rely=0.88, anchor="w")
            tk.Button(ctrl, text="Start", width=8, bg="#4caf50", fg="white",
                      font=("Helvetica", 11), command=on_start).pack(side="left", padx=(0, 10))
            tk.Button(ctrl, text="Stop",  width=8, bg="#f44336", fg="white",
                      font=("Helvetica", 11), command=on_stop).pack(side="left")

            tk.Label(root, textvariable=status_var, font=("Helvetica", 10), fg="#555").place(
                relx=0.08, rely=0.95, anchor="w")

            root.mainloop()

        threading.Thread(target=run, daemon=True).start()

    # ------------------------------------------------------------------
    # Create BPS to direct the noise
    # ------------------------------------------------------------------

    def _build_taps(self):
        """Build a complex bandpass FIR filter for [start_freq, end_freq]."""
        # Clamp to 95% of Nyquist so transition band never exceeds samp_rate/2
        half = self._samp_rate / 2.0 * 0.95
        low  = max(self.freq_start, -half)
        high = min(self.freq_end,    half)
        if high <= low:
            high = low + 1.0

        bandwidth     = high - low
        transition_bw = max(bandwidth * 0.1, self._samp_rate * 0.01)

        taps = firdes.complex_band_pass(
            gain=1.0,
            sampling_freq=self._samp_rate,
            low_cutoff_freq=low,
            high_cutoff_freq=high,
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
        out[:] = np.zeros(np.size(out))
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

    def Follow_attack(self, in0, out):
        n = len(in0)

        # Accumulate input samples
        space_left = self.total_samples - self.sample_count
        to_copy    = min(n, space_left)
        self.accumulated[self.sample_count:self.sample_count + to_copy] = in0[:to_copy]
        self.sample_count += to_copy

        # Output jam noise on known frequency while accumulating
        if self.jam_freq is not None:
            out[:] = self._follow_bandlimited_noise(self.jam_freq, n)
        else:
            out[:] = np.zeros(n, dtype=np.complex64)

        # Not enough samples yet
        if self.sample_count < self.total_samples:
            return n

        # Enough samples: run FFT and find peak
        win        = np.blackman(self.total_samples)
        fft_result = np.fft.fftshift(np.fft.fft(self.accumulated * win))
        power_db   = 20 * np.log10(np.abs(fft_result) + 1e-12)
        freqs      = np.fft.fftshift(np.fft.fftfreq(self.total_samples, 1.0 / self.fs))

        mean_db      = np.mean(power_db)
        peak_indices = np.where(power_db > (mean_db + self.threshold_db))[0]

        if len(peak_indices) > 0:
            highest_idx  = peak_indices[np.argmax(power_db[peak_indices])]
            self.jam_freq = freqs[highest_idx]
            print(f"[Follow] Jamming {self.jam_freq/1e3:.3f} kHz | "
                  f"{power_db[highest_idx]:.1f} dB | "
                  f"{power_db[highest_idx] - mean_db:.1f} dB above mean")
        else:
            self.jam_freq = None

        self.sample_count = 0
        return n

    def _follow_bandlimited_noise(self, center_freq, num_samples):
        noise = (
            np.random.normal(0, self.amplitude, num_samples) +
            1j * np.random.normal(0, self.amplitude, num_samples)
        ).astype(np.complex64)

        cutoff = np.clip((self.bandwidth / 2) / (self.fs / 2), 0.01, 0.99)
        taps   = firwin(101, cutoff)
        noise  = lfilter(taps, 1.0, noise).astype(np.complex64)

        t      = np.arange(num_samples) / self.fs
        noise *= np.exp(1j * 2 * np.pi * center_freq * t).astype(np.complex64)
        return noise

    def Spoof_attack(self, in0, out):
        out_len = len(out[:])

        for i in range(out_len):
            if len(self.samples_queue) > 0:
                out[i] = self.samples_queue.popleft()
            else:
                out[i] = 0
        
        return len(out)
    
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
    
    def add_msg_to_queue(self):
        noise = self._follow_bandlimited_noise(self.fc, 2 * self.timeout * self.fs).tolist()
        preamble = self.preamble.tolist()
        msg = self.enqueue_from_string(self.msg, self.fs, self.t).tolist() 
        self.samples_queue.extend(noise + preamble + msg)
