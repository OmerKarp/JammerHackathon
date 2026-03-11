#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 oron.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy as np
from gnuradio import gr
from scipy.signal import find_peaks

class demod_samp2str(gr.sync_block):
    """
    docstring for block demod_samp2str
    """
    def __init__(self, t=1,fs=1000, voltage=1, timeout = 0.1):
        gr.sync_block.__init__(self,
            name="demod_samp2str",
            in_sig=[np.float32, ],
            out_sig=None)
        
        self.pulse_count_in_symble = 3
        self.char_len = 8
        self.t = t
        self.fs =fs
        self.preamble_value = 1
        self.sample_per_pulse =round(fs*t)
        self.samples_per_symble = self.sample_per_pulse*self.pulse_count_in_symble
        self.samples_per_char = self.samples_per_symble*self.char_len
        self.timeout = timeout
        self.preamble_length = round(fs*t*1)
        self.is_signal = False
        self.bits = np.array([])
        self.remainder = np.array([])
        self.number_of_noisy_bits = 0

    def work(self, input_items, output_items):
        in0 = input_items[0]

        next_char = np.append(self.bits,self.string_from_enqueue(in0, self.fs, self.t))
        if next_char != None:
            print(next_char[0], end='')

        return len(input_items[0])


    def string_from_enqueue(self,in0,fs, t):
        threshold = 0.8 * self.preamble_length

        full_data = np.concatenate((self.remainder, np.array(in0)))
        self.remainder = np.array([])

        signal_start_idx = None

        #find signal start idx
        if(self.is_signal == False):
            if len(full_data) < self.preamble_length: 
                self.remainder = full_data
                return None
        
            preamble_cor = self.preamble_value*np.ones(self.preamble_length)
            cor = np.correlate(full_data, preamble_cor, "valid")

            peaks,_ = find_peaks(cor, distance=self.samples_per_symble,height=threshold )

            if(len(peaks)==0):
                self.remainder = full_data[-self.preamble_length:]
                return None
            
            idx_max_cor = peaks[0]

            print("found pre")
            signal_start_idx = idx_max_cor + self.preamble_length
            self.is_signal = True
        
        else:
            signal_start_idx = 0

        if signal_start_idx != None:
            start_signal_to_end = full_data[signal_start_idx:]
        else:
            start_signal_to_end = None
            print("no signal")
            return None

        new_remainder_len = len(start_signal_to_end)%(self.samples_per_char)
        self.remainder = start_signal_to_end[-new_remainder_len:] #update remainder

        cropped_data = start_signal_to_end[:-new_remainder_len] #data to go throu for this iteration

        indices = np.arange(0,len(cropped_data), self.sample_per_pulse)

        down_sampled = [((np.mean(cropped_data[i:i+self.sample_per_pulse])>0)*2-1) for i in indices] 

        if len(down_sampled) >= self.char_len*self.pulse_count_in_symble:
            msg = ''
            for i in range(round(len(down_sampled)/(self.char_len*self.pulse_count_in_symble))):
                msg = msg + self.vec2char(down_sampled[i*self.char_len*self.pulse_count_in_symble:(i+1)*self.char_len*self.pulse_count_in_symble])

            return msg
        else:
            return None

    
    
    def vec2char(self,vec):
        mat_bit = np.reshape(vec, (-1,3))
        bit_msg = np.array([], dtype=int)

        for row in mat_bit:
            if self.is_one(row):
                bit_msg = np.append(bit_msg, 1)
            elif self.is_zero(row):
                bit_msg = np.append(bit_msg, 0)
            else:
                self.number_of_noisy_bits += 1
                print(f"(+) not found bit, {self.number_of_noisy_bits} / {np.ceil(self.timeout * self.fs / self.samples_per_symble)}")
                if self.number_of_noisy_bits >= np.ceil(self.timeout * self.fs / self.samples_per_symble):
                    self.number_of_noisy_bits = 0
                    self.is_signal = False
                    print("(+) Searching for a preamble")
                    break

        if len(bit_msg) != 8:
            return ''

        bit_msg = ''.join(map(str,bit_msg))  

        msg = (chr(int(bit_msg,2)))
        return msg


    def is_one(self,row):
        symbol_1 = [1,1,-1]
        return (symbol_1==row.tolist())

        
    def is_zero(self,row):
        symbol_0 = [1,-1,-1]
        return (symbol_0==row.tolist())


    def is_signal_end(self,sig):
        if(np.count_nonzero(sig==0)>=self.timeout*self.fs):
            return True
        else:
            return False
