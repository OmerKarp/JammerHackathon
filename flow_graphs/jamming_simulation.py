#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: Not titled yet
# GNU Radio version: 3.10.9.2

from PyQt5 import Qt
from gnuradio import qtgui
from gnuradio import analog
from gnuradio import blocks
import math
from gnuradio import filter
from gnuradio.filter import firdes
from gnuradio import gr
from gnuradio.fft import window
import sys
import signal
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from gnuradio import jammer
from gnuradio import uhd
import time
import sip



class jamming_simulation(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "Not titled yet", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("Not titled yet")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except BaseException as exc:
            print(f"Qt GUI: Could not set Icon: {str(exc)}", file=sys.stderr)
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("GNU Radio", "jamming_simulation")

        try:
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
        except BaseException as exc:
            print(f"Qt GUI: Could not restore geometry: {str(exc)}", file=sys.stderr)

        ##################################################
        # Variables
        ##################################################
        self.t = t = 0.01
        self.start_freq = start_freq = 431e6
        self.samp_rate = samp_rate = int(100e3)
        self.end_freq = end_freq = 436e6
        self.center_freq = center_freq = 434e6

        ##################################################
        # Blocks
        ##################################################

        self.uhd_usrp_source_0 = uhd.usrp_source(
            ",".join(("", '')),
            uhd.stream_args(
                cpu_format="fc32",
                args='',
                channels=list(range(0,1)),
            ),
        )
        self.uhd_usrp_source_0.set_samp_rate(samp_rate)
        self.uhd_usrp_source_0.set_time_unknown_pps(uhd.time_spec(0))

        self.uhd_usrp_source_0.set_center_freq(center_freq, 0)
        self.uhd_usrp_source_0.set_antenna("RX2", 0)
        self.uhd_usrp_source_0.set_gain(20, 0)
        self.uhd_usrp_sink_0_1 = uhd.usrp_sink(
            ",".join(("", '')),
            uhd.stream_args(
                cpu_format="fc32",
                args='',
                channels=list(range(0,1)),
            ),
            "",
        )
        self.uhd_usrp_sink_0_1.set_samp_rate(samp_rate)
        self.uhd_usrp_sink_0_1.set_time_unknown_pps(uhd.time_spec(0))

        self.uhd_usrp_sink_0_1.set_center_freq(center_freq, 0)
        self.uhd_usrp_sink_0_1.set_antenna("TX/RX", 0)
        self.uhd_usrp_sink_0_1.set_gain(10, 0)
        self.qtgui_waterfall_sink_x_0_0_1_0 = qtgui.waterfall_sink_c(
            2048, #size
            window.WIN_BLACKMAN_hARRIS, #wintype
            0, #fc
            (samp_rate/10), #bw
            "Rx", #name
            1, #number of inputs
            None # parent
        )
        self.qtgui_waterfall_sink_x_0_0_1_0.set_update_time(0.10)
        self.qtgui_waterfall_sink_x_0_0_1_0.enable_grid(False)
        self.qtgui_waterfall_sink_x_0_0_1_0.enable_axis_labels(True)



        labels = ['', '', '', '', '',
                  '', '', '', '', '']
        colors = [0, 0, 0, 0, 0,
                  0, 0, 0, 0, 0]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
                  1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_waterfall_sink_x_0_0_1_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_waterfall_sink_x_0_0_1_0.set_line_label(i, labels[i])
            self.qtgui_waterfall_sink_x_0_0_1_0.set_color_map(i, colors[i])
            self.qtgui_waterfall_sink_x_0_0_1_0.set_line_alpha(i, alphas[i])

        self.qtgui_waterfall_sink_x_0_0_1_0.set_intensity_range(-140, 10)

        self._qtgui_waterfall_sink_x_0_0_1_0_win = sip.wrapinstance(self.qtgui_waterfall_sink_x_0_0_1_0.qwidget(), Qt.QWidget)

        self.top_layout.addWidget(self._qtgui_waterfall_sink_x_0_0_1_0_win)
        self.low_pass_filter_0_0_0 = filter.interp_fir_filter_fff(
            1,
            firdes.low_pass(
                1,
                samp_rate,
                5e3,
                1e3,
                window.WIN_HAMMING,
                6.76))
        self.low_pass_filter_0 = filter.fir_filter_ccf(
            1,
            firdes.low_pass(
                1,
                samp_rate,
                5e3,
                1e3,
                window.WIN_HAMMING,
                6.76))
        self.jammer_mod_source_str2samp_0_0 = jammer.mod_source_str2samp(t, samp_rate, 'hello hello hellow')
        self.jammer_demod_samp2str_0 = jammer.demod_samp2str(t, samp_rate, 1, 0.1)
        self.hilbert_fc_1_0 = filter.hilbert_fc(6500, window.WIN_HAMMING, 6.76)
        self.blocks_vco_f_0_0_0 = blocks.vco_f(samp_rate, (2*math.pi*1e3), 1)
        self.blocks_throttle2_1_0_0 = blocks.throttle( gr.sizeof_float*1, samp_rate, True, 0 if "auto" == "auto" else max( int(float(0.1) * samp_rate) if "auto" == "time" else int(0.1), 1) )
        self.blocks_freqshift_cc_0 = blocks.rotator_cc(2.0*math.pi*(-2e3)/samp_rate)
        self.blocks_add_const_vxx_1_0_0_0 = blocks.add_const_ff(2)
        self.analog_fm_demod_cf_1 = analog.fm_demod_cf(
        	channel_rate=samp_rate,
        	audio_decim=1,
        	deviation=1e3,
        	audio_pass=5000,
        	audio_stop=6000,
        	gain=1.0,
        	tau=(75e-6),
        )


        ##################################################
        # Connections
        ##################################################
        self.connect((self.analog_fm_demod_cf_1, 0), (self.jammer_demod_samp2str_0, 0))
        self.connect((self.blocks_add_const_vxx_1_0_0_0, 0), (self.blocks_throttle2_1_0_0, 0))
        self.connect((self.blocks_freqshift_cc_0, 0), (self.low_pass_filter_0, 0))
        self.connect((self.blocks_throttle2_1_0_0, 0), (self.blocks_vco_f_0_0_0, 0))
        self.connect((self.blocks_vco_f_0_0_0, 0), (self.low_pass_filter_0_0_0, 0))
        self.connect((self.hilbert_fc_1_0, 0), (self.uhd_usrp_sink_0_1, 0))
        self.connect((self.jammer_mod_source_str2samp_0_0, 0), (self.blocks_add_const_vxx_1_0_0_0, 0))
        self.connect((self.low_pass_filter_0, 0), (self.analog_fm_demod_cf_1, 0))
        self.connect((self.low_pass_filter_0, 0), (self.qtgui_waterfall_sink_x_0_0_1_0, 0))
        self.connect((self.low_pass_filter_0_0_0, 0), (self.hilbert_fc_1_0, 0))
        self.connect((self.uhd_usrp_source_0, 0), (self.blocks_freqshift_cc_0, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("GNU Radio", "jamming_simulation")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_t(self):
        return self.t

    def set_t(self, t):
        self.t = t

    def get_start_freq(self):
        return self.start_freq

    def set_start_freq(self, start_freq):
        self.start_freq = start_freq

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.blocks_freqshift_cc_0.set_phase_inc(2.0*math.pi*(-2e3)/self.samp_rate)
        self.blocks_throttle2_1_0_0.set_sample_rate(self.samp_rate)
        self.low_pass_filter_0.set_taps(firdes.low_pass(1, self.samp_rate, 5e3, 1e3, window.WIN_HAMMING, 6.76))
        self.low_pass_filter_0_0_0.set_taps(firdes.low_pass(1, self.samp_rate, 5e3, 1e3, window.WIN_HAMMING, 6.76))
        self.qtgui_waterfall_sink_x_0_0_1_0.set_frequency_range(0, (self.samp_rate/10))
        self.uhd_usrp_sink_0_1.set_samp_rate(self.samp_rate)
        self.uhd_usrp_source_0.set_samp_rate(self.samp_rate)

    def get_end_freq(self):
        return self.end_freq

    def set_end_freq(self, end_freq):
        self.end_freq = end_freq

    def get_center_freq(self):
        return self.center_freq

    def set_center_freq(self, center_freq):
        self.center_freq = center_freq
        self.uhd_usrp_sink_0_1.set_center_freq(self.center_freq, 0)
        self.uhd_usrp_source_0.set_center_freq(self.center_freq, 0)




def main(top_block_cls=jamming_simulation, options=None):

    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls()

    tb.start()

    tb.show()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    timer = Qt.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    qapp.exec_()

if __name__ == '__main__':
    main()
