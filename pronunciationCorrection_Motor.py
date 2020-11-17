
# The code for changing pages was derived from: http://stackoverflow.com/questions/7546050/switch-between-two-frames-in-tkinter
# License: http://creativecommons.org/licenses/by-sa/3.0/
# 하나의 윈도우 창에서 스위칭 하는 코드
# 필요 콘텐츠 화면
# 왼쪽                                                오른쪽
# |홈/1레벨1/2레벨/3레벨 버튼   ||                         |
# |이미지                       || 맞음/틀림 이미지        |
# |이미지설명 텍스트            || 현재 점수 텍스트         |
# |소리/녹음/녹음멈춤 버튼      || 전이미지/다음이미지 버튼 |

# 2020-10-18
# 기존의 녹음 파일에 대해서 wav 파일이 아닌 raw pcm 으로 녹음하도록 변경

# 2020-10-19
# 페이지 1은 거의 다 완성한듯 보임
# 1. 문장에 맞는 이미지를 넣는 것
# 2. 페이지 2 및 3 만들기
import tkinter as tk

#녹음
import threading
import pyaudio
import wave

#mp3 파일 재생
import pygame, mutagen.mp3

#이미지
from PIL import ImageTk, Image, ImageDraw

#레벨 별 문장
from sentences import sentence_level1
from sentences import sentence_level2
from sentences import sentence_level3

#pcm 녹음 coding: utf-8
import sounddevice as sd

##-발음 교정 api 사용
import urllib3
import json
import base64

#api response string to dict
from typing import Dict

from procor import proCorrect

# Motor Code
import RPi.GPIO as GPIO
import time

GPIO.setwarnings(False)
pin1 = 17
pin =18
GPIO.setmode(GPIO.BCM)
GPIO.setup(pin, GPIO.OUT)
GPIO.setup(pin1, GPIO.OUT)
p= GPIO.PWM(pin, 50)  #PMW
p1 = GPIO.PWM(pin1,50)
p.start(0)
p1.start(0)

class Main(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        container = tk.Frame(self)
        self.config(background="red")

        container.pack(side="top", fill="both", expand = True)

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        for F in (StartPage, PageOne, PageTwo,PageThree):
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")
            #배경색
            frame.config(bg="MistyRose")
        self.show_frame(StartPage)

    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()

    def test(self):
        print("this is test")


class StartPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self,parent)

        label = tk.Label(self, text="Select Your level")
        label.place(x=50, y=20, width=100, height=50)

        button = tk.Button(self, text="Level 1",command=lambda: controller.show_frame(PageOne))
        button.place(x=50, y=100, width=100, height=50)

        button2 = tk.Button(self, text="Level 2",command=lambda: controller.show_frame(PageTwo))
        button2.place(x=50, y=200, width=100, height=50)

        button3 = tk.Button(self, text="Level 3",command=lambda: controller.show_frame(PageThree))
        button3.place(x=50, y=300, width=100, height=50)

#Level1
class PageOne(tk.Frame):

    def __init__(self, parent, controller):
        #전역변수
        global qImage_name #Quest 이미지
        global imgLabel #Quest 이미지에 대한 라벨
        global questionText #Quest 설명에 대한 라벨
        global pronunciationText #발음 평가 점수에 대한 라벨


        #Quest 이미지
        qImage_name = 0
        qImageLevel = "level//level1//image//"
        qImageDir = qImageLevel+str(qImage_name)+".jpg"



        #Result 이미지
        rImage_name = "base"
        rImageLevel = "image//"
        rImageDir = rImageLevel+str(rImage_name)+".jpg"

        #질문 문장 배열 quest sentence
        qSentence1 = sentence_level1

        pronunciation = 0
        strPronunciation = "Your pronunciation score is "+str(pronunciation)


        #콘텐츠
        tk.Frame.__init__(self, parent)
        self.isrecording = False

        label = tk.Label(self, text="Page One!!!")
        label.place(x=100, y=0, width=100, height=30)

        button1 = tk.Button(self, text="Back to Home",command=lambda: controller.show_frame(StartPage))
        button1.place(x=0, y=0, width=100, height=30)

        button2 = tk.Button(self, text="Page Two",command=lambda: controller.show_frame(PageTwo))
        button2.place(x=200, y=0, width=100, height=30)

        button3 = tk.Button(self, text="Page Three",command=lambda: controller.show_frame(PageThree))
        button3.place(x=300, y=0, width=100, height=30)

        #퀘스트 이미지
        load = Image.open(qImageDir)
        load = load.resize((350, 250))
        render = ImageTk.PhotoImage(load)
        imgLabel = tk.Label(self, image=render)
        imgLabel.image = render
        imgLabel.place(x=25, y=45)

        #설명
        questionText=tk.Text(self)
        questionText.insert(tk.CURRENT, qSentence1[0])
        ##아래 두줄 모두 중앙 정렬을 위해 필요하다.
        questionText.tag_configure("center", justify='center')
        questionText.tag_add("center", "1.0", "end")
        questionText.place(x=27, y=300, width=350, height=30)

        #음성 재생 lambda 없으면 가장 먼저 실행 후 죽어버림
        button4=tk.Button(self, text="voice",command=self.voice)
        button4.place(x=50, y=360, width=100, height=50)

        #Record 녹음
        button5 = tk.Button(self, text='rec',command=self.startrecording)
        button5.place(x=150, y=360, width=100, height=50)
        button6 = tk.Button(self, text='Go!',command=self.pronunciationC)
        button6.place(x=250, y=360, width=100, height=50)

        #############################################################

        #Result 이미지
        rLoad = Image.open(rImageDir)
        rLoad = rLoad.resize((350, 200))
        rRender = ImageTk.PhotoImage(rLoad)
        rlmg = tk.Label(self, image=rRender)
        rlmg.image = rRender
        rlmg.place(x=425, y=75)

        #발음 평가 점수 Text 창
        pronunciationText = tk.Text(self)
        pronunciationText.insert(tk.CURRENT, strPronunciation)
        ##아래 두줄 모두 중앙 정렬을 위해 필요하다.
        pronunciationText.tag_configure("center", justify='center')
        pronunciationText.tag_add("center", "1.0", "end")
        pronunciationText.place(x=427, y=300, width=350, height=30)

        #이전 버튼
        button7 = tk.Button(self, text='Prev',command=self.prevB)
        button7.place(x=500, y=360, width=75, height=50)
        #다음 버튼
        button8 = tk.Button(self, text='Next',command=self.nextB)
        button8.place(x=625, y=360, width=75, height=50)


    def startrecording(self):
        #녹음
        duration = 5
        fs = 16000
        rec = sd.rec(duration * fs, samplerate=fs, channels=1, dtype='int16')
        sd.wait()
        pcm = rec.tostring()
        with open('audio/test.raw', 'wb') as w:
            w.write(pcm)

    def pronunciationC(self):
        #발음교정
        getText = questionText.get("1.0", "end")
        script = str(getText)
        # \n 안 지워주면 result -500 에러
        script = script.rstrip("\n")
        #이미지 경로
        winImg = "image//win.jpg"
        loseImg = "image//lose.jpg"
        imgDir = "image//win.jpg"

        result = proCorrect(script)
        pronunciationText.delete(1.0,"end")
        pronunciationText.insert(1.0, "Your pronunciation score is "+ str(result))
        pronunciationText.tag_configure("center", justify='center')
        pronunciationText.tag_add("center", "1.0", "end")

        if result > 3:
            imgDir = "image//win.jpg"
            p1.ChangeDutyCycle(12.5)
            p.ChangeDutyCycle(12.5)  # MAX
            time.sleep(1)
            p1.ChangeDutyCycle(2.5)
            p.ChangeDutyCycle(2.5)  # MIN
            time.sleep(1)
            #p1.stop()
            #p.stop()

        else:
            imgDir = "image//lose.jpg"

        self.rLoad = Image.open(imgDir)
        self.rLoad = self.rLoad.resize((350, 200))
        self.rRender = ImageTk.PhotoImage(self.rLoad)
        rlmg = tk.Label(self, image=self.rRender)
        rlmg.image = self.rRender
        rlmg.place(x=425, y=75)

    def voice(self):
        # mp3 파일 재생
        global qImage_name
        voice_name= qImage_name
        mp3level = "level//level1//audio//"
        mp3Name = mp3level+str(voice_name)+".mp3"

        sound_dir = mp3Name
        self.playmusic(sound_dir)

    def playmusic(self,mp3Name):
        pygame.init()

        bitsize = -16   # signed 16 bit. support 8,-8,16,-16
        channels = 1    # 1 is mono, 2 is stereo
        buffer = 2048   # number of samples (experiment to get right sound)
        mp3 = mutagen.mp3.MP3(mp3Name)
        frequency=mp3.info.sample_rate

        pygame.mixer.init()
        clock= pygame.time.Clock()
        pygame.mixer.music.load(mp3Name)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            clock.tick(1000)

    def prevB(self):
        print("preb")
        global qImage_name
        global imgLabel
        global questionText

        qImage_name = qImage_name -1
        if qImage_name < 0:
            qImage_name = 0

        #이미지
        num = qImage_name
        qImageLevel = "level//level1//image//"
        qImageDir = qImageLevel+str(num)+".jpg"

        imgDir = "image//base.jpg"

        self.load = Image.open(qImageDir)
        self.load = self.load.resize((350, 250))
        self.render = ImageTk.PhotoImage(self.load)
        imgLabel = tk.Label(self, image=self.render)
        imgLabel.image = self.render
        imgLabel.place(x=25, y=45)

        #설명
        qSentence1 = sentence_level1
        questionText.delete(1.0,"end")
        questionText.insert(1.0, qSentence1[num])
        questionText.tag_configure("center", justify='center')
        questionText.tag_add("center", "1.0", "end")

        #스코어 디폴트 이미지
        self.rLoad = Image.open(imgDir)
        self.rLoad = self.rLoad.resize((350, 200))
        self.rRender = ImageTk.PhotoImage(self.rLoad)
        rlmg = tk.Label(self, image=self.rRender)
        rlmg.image = self.rRender
        rlmg.place(x=425, y=75)

    def nextB(self):
        print("nextb")
        global qImage_name
        global imgLabel
        global questionText

        qImage_name = qImage_name +1

        #이미지 테스트일 때만 1로 맞추자
        #원래는 4
        if qImage_name > 4:
            qImage_name = 4

        num = qImage_name
        qImageLevel = "level//level1//image//"
        qImageDir = qImageLevel+str(num)+".jpg"

        imgDir = "image//base.jpg"

        self.load = Image.open(qImageDir)
        self.load = self.load.resize((350, 250))
        self.render = ImageTk.PhotoImage(self.load)
        imgLabel = tk.Label(self, image=self.render)
        imgLabel.image = self.render
        imgLabel.place(x=25, y=45)

        #설명
        qSentence1 = sentence_level1
        questionText.delete(1.0,"end")
        questionText.insert(1.0, qSentence1[num])
        questionText.tag_configure("center", justify='center')
        questionText.tag_add("center", "1.0", "end")

        #스코어 디폴트 이미지
        self.rLoad = Image.open(imgDir)
        self.rLoad = self.rLoad.resize((350, 200))
        self.rRender = ImageTk.PhotoImage(self.rLoad)
        rlmg = tk.Label(self, image=self.rRender)
        rlmg.image = self.rRender
        rlmg.place(x=425, y=75)

#level2
class PageTwo(tk.Frame):

    def __init__(self, parent, controller):
        #전역변수
        global qImage_name2 #Quest 이미지
        global imgLabel2 #Quest 이미지에 대한 라벨
        global questionText2 #Quest 설명에 대한 라벨
        global pronunciationText2 #발음 평가 점수에 대한 라벨


        #Quest 이미지
        qImage_name2 = 0
        qImageLevel = "level//level2//image//"
        qImageDir = qImageLevel+str(qImage_name2)+".jpg"



        #Result 이미지
        rImage_name = "base"
        rImageLevel = "image//"
        rImageDir = rImageLevel+str(rImage_name)+".jpg"

        #질문 문장 배열 quest sentence
        qSentence2 = sentence_level2

        pronunciation = 0
        strPronunciation = "Your pronunciation score is "+str(pronunciation)


        #콘텐츠
        tk.Frame.__init__(self, parent)

        button1 = tk.Button(self, text="Back to Home",command=lambda: controller.show_frame(StartPage))
        button1.place(x=0, y=0, width=100, height=30)

        button2 = tk.Button(self, text="Page One",command=lambda: controller.show_frame(PageOne))
        button2.place(x=100, y=0, width=100, height=30)

        label = tk.Label(self, text="Page Two!!!")
        label.place(x=200, y=0, width=100, height=30)

        button3 = tk.Button(self, text="Page Three",command=lambda: controller.show_frame(PageThree))
        button3.place(x=300, y=0, width=100, height=30)

        #퀘스트 이미지
        load = Image.open(qImageDir)
        load = load.resize((350, 250))
        render = ImageTk.PhotoImage(load)
        imgLabel2 = tk.Label(self, image=render)
        imgLabel2.image = render
        imgLabel2.place(x=25, y=45)

        #설명
        questionText2=tk.Text(self)
        questionText2.insert(tk.CURRENT, qSentence2[0])
        ##아래 두줄 모두 중앙 정렬을 위해 필요하다.
        questionText2.tag_configure("center", justify='center')
        questionText2.tag_add("center", "1.0", "end")
        questionText2.place(x=27, y=300, width=350, height=30)

        #음성 재생 lambda 없으면 가장 먼저 실행 후 죽어버림
        button4=tk.Button(self, text="voice",command=self.voice)
        button4.place(x=50, y=360, width=100, height=50)

        #Record 녹음
        button5 = tk.Button(self, text='rec',command=self.startrecording)
        button5.place(x=150, y=360, width=100, height=50)
        button6 = tk.Button(self, text='Go!',command=self.pronunciationC)
        button6.place(x=250, y=360, width=100, height=50)

        #############################################################

        #Result 이미지
        rLoad = Image.open(rImageDir)
        rLoad = rLoad.resize((350, 200))
        rRender = ImageTk.PhotoImage(rLoad)
        rlmg = tk.Label(self, image=rRender)
        rlmg.image = rRender
        rlmg.place(x=425, y=75)

        #발음 평가 점수 Text 창
        pronunciationText2 = tk.Text(self)
        pronunciationText2.insert(tk.CURRENT, strPronunciation)
        ##아래 두줄 모두 중앙 정렬을 위해 필요하다.
        pronunciationText2.tag_configure("center", justify='center')
        pronunciationText2.tag_add("center", "1.0", "end")
        pronunciationText2.place(x=427, y=300, width=350, height=30)

        #이전 버튼
        button7 = tk.Button(self, text='Prev',command=self.prevB)
        button7.place(x=500, y=360, width=75, height=50)
        #다음 버튼
        button8 = tk.Button(self, text='Next',command=self.nextB)
        button8.place(x=625, y=360, width=75, height=50)


    def startrecording(self):
        #녹음
        duration = 5
        fs = 16000
        rec = sd.rec(duration * fs, samplerate=fs, channels=1, dtype='int16')
        sd.wait()
        pcm = rec.tostring()
        with open('audio/test.raw', 'wb') as w:
            w.write(pcm)

    def pronunciationC(self):
        #발음교정
        getText = questionText2.get("1.0", "end")
        script = str(getText)
        # \n 안 지워주면 result -500 에러
        script = script.rstrip("\n")
        #이미지 경로
        winImg = "image//win.jpg"
        loseImg = "image//lose.jpg"
        imgDir = "image//win.jpg"

        result = proCorrect(script)
        pronunciationText2.delete(1.0,"end")
        pronunciationText2.insert(1.0, "Your pronunciation score is "+ str(result))
        pronunciationText2.tag_configure("center", justify='center')
        pronunciationText2.tag_add("center", "1.0", "end")
        # Add Motor Control Code
        if result > 3:
            imgDir = "image//win.jpg"

            p1.ChangeDutyCycle(12.5)
            p.ChangeDutyCycle(12.5)  # MAX
            time.sleep(1)
            p1.ChangeDutyCycle(2.5)
            p.ChangeDutyCycle(2.5)  # MIN
            time.sleep(1)
        else:
            imgDir = "image//lose.jpg"

        self.rLoad = Image.open(imgDir)
        self.rLoad = self.rLoad.resize((350, 200))
        self.rRender = ImageTk.PhotoImage(self.rLoad)
        rlmg = tk.Label(self, image=self.rRender)
        rlmg.image = self.rRender
        rlmg.place(x=425, y=75)

    def voice(self):
        # mp3 파일 재생
        global qImage_name2
        voice_name= qImage_name2
        mp3level = "level//level2//audio//"
        mp3Name = mp3level+str(voice_name)+".mp3"

        sound_dir = mp3Name
        self.playmusic(sound_dir)

    def playmusic(self,mp3Name):
        pygame.init()

        bitsize = -16   # signed 16 bit. support 8,-8,16,-16
        channels = 1    # 1 is mono, 2 is stereo
        buffer = 2048   # number of samples (experiment to get right sound)
        mp3 = mutagen.mp3.MP3(mp3Name)
        frequency=mp3.info.sample_rate

        pygame.mixer.init()
        clock= pygame.time.Clock()
        pygame.mixer.music.load(mp3Name)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            clock.tick(1000)

    def prevB(self):
        print("preb")
        global qImage_name2
        global imgLabel2
        global questionText2

        qImage_name2 = qImage_name2 -1
        if qImage_name2 < 0:
            qImage_name2 = 0

        #이미지
        num = qImage_name2
        qImageLevel = "level//level2//image//"
        qImageDir = qImageLevel+str(num)+".jpg"

        imgDir = "image//base.jpg"

        self.load = Image.open(qImageDir)
        self.load = self.load.resize((350, 250))
        self.render = ImageTk.PhotoImage(self.load)
        imgLabel2 = tk.Label(self, image=self.render)
        imgLabel2.image = self.render
        imgLabel2.place(x=25, y=45)

        #설명
        qSentence2 = sentence_level2
        questionText2.delete(1.0,"end")
        questionText2.insert(1.0, qSentence2[num])
        questionText2.tag_configure("center", justify='center')
        questionText2.tag_add("center", "1.0", "end")

        #스코어 디폴트 이미지
        self.rLoad = Image.open(imgDir)
        self.rLoad = self.rLoad.resize((350, 200))
        self.rRender = ImageTk.PhotoImage(self.rLoad)
        rlmg = tk.Label(self, image=self.rRender)
        rlmg.image = self.rRender
        rlmg.place(x=425, y=75)

    def nextB(self):
        print("nextb")
        global qImage_name2
        global imgLabel2
        global questionText2

        qImage_name2 = qImage_name2 +1

        #이미지 테스트일 때만 1로 맞추자
        #원래는 4
        if qImage_name2 > 4:
            qImage_name2 = 4

        num = qImage_name2
        qImageLevel = "level//level2//image//"
        qImageDir = qImageLevel+str(num)+".jpg"

        imgDir = "image//base.jpg"

        self.load = Image.open(qImageDir)
        self.load = self.load.resize((350, 250))
        self.render = ImageTk.PhotoImage(self.load)
        imgLabel2 = tk.Label(self, image=self.render)
        imgLabel2.image = self.render
        imgLabel2.place(x=25, y=45)

        #설명
        qSentence2 = sentence_level2
        questionText2.delete(1.0,"end")
        questionText2.insert(1.0, qSentence2[num])
        questionText2.tag_configure("center", justify='center')
        questionText2.tag_add("center", "1.0", "end")

        #스코어 디폴트 이미지
        self.rLoad = Image.open(imgDir)
        self.rLoad = self.rLoad.resize((350, 200))
        self.rRender = ImageTk.PhotoImage(self.rLoad)
        rlmg = tk.Label(self, image=self.rRender)
        rlmg.image = self.rRender
        rlmg.place(x=425, y=75)

#level3
class PageThree(tk.Frame):

    def __init__(self, parent, controller):
        #전역변수
        global qImage_name3 #Quest 이미지
        global imgLabel3 #Quest 이미지에 대한 라벨
        global questionText3 #Quest 설명에 대한 라벨
        global pronunciationText3 #발음 평가 점수에 대한 라벨


        #Quest 이미지
        qImage_name3 = 0
        qImageLevel = "level//level3//image//"
        qImageDir = qImageLevel+str(qImage_name3)+".jpg"


        #Result 이미지
        rImage_name = "base"
        rImageLevel = "image//"
        rImageDir = rImageLevel+str(rImage_name)+".jpg"

        #질문 문장 배열 quest sentence
        qSentence3 = sentence_level3

        pronunciation = 0
        strPronunciation = "Your pronunciation score is "+str(pronunciation)


        #콘텐츠
        tk.Frame.__init__(self, parent)

        button1 = tk.Button(self, text="Back to Home",command=lambda: controller.show_frame(StartPage))
        button1.place(x=0, y=0, width=100, height=30)

        button2 = tk.Button(self, text="Page One",command=lambda: controller.show_frame(PageOne))
        button2.place(x=100, y=0, width=100, height=30)

        button3 = tk.Button(self, text="Page Two",command=lambda: controller.show_frame(PageTwo))
        button3.place(x=200, y=0, width=100, height=30)

        label = tk.Label(self, text="Page Three!!!")
        label.place(x=300, y=0, width=100, height=30)

        #퀘스트 이미지
        load = Image.open(qImageDir)
        load = load.resize((350, 250))
        render = ImageTk.PhotoImage(load)
        imgLabel3 = tk.Label(self, image=render)
        imgLabel3.image = render
        imgLabel3.place(x=25, y=45)

        #설명
        questionText3=tk.Text(self)
        questionText3.insert(tk.CURRENT, qSentence3[0])
        ##아래 두줄 모두 중앙 정렬을 위해 필요하다.
        questionText3.tag_configure("center", justify='center')
        questionText3.tag_add("center", "1.0", "end")
        questionText3.place(x=27, y=300, width=350, height=30)

        #음성 재생 lambda 없으면 가장 먼저 실행 후 죽어버림
        button4=tk.Button(self, text="voice",command=self.voice)
        button4.place(x=50, y=360, width=100, height=50)

        #Record 녹음
        button5 = tk.Button(self, text='rec',command=self.startrecording)
        button5.place(x=150, y=360, width=100, height=50)
        button6 = tk.Button(self, text='Go!',command=self.pronunciationC)
        button6.place(x=250, y=360, width=100, height=50)

        #############################################################

        #Result 이미지
        rLoad = Image.open(rImageDir)
        rLoad = rLoad.resize((350, 200))
        rRender = ImageTk.PhotoImage(rLoad)
        rlmg = tk.Label(self, image=rRender)
        rlmg.image = rRender
        rlmg.place(x=425, y=75)

        #발음 평가 점수 Text 창
        pronunciationText3 = tk.Text(self)
        pronunciationText3.insert(tk.CURRENT, strPronunciation)
        ##아래 두줄 모두 중앙 정렬을 위해 필요하다.
        pronunciationText3.tag_configure("center", justify='center')
        pronunciationText3.tag_add("center", "1.0", "end")
        pronunciationText3.place(x=427, y=300, width=350, height=30)

        #이전 버튼
        button7 = tk.Button(self, text='Prev',command=self.prevB)
        button7.place(x=500, y=360, width=75, height=50)
        #다음 버튼
        button8 = tk.Button(self, text='Next',command=self.nextB)
        button8.place(x=625, y=360, width=75, height=50)


    def startrecording(self):
        #녹음
        duration = 5
        fs = 16000
        rec = sd.rec(duration * fs, samplerate=fs, channels=1, dtype='int16')
        sd.wait()
        pcm = rec.tostring()
        with open('audio/test.raw', 'wb') as w:
            w.write(pcm)

    def pronunciationC(self):
        #발음교정
        getText = questionText3.get("1.0", "end")
        script = str(getText)
        # \n 안 지워주면 result -500 에러
        script = script.rstrip("\n")
        #이미지 경로
        winImg = "image//win.jpg"
        loseImg = "image//lose.jpg"
        imgDir = "image//win.jpg"

        result = proCorrect(script)
        pronunciationText3.delete(1.0,"end")
        pronunciationText3.insert(1.0, "Your pronunciation score is "+ str(result))
        pronunciationText3.tag_configure("center", justify='center')
        pronunciationText3.tag_add("center", "1.0", "end")

        # Motor Control Code Add First
        if result > 3:
            imgDir = "image//win.jpg"

            # Add Code
            p1.ChangeDutyCycle(12.5)
            p.ChangeDutyCycle(12.5)  # MAX
            time.sleep(1)
            p1.ChangeDutyCycle(2.5)
            p.ChangeDutyCycle(2.5)  # MIN
            time.sleep(1)

        else:
            imgDir = "image//lose.jpg"

        self.rLoad = Image.open(imgDir)
        self.rLoad = self.rLoad.resize((350, 200))
        self.rRender = ImageTk.PhotoImage(self.rLoad)
        rlmg = tk.Label(self, image=self.rRender)
        rlmg.image = self.rRender
        rlmg.place(x=425, y=75)

    def voice(self):
        # mp3 파일 재생
        global qImage_name3
        voice_name= qImage_name3
        mp3level = "level//level3//audio//"
        mp3Name = mp3level+str(voice_name)+".mp3"

        sound_dir = mp3Name
        self.playmusic(sound_dir)

    def playmusic(self,mp3Name):
        pygame.init()

        bitsize = -16   # signed 16 bit. support 8,-8,16,-16
        channels = 1    # 1 is mono, 2 is stereo
        buffer = 2048   # number of samples (experiment to get right sound)
        mp3 = mutagen.mp3.MP3(mp3Name)
        frequency=mp3.info.sample_rate

        pygame.mixer.init()
        clock= pygame.time.Clock()
        pygame.mixer.music.load(mp3Name)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            clock.tick(1000)

    def prevB(self):
        print("preb")
        global qImage_name3
        global imgLabel3
        global questionText3

        qImage_name3 = qImage_name3 -1
        if qImage_name3 < 0:
            qImage_name3 = 0

        #이미지
        num = qImage_name3
        qImageLevel = "level//level3//image//"
        qImageDir = qImageLevel+str(num)+".jpg"

        imgDir = "image//base.jpg"

        self.load = Image.open(qImageDir)
        self.load = self.load.resize((350, 250))
        self.render = ImageTk.PhotoImage(self.load)
        imgLabel3 = tk.Label(self, image=self.render)
        imgLabel3.image = self.render
        imgLabel3.place(x=25, y=45)

        #설명
        qSentence3 = sentence_level3
        questionText3.delete(1.0,"end")
        questionText3.insert(1.0, qSentence3[num])
        questionText3.tag_configure("center", justify='center')
        questionText3.tag_add("center", "1.0", "end")

        #스코어 디폴트 이미지
        self.rLoad = Image.open(imgDir)
        self.rLoad = self.rLoad.resize((350, 200))
        self.rRender = ImageTk.PhotoImage(self.rLoad)
        rlmg = tk.Label(self, image=self.rRender)
        rlmg.image = self.rRender
        rlmg.place(x=425, y=75)

    def nextB(self):
        print("nextb")
        global qImage_name3
        global imgLabel3
        global questionText3

        qImage_name3 = qImage_name3 +1

        #이미지 테스트일 때만 1로 맞추자
        #원래는 4
        if qImage_name3 > 4:
            qImage_name3 = 4

        num = qImage_name3
        qImageLevel = "level//level3//image//"
        qImageDir = qImageLevel+str(num)+".jpg"

        imgDir = "image//base.jpg"

        self.load = Image.open(qImageDir)
        self.load = self.load.resize((350, 250))
        self.render = ImageTk.PhotoImage(self.load)
        imgLabel3 = tk.Label(self, image=self.render)
        imgLabel3.image = self.render
        imgLabel3.place(x=25, y=45)

        #설명
        qSentence3 = sentence_level3
        questionText3.delete(1.0,"end")
        questionText3.insert(1.0, qSentence3[num])
        questionText3.tag_configure("center", justify='center')
        questionText3.tag_add("center", "1.0", "end")

        #스코어 디폴트 이미지
        self.rLoad = Image.open(imgDir)
        self.rLoad = self.rLoad.resize((350, 200))
        self.rRender = ImageTk.PhotoImage(self.rLoad)
        rlmg = tk.Label(self, image=self.rRender)
        rlmg.image = self.rRender
        rlmg.place(x=425, y=75)

def main():
    app = Main()
    #윈도우 크기
    app.geometry('800x420')
    app.resizable(width=0, height=0)
    #창 이름
    app.title("TuringBot")
    #ESC 키
    app.bind("<Escape>", lambda e: app.destroy())
    app.mainloop()

if __name__ == '__main__':
    main()
    GPIO.cleanup()
