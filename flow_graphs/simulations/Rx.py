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
from PyQt5 import QtCore
from gnuradio import blocks
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
import math



class Rx(gr.top_block, Qt.QWidget):

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

        self.settings = Qt.QSettings("GNU Radio", "Rx")

        try:
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
        except BaseException as exc:
            print(f"Qt GUI: Could not restore geometry: {str(exc)}", file=sys.stderr)

        ##################################################
        # Variables
        ##################################################
        self.t = t = 0.05
        self.samp_rate = samp_rate = int(50e3)
        self.center_freq = center_freq = 434e6
        self.Tx_gain = Tx_gain = 20
        self.Rx_gain = Rx_gain = 20
        self.Attacker_gain = Attacker_gain = 30

        ##################################################
        # Blocks
        ##################################################

        self._center_freq_range = qtgui.Range(433.990e6, 434.01e6, 1e3, 434e6, 200)
        self._center_freq_win = qtgui.RangeWidget(self._center_freq_range, self.set_center_freq, "'center_freq'", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._center_freq_win)
        self._Tx_gain_range = qtgui.Range(0, 50, 1, 20, 200)
        self._Tx_gain_win = qtgui.RangeWidget(self._Tx_gain_range, self.set_Tx_gain, "'Tx_gain'", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._Tx_gain_win)
        self.uhd_usrp_sink_0 = uhd.usrp_sink(
            ",".join(("", '')),
            uhd.stream_args(
                cpu_format="fc32",
                args='',
                channels=list(range(0,1)),
            ),
            "",
        )
        self.uhd_usrp_sink_0.set_samp_rate(samp_rate)
        self.uhd_usrp_sink_0.set_time_unknown_pps(uhd.time_spec(0))

        self.uhd_usrp_sink_0.set_center_freq(center_freq, 0)
        self.uhd_usrp_sink_0.set_antenna("TX/RX", 0)
        self.uhd_usrp_sink_0.set_gain(Tx_gain, 0)
        self.low_pass_filter_0_0 = filter.interp_fir_filter_fff(
            1,
            firdes.low_pass(
                1,
                samp_rate,
                5e3,
                1e3,
                window.WIN_HAMMING,
                6.76))
        self.jammer_mod_source_str2samp_0 = jammer.mod_source_str2samp(t, samp_rate, 'hello')
        self.hilbert_fc_1 = filter.hilbert_fc(6500, window.WIN_HAMMING, 6.76)
        self.blocks_vco_f_0_0 = blocks.vco_f(samp_rate, (2*math.pi*1e3), 1)
        self.blocks_add_const_vxx_1_0_0 = blocks.add_const_ff(2)
        self._Rx_gain_range = qtgui.Range(0, 20, 1, 20, 200)
        self._Rx_gain_win = qtgui.RangeWidget(self._Rx_gain_range, self.set_Rx_gain, "'Rx_gain'", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._Rx_gain_win)
        self._Attacker_gain_range = qtgui.Range(0, 50, 1, 30, 200)
        self._Attacker_gain_win = qtgui.RangeWidget(self._Attacker_gain_range, self.set_Attacker_gain, "'Attacker_gain'", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._Attacker_gain_win)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.blocks_add_const_vxx_1_0_0, 0), (self.blocks_vco_f_0_0, 0))
        self.connect((self.blocks_vco_f_0_0, 0), (self.low_pass_filter_0_0, 0))
        self.connect((self.hilbert_fc_1, 0), (self.uhd_usrp_sink_0, 0))
        self.connect((self.jammer_mod_source_str2samp_0, 0), (self.blocks_add_const_vxx_1_0_0, 0))
        self.connect((self.low_pass_filter_0_0, 0), (self.hilbert_fc_1, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("GNU Radio", "Rx")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_t(self):
        return self.t

    def set_t(self, t):
        self.t = t

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.low_pass_filter_0_0.set_taps(firdes.low_pass(1, self.samp_rate, 5e3, 1e3, window.WIN_HAMMING, 6.76))
        self.uhd_usrp_sink_0.set_samp_rate(self.samp_rate)

    def get_center_freq(self):
        return self.center_freq

    def set_center_freq(self, center_freq):
        self.center_freq = center_freq
        self.uhd_usrp_sink_0.set_center_freq(self.center_freq, 0)

    def get_Tx_gain(self):
        return self.Tx_gain

    def set_Tx_gain(self, Tx_gain):
        self.Tx_gain = Tx_gain
        self.uhd_usrp_sink_0.set_gain(self.Tx_gain, 0)

    def get_Rx_gain(self):
        return self.Rx_gain

    def set_Rx_gain(self, Rx_gain):
        self.Rx_gain = Rx_gain

    def get_Attacker_gain(self):
        return self.Attacker_gain

    def set_Attacker_gain(self, Attacker_gain):
        self.Attacker_gain = Attacker_gain




def main(top_block_cls=Rx, options=None):

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
