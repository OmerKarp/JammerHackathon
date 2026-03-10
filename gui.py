import tkinter as tk
import threading
import time
import numpy as np
from gnuradio import gr, blocks
from gnuradio.jammer import barrage
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

root = tk.Tk()
root.title("Smart Jammer")
root.geometry("1000x800")

selected_mode = tk.StringVar(value="")
tb        = None   # active top block
running   = False  # jammer active flag
scanning  = False  # spectrum update flag (independent of running)

MODES = ["Barrage", "Mode 2", "Mode 3"]
CIRCLE_R        = 12
SELECTED_COLOR  = "#2196F3"
UNSELECTED_COLOR = "#ffffff"
OUTLINE_COLOR   = "#555555"
N_SAMPLES       = 8192  # FFT size per update

circles = {}

# ------------------------------------------------------------------
# Flowgraph — finite burst: collects N_SAMPLES then stops
# ------------------------------------------------------------------

class BarrageFlowgraph(gr.top_block):
    def __init__(self, start_freq, end_freq, amplitude, samp_rate):
        gr.top_block.__init__(self, "Barrage Jammer")
        self.samp_rate = samp_rate
        self.src  = barrage(start_freq, end_freq, amplitude, samp_rate)
        self.head = blocks.head(gr.sizeof_gr_complex, N_SAMPLES)
        self.vsink = blocks.vector_sink_c()
        self.connect(self.src, self.head, self.vsink)

    def get_samples(self):
        return np.array(self.vsink.data())

# ------------------------------------------------------------------
# Spectrum plot (right side of window)
# ------------------------------------------------------------------

fig = Figure(figsize=(5.5, 4), dpi=100)
ax  = fig.add_subplot(111)
ax.set_title("Spectrum")
ax.set_xlabel("Frequency (Hz)")
ax.set_ylabel("Power (dB)")
ax.set_facecolor("#111")
fig.patch.set_facecolor("#1e1e1e")
ax.tick_params(colors="white")
ax.title.set_color("white")
ax.xaxis.label.set_color("white")
ax.yaxis.label.set_color("white")
for spine in ax.spines.values():
    spine.set_edgecolor("#555")
line, = ax.plot([], [], color="#2196F3", linewidth=1)

plot_canvas = FigureCanvasTkAgg(fig, master=root)
plot_canvas.get_tk_widget().place(relx=0.35, rely=0.5, anchor="w", width=580, height=400)

# ------------------------------------------------------------------
# Callbacks
# ------------------------------------------------------------------

def select_mode(mode):
    global scanning
    selected_mode.set(mode)
    for m, cid in circles.items():
        color = SELECTED_COLOR if m == mode else UNSELECTED_COLOR
        canvas.itemconfig(cid, fill=color)
    if mode == "Barrage":
        param_frame.place(relx=0.08, rely=0.62, anchor="w")
        if not scanning:
            scanning = True
            threading.Thread(target=scan_thread, daemon=True).start()
    else:
        scanning = False
        param_frame.place_forget()

def on_start():
    global running
    mode = selected_mode.get()
    if not mode or running:
        return

    if mode == "Barrage":
        running = True
        status_var.set("Running: Barrage")

def scan_thread():
    """Background thread: repeatedly collects samples and schedules plot update."""
    global tb, scanning

    while scanning:
        try:
            samp_rate  = float(entry_samp_rate.get())
            start_freq = float(entry_start_freq.get())
            end_freq   = float(entry_end_freq.get())
            amplitude  = float(entry_amplitude.get())
        except ValueError:
            time.sleep(0.2)
            continue

        if running:
            tb = BarrageFlowgraph(start_freq, end_freq, amplitude, samp_rate)
            tb.run()
            samples = tb.get_samples()
        else:
            # barrage off — plot silence
            samples = np.zeros(N_SAMPLES, dtype=np.complex64)
            time.sleep(0.2)

        if scanning:
            root.after(0, lambda s=samples, sr=samp_rate: plot_samples(s, sr))

def plot_samples(samples, samp_rate):
    N     = len(samples)
    fft   = np.fft.fftshift(np.fft.fft(samples * np.hanning(N)))
    psd   = 20 * np.log10(np.abs(fft) / N + 1e-12)
    freqs = np.fft.fftshift(np.fft.fftfreq(N, 1.0 / samp_rate))

    line.set_xdata(freqs)
    line.set_ydata(psd)
    ax.set_xlim(freqs[0], freqs[-1])
    ax.set_ylim(psd.min() - 5, psd.max() + 5)
    plot_canvas.draw()

def on_stop():
    global running
    running = False
    selected_mode.set("")
    for cid in circles.values():
        canvas.itemconfig(cid, fill=UNSELECTED_COLOR)
    status_var.set("Stopped — spectrum still scanning.")

# ------------------------------------------------------------------
# Radio selectors
# ------------------------------------------------------------------

radio_frame = tk.Frame(root)
radio_frame.place(relx=0.08, rely=0.45, anchor="w")

canvas = tk.Canvas(radio_frame, bg=root.cget("bg"), highlightthickness=0)
canvas.pack()

row_h = 40
pad_x = 10
label_offset = 30
canvas_w = 160
canvas_h = row_h * len(MODES)
canvas.config(width=canvas_w, height=canvas_h)

for i, mode in enumerate(MODES):
    cy = i * row_h + row_h // 2
    cx = pad_x + CIRCLE_R
    cid = canvas.create_oval(
        cx - CIRCLE_R, cy - CIRCLE_R, cx + CIRCLE_R, cy + CIRCLE_R,
        fill=UNSELECTED_COLOR, outline=OUTLINE_COLOR, width=2
    )
    circles[mode] = cid
    canvas.create_text(cx + label_offset, cy, text=mode, anchor="w",
                       font=("Helvetica", 13))
    canvas.tag_bind(cid, "<Button-1>", lambda _, m=mode: select_mode(m))

# ------------------------------------------------------------------
# Barrage parameters
# ------------------------------------------------------------------

param_frame = tk.Frame(root)  # shown/hidden by select_mode

params = [
    ("Start Freq (Hz)",  "start_freq",  "-16000"),
    ("End Freq (Hz)",    "end_freq",    "16000"),
    ("Amplitude",        "amplitude",   "1.0"),
    ("Sample Rate (Hz)", "samp_rate",   "32000"),
]

entry_widgets = {}
for row, (label, key, default) in enumerate(params):
    tk.Label(param_frame, text=label, font=("Helvetica", 10), width=16, anchor="w").grid(
        row=row, column=0, pady=2)
    e = tk.Entry(param_frame, width=12, font=("Helvetica", 10))
    e.insert(0, default)
    e.grid(row=row, column=1, padx=(6, 0), pady=2)
    entry_widgets[key] = e

entry_start_freq = entry_widgets["start_freq"]
entry_end_freq   = entry_widgets["end_freq"]
entry_amplitude  = entry_widgets["amplitude"]
entry_samp_rate  = entry_widgets["samp_rate"]

# ------------------------------------------------------------------
# Start / Stop
# ------------------------------------------------------------------

control_frame = tk.Frame(root)
control_frame.place(relx=0.08, rely=0.85, anchor="w")

tk.Button(control_frame, text="Start", width=8, height=1,
          bg="#4caf50", fg="white", font=("Helvetica", 12),
          command=on_start).pack(side="left", padx=(0, 10))

tk.Button(control_frame, text="Stop", width=8, height=1,
          bg="#f44336", fg="white", font=("Helvetica", 12),
          command=on_stop).pack(side="left")

# ------------------------------------------------------------------
# Status label
# ------------------------------------------------------------------

status_var = tk.StringVar(value="")
tk.Label(root, textvariable=status_var, font=("Helvetica", 10), fg="#555").place(
    relx=0.08, rely=0.91, anchor="w")

root.mainloop()
