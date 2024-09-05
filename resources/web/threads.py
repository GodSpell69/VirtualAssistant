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
#from bardapi import Bard
import pyttsx3
from transformers import GPT2LMHeadModel, GPT2Tokenizer

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
    THRESHOLD = 150
    CHUNK_SIZE = 1024
    FORMAT = pyaudio.paInt16
    RATE = 44100
    my_flag = False
    model_name = "gpt2"
    tokenizer = GPT2Tokenizer.from_pretrained(model_name)
    model = GPT2LMHeadModel.from_pretrained(model_name)
    def __init__(self, *args, **kwargs):
        super(Recorder, self).__init__()
        '''
        self.slyme = SlymeDriver(pfname='Default')
        time.sleep(5)
        self.slyme.select_latest_chat()
        time.sleep(5)
        '''
        #os.environ['_BARD_API_KEY']="ZwhR1jSkN5dW2PDfqV9zY4MqwIuurobcBNkTHi8fsg6GLB1t_iiOMcLNq2jPO2q023-qoQ."
        self.engine = pyttsx3.init()
        self.args = args
        self.kwargs = kwargs
    # language  : en_US, ...
    # gender    : VoiceGenderFemale, VoiceGenderMale
    def change_voice(self):
        voices = self.engine.getProperty('voices')
        self.engine.setProperty('voice', voices[1].id)
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
        Save = False

        r = array('h')

        while 1:

            # little endian, signed short
            snd_data = array('h', stream.read(self.CHUNK_SIZE))
            if byteorder == 'big':
                snd_data.byteswap()
            r.extend(snd_data)

            silent = self.is_silent(snd_data)

            '''Silence while Not Recording'''
            if silent and not snd_started:
                num_silent += 1

            '''Separate Silent Streams and Don't Save it'''
            if num_silent > 1000:
                num_silent = 0
                break

            '''Spoken and Start Recording'''
            if not silent and not snd_started:
                print("Started recording")
                num_silent = 0
                snd_started = True

            '''Silence while Recording'''
            if silent and snd_started:
                num_silent += 1

            '''Silent for long while Recording so Finish recording'''
            if snd_started and num_silent > 300:
                print("Record has ended")
                num_silent = 0
                Save = True
                break

        if Save:
            sample_width = p.get_sample_size(FORMAT)
            stream.stop_stream()
            stream.close()
            p.terminate()

            r = self.normalize(r)
            r = self.trim(r)
            r = self.add_silence(r, 0.5)

            return sample_width, r
        else:
            stream.stop_stream()
            stream.close()
            p.terminate()
            return (0,0)
    #Zero
    def record_to_file(self):
        "Records from the microphone and outputs the resulting data to 'path'"
        print(1)
        while self.my_flag == False:
            time.sleep(1)
        sample_width, data = self.record()

        if (sample_width, data) == (0,0):
            self.record_to_file()

        else:
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
                recorded_phrase = r.recognize_google(audio,language='en-US')

            except sr.UnknownValueError:
                recorded_phrase = "Not understood"

        if "man" in recorded_phrase:
            print(recorded_phrase)
            self.phrase.emit(recorded_phrase)
            self.generate_answer(recorded_phrase)
        else:
            os.remove(filename)

        self.record_to_file()
    #Sétimo
    def generate_answer(self, question):
        # Tokenizar a pergunta e converter para tensores
        input_ids = self.tokenizer.encode(question, return_tensors="pt")
        # Gerar resposta usando o modelo GPT-2
        output = self.model.generate(input_ids, max_length=2000, num_return_sequences=1, no_repeat_ngram_size=1, early_stopping=False)

        # Decodificar a resposta gerada
        answer = self.tokenizer.decode(output[0], skip_special_tokens=True)
        print(answer)
        self.change_voice()
        self.speak(answer)
    #Oitavo
    def speak(self, answer):
        self.engine.setProperty('rate', 200)
        self.engine.say(answer)
        self.engine.runAndWait()
        self.engine.stop()
    '''
    def answer(self, recorded_phrase):
        print("Gerando resposta...")
        #result = Bard().get_answer(recorded_phrase)['content']
        #print(result)
        self.speak(result)
    #Oitavo
    def speak(self, answer):
        self.engine.setProperty('rate', 200)
        self.engine.say(answer)
        self.engine.runAndWait()
        self.engine.stop()
    '''

class ProcessingData(QThread):
    data_of_x_and_y = pyqtSignal(np.ndarray, np.ndarray)

    def __init__(self, *args, **kwargs):
        super(ProcessingData, self).__init__()
        self.args = args
        self.kwargs = kwargs
        self.traces = dict()

    def Update(self):
        self.x = np.arange(0, 2 * CHUNK, 2)

        self.activate = True
        while True:

            self.wf_data = stream.read(CHUNK)
            self.wf_data = struct.unpack(str(2 * CHUNK) + 'B', self.wf_data)
            self.wf_data = np.array(self.wf_data, dtype='b') [::2] + 128
            if self.activate:
                self.data_of_x_and_y.emit(self.x, self.wf_data)

    def Stop(self):
        self.activate = False

'''
class Question_Answering(QThread):
    phrase = pyqtSignal(str)
    model_name = "gpt2"
    tokenizer = GPT2Tokenizer.from_pretrained(model_name)
    model = GPT2LMHeadModel.from_pretrained(model_name)

    def __init__(self, *args, **kwargs):
        super(Question_Answering, self).__init__()

        self.engine = pyttsx3.init()
        self.args = args
        self.kwargs = kwargs

    def generate_answer(self, question):
        # Tokenizar a pergunta e converter para tensores
        input_ids = self.tokenizer.encode(question, return_tensors="pt")
        # Gerar resposta usando o modelo GPT-2
        output = self.model.generate(input_ids, max_length=2000, num_return_sequences=1, no_repeat_ngram_size=1, early_stopping=True)

        # Decodificar a resposta gerada
        answer = self.tokenizer.decode(output[0], skip_special_tokens=True)
        print(answer)
        self.speak(answer)

    def speak(self, answer):
        self.engine.setProperty('rate', 200)
        self.engine.say(answer)
        self.engine.runAndWait()
        self.engine.stop()

'''