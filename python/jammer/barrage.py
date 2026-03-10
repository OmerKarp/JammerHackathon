import numpy as np
from gnuradio import gr, filter
from gnuradio.filter import firdes
from gnuradio.fft import window

class barrage(gr.sync_block):
    """
    Barrage Jammer Source Block
    Generates band-limited noise between start_freq and end_freq
    with the specified output amplitude.
    """

    def __init__(self, start_freq, end_freq, amplitude, samp_rate):
        gr.sync_block.__init__(
            self,
            name="barrage",
            in_sig=None,
            out_sig=[np.complex64]
        )

        # Validate inputs
        assert end_freq > start_freq, "end_freq must be greater than start_freq"
        assert abs(start_freq) <= samp_rate / 2, "start_freq out of Nyquist range"
        assert abs(end_freq)   <= samp_rate / 2, "end_freq out of Nyquist range"
        assert amplitude > 0, "amplitude must be positive"

        self._samp_rate  = samp_rate
        self._amplitude  = amplitude
        self._start_freq = start_freq
        self._end_freq   = end_freq

        # Compute bandpass filter taps
        self._taps = self._build_taps()

        # Internal filter state (overlap-save buffer)
        self._filter_state = np.zeros(len(self._taps) - 1, dtype=np.complex64)


    # ------------------------------------------------------------------
    # Create BPS to direct the noise
    # ------------------------------------------------------------------

    def _build_taps(self):
        """Build a complex bandpass FIR filter for [start_freq, end_freq]."""
        bandwidth    = self._end_freq - self._start_freq
        transition_bw = max(bandwidth * 0.1, 1e3)   # 10% of BW, min 1 kHz

        taps = firdes.complex_band_pass(
            gain=1.0,
            sampling_freq=self._samp_rate,
            low_cutoff_freq=self._start_freq,
            high_cutoff_freq=self._end_freq,
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
    # GNU Radio work function
    # ------------------------------------------------------------------

    def work(self, input_items, output_items):
        out = output_items[0]
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
