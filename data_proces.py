import json
import os
import numpy as np # type: ignore
from scipy.optimize import curve_fit # type: ignore
from scipy.fft import fft, fftfreq # type: ignore
from collections import deque

class DataProcessor:
    def __init__(self):
        self.config_file = "config.json"
        self.load_config()
        self.main_channel = 0
        self.ch_zoom = [1, 1, 1, 1]
        self.phase_offset_history = [deque(maxlen=20) for _ in range(4)]

    def load_config(self):
        if not os.path.exists(self.config_file):
            self.config = {"REF": 3.4, "phase_offset": [0, 0, 0, 0], "unit": ["V", "A", "V", "A"], "ratio": [250, 30, 250, 30]}
            self.save_config()
        else:
            with open(self.config_file, "r") as file:
                self.config = json.load(file)
        self.REF = self.config["REF"]
        self.phase_offset = self.config["phase_offset"]
        self.unit = self.config["unit"]
        self.ratio = self.config["ratio"]

    def save_config(self):
        with open(self.config_file, "w") as file:
            json.dump(self.config, file)

    def update_phase_offset(self, new_phase_offset):
        self.config["phase_offset"] = new_phase_offset
        self.save_config()
        self.phase_offset = new_phase_offset

    def update_unit_ratio(self, unit, ratio):
        self.config["unit"] = unit
        self.config["ratio"] = ratio
        self.save_config()
        self.unit = unit
        self.ratio = ratio

    def voltage_calc(self, ADC_Value):
        tab = []
        for i, x in enumerate(ADC_Value):
            if (x >> 31 == 1):
                tab.append((-1 * (self.REF * 2 - x * self.REF / 0x80000000)))
            else:
                tab.append((x * self.REF / 0x7fffffff))
        return tab

    def time_normalize(self, time_sample):
        first = time_sample[0]
        tab = []
        for x in time_sample:
            tab.append(x - first)
        return tab

    def freq_calc(self, times):
        time_diffs = [times[i + 1] - times[i] for i in range(len(times) - 1)]
        average_time_diff = sum(time_diffs) / len(time_diffs)
        return 1 / average_time_diff

    def sine_wave(self, x, amplitude, frequency, phase):
        x = np.asarray(x)
        return amplitude * np.sin(2 * np.pi * frequency * x + phase)

    def predict_sine_wave(self, times, data):
        if len(times) == 0 or len(data) == 0:
            return np.zeros_like(data), (0, 0, 0)
        
        guess_amplitude = np.std(data) * 2**0.5
        guess_frequency = self.estimate_frequency(times, data)
        guess_phase = 0
        try:
            popt, _ = curve_fit(self.sine_wave, times, data, p0=[guess_amplitude, guess_frequency, guess_phase])
            amplitude, frequency, phase = popt
            if amplitude < 0:
                amplitude = -amplitude
                phase += np.pi
            phase = (phase + np.pi) % (2 * np.pi) - np.pi
            return self.sine_wave(times, amplitude, frequency, phase), (amplitude, frequency, phase)
        except RuntimeError:
            return np.zeros_like(data), (0, 0, 0)

    def calculate_offset(self, data):
        return np.mean(data)

    def subtract_offset(self, data, offset):
        return [d - offset for d in data]

    def estimate_frequency(self, times, data):
        try:
            N = len(data)
            T = (times[-1] - times[0]) / (N - 1)
            
            #FFT
            yf = fft(data)
            xf = fftfreq(N, T)[:N//2]
            idx = np.argmax(np.abs(yf[:N//2]))
            freq = xf[idx]
            
            if 1 <= freq <= 200:
                return freq
            else:
                return 50
        except Exception:
            return 50

    def sync_phase_offset(self):
        while len(self.phase_offset_history[0]) > 10 and np.mean(self.phase_offset_history[0]) != 0:
            pass
        phase_offset_temp = [np.mean(self.phase_offset_history[i]) for i in range(4)]
        self.update_phase_offset(phase_offset_temp)
