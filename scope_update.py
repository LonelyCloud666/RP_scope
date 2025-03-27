import numpy as np # type: ignore

class PlotUpdater:
    def __init__(self, fig, ax, data, sine_wave_data, ch_toggle, state, ch_time):
        self.fig = fig
        self.ax = ax
        self.data = data
        self.sine_wave_data = sine_wave_data
        self.ch_toggle = ch_toggle
        self.state = state
        self.ch_time = ch_time
        self.sin_time = np.arange(0, 0.031, 0.0005)

    def update_plot(self, frame):
        local_data = self.data.copy()
        local_ch_time = self.ch_time.copy()
        local_sine_wave_data = self.sine_wave_data.copy()
        self.ax.clear()
        lines = []

        self.ax.set_xlim(0, 0.03)
        self.ax.set_ylim(-1.5, 1.5)
        self.ax.grid(True)
        self.ax.set_xlabel("time (s)")

        for i in range(4):
            if self.ch_toggle[i]:
                try:
                    sine_wave, _ = local_sine_wave_data[i]
                    if self.state == 0:
                        line, = self.ax.plot(self.sin_time, sine_wave, label=f"Ch{i} Sine")
                    elif self.state == 1:
                        line, = self.ax.plot(local_ch_time[i], local_data[i], label=f"Ch{i} Raw")
                    elif self.state == 2:
                        line, = self.ax.plot(self.sin_time, sine_wave, label=f"Ch{i} Sine")
                        lines.append(line)
                        line, = self.ax.plot(local_ch_time[i], local_data[i], 'o', label=f"Ch{i} Raw")
                    lines.append(line)
                except:
                    pass
        if any(self.ch_toggle):
            legend = self.ax.legend()
            lines.append(legend)

        return lines
