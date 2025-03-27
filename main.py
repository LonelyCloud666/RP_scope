import tkinter as tk
from gui import App
from ADC import start_adc_task
from collections import deque
import threading
import time
from data_proces import DataProcessor
import numpy as np # type: ignore

data_processor = DataProcessor()

history_len = 200

shared_data = [deque(maxlen=history_len) for _ in range(6)]

bufor = [[] for _ in range(6)]
normalized_data = [[] for _ in range(6)]
ch_time = [[] for _ in range(4)]
sine_wave_data = [(np.zeros(history_len), (0, 0, 0)) for _ in range(4)]
sine_wave_data_temp = [(np.zeros(history_len), (0, 0, 0)) for _ in range(4)]
running = True

sin_time = np.arange(0, 0.031, 0.0005)

def normalize_data():
    global normalized_data, sine_wave_data, sine_wave_data_temp
    local_data = shared_data.copy()
    while running:
        bufor[0] = [x * data_processor.ch_zoom[0] for x in data_processor.voltage_calc(local_data[0])]  # Ch0
        bufor[1] = [x * data_processor.ch_zoom[1] for x in data_processor.voltage_calc(local_data[1])]  # Ch1
        bufor[2] = [x * data_processor.ch_zoom[2] for x in data_processor.voltage_calc(local_data[2])]  # Ch2
        bufor[3] = [x * data_processor.ch_zoom[3] for x in data_processor.voltage_calc(local_data[3])]  # Ch3
        bufor[4] = data_processor.time_normalize(local_data[4])  # time
        bufor[5] = data_processor.freq_calc(bufor[4])
        
        if bufor[5] > 400:

            for i in range(4):
                offset = data_processor.calculate_offset(bufor[i])
                bufor[i] = data_processor.subtract_offset(bufor[i], offset)
            
            phase_offset = data_processor.phase_offset

            main_channel = data_processor.main_channel
            sine_wave_data_temp[0] = data_processor.predict_sine_wave(bufor[4], bufor[main_channel])
            amplitude_ch_main, frequency_ch_main, phase_ch_main = sine_wave_data_temp[0][1]

            for i in range(4):
                sine_wave_data_temp[i] = data_processor.predict_sine_wave(bufor[4], bufor[i])
                amplitude, frequency, phase = sine_wave_data_temp[i][1]
                
                phase_diff = phase - (phase_ch_main + (phase_offset[i] - phase_offset[main_channel]))
                phase_diff = (phase_diff + np.pi) % (2 * np.pi) - np.pi
                sine_wave_data_temp[i] = (
                    data_processor.sine_wave(sin_time, amplitude, frequency, phase_diff),
                    (amplitude, frequency, phase_diff)
                )
                data_processor.phase_offset_history[i].append(sine_wave_data_temp[i][1][2])

            try:
                phase_shift_s = (phase_ch_main / (2 * np.pi)) * (1 / frequency_ch_main)
            except ZeroDivisionError:
                phase_shift_s = 0

            bufor[4] = [t + phase_shift_s for t in bufor[4]]

            for i in range(4):
                try:
                    frec_time = 1 / sine_wave_data_temp[i][1][1]
                except ZeroDivisionError:
                    frec_time = 0
                ch_time[i] = [t - frec_time for t in bufor[4]]

            normalized_data = bufor
            sine_wave_data = sine_wave_data_temp

        time.sleep(0.5)

def main():
    global running
    adc_reader = start_adc_task(shared_data)

    time.sleep(1)

    normalization_thread = threading.Thread(target=normalize_data, daemon=True)
    normalization_thread.start()
    time.sleep(1)
    app = App(normalized_data, sine_wave_data, ch_time, data_processor)
    app.mainloop()

    running = False
    normalization_thread.join()
    adc_reader.stop()

if __name__ == "__main__":
    main()
