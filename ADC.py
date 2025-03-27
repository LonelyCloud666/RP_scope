import threading
import time
import ADS1263
import RPi.GPIO as GPIO # type: ignore

REF = 2.5

try:
    ADC = ADS1263.ADS1263()

    if (ADC.ADS1263_init_ADC1('ADS1263_14400SPS') == -1):
        exit()
    ADC.ADS1263_SetMode(1) # 0 is singleChannel, 1 is diffChannel
    time_start = 0
    time_end = 0
    channelList = [0, 1, 2, 3]
except IOError as e:
    print(e)

class ADCReader:
    def __init__(self, data_list):
        self.data_list = data_list
        self.running = True
        self.thread = threading.Thread(target=self.read_adc, daemon=True)

    def start(self):
        self.thread.start()

    def read_adc(self):
        while self.running:
            ADC_Value = ADC.ADS1263_GetAll(channelList)
            for i in channelList:
                self.data_list[i].append(ADC_Value[i])
            self.data_list[4].append(time.time())

    def stop(self):
        self.running = False
        self.thread.join()
        ADC.ADS1263_Exit()

def start_adc_task(data_list):
    adc_reader = ADCReader(data_list)
    adc_reader.start()
    return adc_reader
