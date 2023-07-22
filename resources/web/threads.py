from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import pyaudio
from array import array
from sys import byteorder
import time
import wave
import speech_recognition as sr
import os
import numpy as np
import struct

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024 * 2

p = pyaudio.PyAudio()
stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        output=True,
                        frames_per_buffer=CHUNK)

class Recorder(QThread):
    phrase = pyqtSignal(str)
    THRESHOLD = 310
    CHUNK_SIZE = 1024
    FORMAT = pyaudio.paInt16
    RATE = 44100
    my_flag = False
    def __init__(self, *args, **kwargs):
        super(Recorder, self).__init__()
        self.args = args
        self.kwargs = kwargs
    #Segundo
    def is_silent(self, snd_data):
        "Returns 'True' if below the 'silent' threshold"
        return max(snd_data) < self.THRESHOLD
    #Terceiro
    def normalize(self, snd_data):
        "Average the volume out"
        MAXIMUM = 16384
        times = float(MAXIMUM)/max(abs(i) for i in snd_data)

        r = array('h')
        for i in snd_data:
            r.append(int(i*times))
        return r
    #Quarto
    def trim(self, snd_data):
        "Trim the blank spots at the start and end"

        def _trim(snd_data):
            snd_started = False
            r = array('h')

            for i in snd_data:
                if not snd_started and abs(i) > self.THRESHOLD:
                    snd_started = True
                    r.append(i)

                elif snd_started:
                    r.append(i)
            return r

        # Trim to the left
        snd_data = _trim(snd_data)

        # Trim to the right
        snd_data.reverse()
        snd_data = _trim(snd_data)
        snd_data.reverse()
        return snd_data
    #Quinto
    def add_silence(self, snd_data, seconds):
        "Add silence to the start and end of 'snd_data' of length 'seconds' (float)"
        silence = [0] * int(seconds * self.RATE)
        r = array('h', silence)
        r.extend(snd_data)
        r.extend(silence)
        return r
    #Primeiro
    def record(self):
        """
        Record a word or words from the microphone and 
        return the data as an array of signed shorts.

        Normalizes the audio, trims silence from the 
        start and end, and pads with 0.5 seconds of 
        blank sound to make sure VLC et al can play 
        it without getting chopped off.
        """
        p = pyaudio.PyAudio()
        stream = p.open(format=self.FORMAT, channels=1, rate=self.RATE,
            input=True, output=True,
            frames_per_buffer=self.CHUNK_SIZE)

        num_silent = 0
        snd_started = False

        r = array('h')

        while 1:

            # little endian, signed short
            snd_data = array('h', stream.read(self.CHUNK_SIZE))
            if byteorder == 'big':
                snd_data.byteswap()
            r.extend(snd_data)

            silent = self.is_silent(snd_data)

            if silent and snd_started:
                num_silent += 1
            elif not silent and not snd_started:
                #print("Started recording")
                snd_started = True

            if snd_started and num_silent > 300:
                #print("Record has ended")
                break

        sample_width = p.get_sample_size(FORMAT)
        stream.stop_stream()
        stream.close()
        p.terminate()

        r = self.normalize(r)
        r = self.trim(r)
        r = self.add_silence(r, 0.5)

        return sample_width, r
    #Zero
    def record_to_file(self):
        "Records from the microphone and outputs the resulting data to 'path'"
        while self.my_flag == False:
            time.sleep(1)
        sample_width, data = self.record()

        f_name_directory = r'D:\Gab\prog\Nicole_project\resources\audios'

        n_files = len(os.listdir(f_name_directory))

        filename = os.path.join(f_name_directory, '{}.wav'.format(n_files))

        wf = wave.open(filename, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(sample_width)
        wf.setframerate(RATE)
        wf.writeframes(data)
        wf.close()
        #print('Written to file: {}'.format(filename))
        #print(filename)

        self.recognition(filename)
    #Sexto
    def recognition(self, filename):

        r = sr.Recognizer()

        recorded_phrase = ""

        with sr.AudioFile(filename) as source:

            r.adjust_for_ambient_noise(source, 1)

            #Armazena o que foi dito numa variavel
            audio = r.listen(source)

            try:
                recorded_phrase = r.recognize_google(audio,language='pt-BR')

            except sr.UnknownValueError:
                recorded_phrase = "Not understood"

        if "mano" in recorded_phrase:
            self.phrase.emit(recorded_phrase)
        else:
            os.remove(filename)

        self.record_to_file()
class ProcessingData(QThread):
    data_of_x_and_y = pyqtSignal(np.ndarray, np.ndarray)

    def __init__(self, *args, **kwargs):
        super(ProcessingData, self).__init__()
        self.args = args
        self.kwargs = kwargs
        self.traces = dict()

    def Update(self):
        self.x = np.arange(0, 2 * CHUNK, 2)

        while True:

            self.wf_data = stream.read(CHUNK)
            self.wf_data = struct.unpack(str(2 * CHUNK) + 'B', self.wf_data)
            self.wf_data = np.array(self.wf_data, dtype='b') [::2] + 128
            self.data_of_x_and_y.emit(self.x, self.wf_data)