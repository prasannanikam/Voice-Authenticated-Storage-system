from tkinter import *
import ctypes,os,sys
from tkinter.tix import *
from PIL import ImageTk, Image
import tkinter.filedialog as filedialog 
import tkinter.messagebox as tkMessageBox
import wave
import time
import steg
import pickle
import pyaudio,sqlite3
import warnings
import numpy as np
from sklearn import preprocessing
from scipy.io.wavfile import read
import python_speech_features as mfcc
from sklearn.mixture import GaussianMixture 
import threading as T
import shutil
from tkinter import ttk
import mysql.connector as msc
from shutil import copyfile
from tkinter import ttk
import threading  # To perform multi threading
import pyjokes

warnings.filterwarnings("ignore")
os.makedirs('testing_set', exist_ok=True)
os.makedirs('training_set', exist_ok=True)
path = 'C:/Users/prasa/OneDrive/Desktop/VoiceVault-main'
ImagePath='./Images/'
D_path = "./Downloads/"
if not os.path.exists(D_path):
    os.mkdir(D_path)
if not os.path.exists(path):
    os.mkdir(path)

mydb = msc.connect(
    host="localhost",
    user="root",
    password="0312",
    database="world",
)

def Database():
    #Function For Database Connectivity
    global cursor #Making conn,cursor a globle variable


    cursor = mydb.cursor()

    table_name = "users"
    cursor.execute(f'''create table IF NOT EXISTS {table_name}(
                            ID int NOT NULL AUTO_INCREMENT,
                            Name varchar(255) NOT NULL,
                            Username varchar(255) NOT NULL,
                            Password varchar(255) NOT NULL,
                            PRIMARY KEY (ID)
                        )''')
    
def create_user_table(table_name="Data"):
        try:
            mycursor = mydb.cursor()

            mycursor.execute(f'''create table IF NOT EXISTS {table_name}(
                                ID int NOT NULL AUTO_INCREMENT,
                                FileName varchar(255) NOT NULL,
                                File LONGBLOB NOT NULL,
                                PRIMARY KEY (ID)
                            )''')
            print(mycursor)
            print("Successfully Table Created.")
        except Exception as e:
            print(e)

def calculate_delta(array):
    rows,cols = array.shape
    print(rows)
    print(cols)
    deltas = np.zeros((rows,20))
    N = 2
    for i in range(rows):
        index = []
        j = 1
        while j <= N:
            if i-j < 0:
              first =0
            else:
              first = i-j
            if i+j > rows-1:
                second = rows-1
            else:
                second = i+j 
            index.append((second,first))
            j+=1
        deltas[i] = ( array[index[0][0]]-array[index[0][1]] + (2 * (array[index[1][0]]-array[index[1][1]])) ) / 10
    return deltas

def extract_features(audio,rate):
       
    mfcc_feature = mfcc.mfcc(audio,rate, 0.025, 0.01,20,nfft = 1200, appendEnergy = True)    
    mfcc_feature = preprocessing.scale(mfcc_feature)
    print(mfcc_feature)
    delta = calculate_delta(mfcc_feature)
    combined = np.hstack((mfcc_feature,delta)) 
    return combined

def train_model():

    source   = './training_set/'   
    dest = "./"
    train_file = "./training_set_addition.txt"        
    file_paths = open(train_file,'r')
    count = 1
    features = np.asarray(())
    for path in file_paths:    
        path = path.strip()   
        
        sr,audio = read(source + path)
        vector   = extract_features(audio,sr)
        
        if features.size == 0:
            features = vector
        else:
            features = np.vstack((features, vector))

        if count == 1:    
            gmm = GaussianMixture(n_components = 6, max_iter = 200, covariance_type='diag',n_init = 3)
            gmm.fit(features)
            
            # dumping the trained gaussian model
            picklefile = path.split("-")[0]+".gmm"
            pickle.dump(gmm,open(dest + picklefile,'wb'))
            features = np.asarray(())
            count = 0
        count = count + 1
        
def voiceverificationlogin():
        #-----------------------------------------------------------------------
        loginwindow = Toplevel()
        loginwindow.title('VoiceVault')
        loginwindow.resizable(0,0)
        NAME = StringVar()
        #-----------------------------------------------------------------------
        user32 = ctypes.windll.user32
        user32.SetProcessDPIAware()
        [w, h] = [user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)]
        lt = [w, h]
        a = str(lt[0]//2-451)
        b= str(lt[1]//2-339)
        loginwindow.geometry("902x678+"+a+"+"+b)
        #-----------------------------------------------------------------------
        img = Image.open(r"images/registerPage.png")
        img = ImageTk.PhotoImage(img)
        panel = Label(loginwindow, image=img)
        panel.pack(side="top", fill="both", expand="yes")
        #-----------------------------------------------------------------------
        def verify():
            n = (NAME.get()).lower()
            if n=='':
               tkMessageBox.showinfo('VoiceVault','All Fields Are Mendatory To Fill')
            else:
                FORMAT = pyaudio.paInt16
                CHANNELS = 1
                RATE = 44100
                CHUNK = 512
                RECORD_SECONDS = 10
                device_index = 2
                audio = pyaudio.PyAudio()

                index = 1    

                stream = audio.open(format=FORMAT, channels=CHANNELS,
                                rate=RATE, input=True,input_device_index = index,
                                frames_per_buffer=CHUNK)

                Recordframes = []
                for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
                    data = stream.read(CHUNK)
                    Recordframes.append(data)
         
                stream.stop_stream()
                stream.close()
                audio.terminate()
                OUTPUT_FILENAME="sample.wav"
                WAVE_OUTPUT_FILENAME=os.path.join("testing_set",OUTPUT_FILENAME)
                trainedfilelist = open("testing_set_addition.txt", 'w')
                trainedfilelist.write(OUTPUT_FILENAME+"\n")
                trainedfilelist.close()
                waveFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
                waveFile.setnchannels(CHANNELS)
                waveFile.setsampwidth(audio.get_sample_size(FORMAT))
                waveFile.setframerate(RATE)
                waveFile.writeframes(b''.join(Recordframes))
                waveFile.close()
                
                source   = "./testing_set/"  
                modelpath = "./"
                test_file = "./testing_set_addition.txt"       
                file_paths = open(test_file,'r')
                 
                gmm_files = [os.path.join(modelpath,fname) for fname in
                              os.listdir(modelpath) if fname.endswith('.gmm')]
                 
                #Load the Gaussian gender Models
                models    = [pickle.load(open(fname,'rb')) for fname in gmm_files]
                speakers   = [fname.split("\\")[-1].split(".gmm")[0] for fname 
                              in gmm_files]
                 
                # Read the test directory and get the list of test audio files 

                for path in file_paths:  
                    path = path.strip()   

                    sr,audio = read(source + path)
                    vector   = extract_features(audio,sr)
                     
                    log_likelihood = np.zeros(len(models)) 
                    
                    for i in range(len(models)):
                        gmm    = models[i]  #checking with each model one by one
                        scores = np.array(gmm.score(vector))
                        log_likelihood[i] = scores.sum()
                     
                    winner = np.argmax(log_likelihood)
                    if n in speakers[winner]:
                        loginwindow.destroy()
                        home(n)
                        
                    else:
     
                        tkMessageBox.showinfo('VoiceVault','Unable To Verify The User')
      

        def verifyv():
                x = T.Thread(target=verifyv)
                x.start()  

        def switchwin4():
                loginwindow.destroy()
                signinmanual()

        def switchwin5():
                loginwindow.destroy()
                register()
        

        photo = (Image.open("images/voiceverificationlogin.png")).resize((300,300))
        img2 = ImageTk.PhotoImage(photo)
        b1 = Button(loginwindow, highlightthickness = 0, bd = 0,bg='white', image = img2,command=verify)
        b1.place(x=80,y=240)
        l1 = Label(loginwindow, text="Name         : ", bg="white",font = ('Arial',13,'bold'), fg="#2a72af")
        l1.place(x=100, y=240)    
        e1 = Entry(loginwindow, textvariable=NAME, bg="#e6f2ff",width = 17,font = ('Arial',13,'bold'), fg="#2a72af")
        e1.place(x=200, y=240)
    
        b2 = Button(loginwindow, text="LOGIN USING VOICE MANUAL METHOD", width="38", fg="#1E1D6C", highlightthickness = 0,relief = FLAT, bd = 0, borderwidth=0,font = ('Arial',9,'bold'), bg="white",activebackground ="white", command=switchwin4)
        b2.place(x=94, y=540)
        b3 = Button(loginwindow, text="REGISTER TO VOICEVAULT", width="40", fg="#1E1D6C", highlightthickness = 0,relief = FLAT, bd = 0, borderwidth=0,font = ('Arial',9,'bold'), bg="white",activebackground ="white", command=switchwin5)
        b3.place(x=85, y=560)
        loginwindow.mainloop()
        
def signinmanual():
        #-----------------------------------------------------------------------
        
        mloginwindow = Toplevel()
        mloginwindow.title('VoiceVault')
        mloginwindow.resizable(0,0)
        #-----------------------------------------------------------------------
        user32 = ctypes.windll.user32
        user32.SetProcessDPIAware()
        [w, h] = [user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)]
        lt = [w, h]
        a = str(lt[0]//2-451)
        b= str(lt[1]//2-339)
        mloginwindow.geometry("902x678+"+a+"+"+b)
        #-----------------------------------------------------------------------
        img = Image.open(r"images/registerPage.png")
        img = ImageTk.PhotoImage(img)
        panel = Label(mloginwindow, image=img)
        panel.pack(side="top", fill="both", expand="yes")
        #-----------------------------------------------------------------------
        EMAIL = StringVar()
        PASSWORD = StringVar()
        def login():
            e,p=EMAIL.get(),PASSWORD.get()
            print(e,p)
            if e=='' or p=='':
                tkMessageBox.showinfo('VoiceVault','All Fields Are Mendatory To Fill')
            elif len(p)<6:
                tkMessageBox.showinfo('VoiceVault','Password Length Must Be Greater Then Six')
                PASSWORD.set('')
            else:
                Database()
                cursor.execute(''' 
                                         SELECT * FROM users 
                                         WHERE(Name = %s and Password = %s)
                                         ''', (e,p))
                verifyLogin =cursor.fetchone()
                try:
                    if(e in verifyLogin and p in verifyLogin):
                        tkMessageBox.showinfo(title="Login info", message="Logged In")
                        mloginwindow.destroy()
                        home(e)
                except:
                     tkMessageBox.showinfo(title="Login info", message="Unable To Login !!!")                 
        #-----------------------------------------------------------------------
        def switchwin1():
            mloginwindow.destroy()
            voiceverificationlogin()
        def switchwin2():
            mloginwindow.destroy()
            register()
        def sysVerify():
            steg.stegano()
        l1 = Label(mloginwindow, text="Name    : ", bg="white",font = ('Arial',13,'bold'), fg="#2a72af")
        l1.place(x=100, y=270)
        l2 = Label(mloginwindow, text="Password : ", bg="white",font = ('Arial',13,'bold'), fg="#2a72af")
        l2.place(x=100, y=320)
        e1 = Entry(mloginwindow, textvariable=EMAIL, bg="#e6f2ff",width = 17,font = ('Arial',13,'bold'), fg="#2a72af")
        e1.place(x=200, y=270)
        e2 = Entry(mloginwindow, textvariable=PASSWORD, bg="#e6f2ff",width = 17,font = ('Arial',13,'bold'), fg="#2a72af",show='*')
        e2.place(x=200, y=320)
        b1 = Button(mloginwindow, text="LOGIN", width="21", bg="#1E1D6C", highlightthickness = 0,relief = FLAT, bd = 1, borderwidth=0,font = ('Arial',15,'bold'), fg="#F5FAFE", command=login)
        b1.place(x=100, y=370)
        b2 = Button(mloginwindow, text="VERIFY SYSTEM", width="38", fg="#1E1D6C", highlightthickness = 0,relief = FLAT, bd = 0, borderwidth=0,font = ('Arial',9,'bold'), bg="white", command=sysVerify)
        b2.place(x=94, y=420)
        b3 = Button(mloginwindow, text="LOGIN USING VOICE VERIFICATION METHOD", width="40", fg="#1E1D6C", highlightthickness = 0,relief = FLAT, bd = 0, borderwidth=0,font = ('Arial',9,'bold'), bg="white", command=switchwin1)
        b3.place(x=94, y=440)
        b3 = Button(mloginwindow, text="NEW TO VOICEVAULT? REGISTER TO VOICEVAULT", width="40", fg="#1E1D6C", highlightthickness = 0,relief = FLAT, bd = 0, borderwidth=0,font = ('Arial',9,'bold'), bg="white", command=switchwin2)
        b3.place(x=94, y=460)
        mloginwindow.mainloop()

def register():
        #-----------------------------------------------------------------------
        regwindow = Toplevel()
        regwindow.title('VoiceVault')
        regwindow.resizable(0,0)
        #-----------------------------------------------------------------------
        user32 = ctypes.windll.user32
        user32.SetProcessDPIAware()
        [w, h] = [user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)]
        lt = [w, h]
        a = str(lt[0]//2-451)
        b= str(lt[1]//2-339)
        regwindow.geometry("902x678+"+a+"+"+b)
        #-----------------------------------------------------------------------
        img = Image.open(r"images/registerPage.png")
        img = ImageTk.PhotoImage(img)
        panel = Label(regwindow, image=img)
        panel.pack(side="top", fill="both", expand="yes")
        #-----------------------------------------------------------------------
        NAME = StringVar()
        EMAIL = StringVar()
        PASSWORD = StringVar()

        #-----------------------------------------------------------------------
        def addv():
            n,e,p=(NAME.get()).lower(),EMAIL.get(),PASSWORD.get()
            fname =  n+'.gmm'
            flist = os.listdir('./')
            if n=='' or e=='' or p=='':
                tkMessageBox.showinfo('VoiceVault','All Fields Are Mendatory To Fill')            
            else:
                Name =n

                FORMAT = pyaudio.paInt16
                CHANNELS = 1
                RATE = 44100
                CHUNK = 512
                RECORD_SECONDS = 10
                device_index = 2
                audio = pyaudio.PyAudio()
        
                index = 1   
                stream = audio.open(format=FORMAT, channels=CHANNELS,
                                rate=RATE, input=True,input_device_index = index,
                                frames_per_buffer=CHUNK)
                b1["text"]="Speak Now"
                b1.config(command=None)
                Recordframes = []
                for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
                    data = stream.read(CHUNK)
                    Recordframes.append(data)
                b1["text"]="Audio Sample Taken"
                
                
                OUTPUT_FILENAME=Name+"-sample"+".wav"
                WAVE_OUTPUT_FILENAME=os.path.join("training_set",OUTPUT_FILENAME)

                trainedfilelist = open("training_set_addition.txt", 'w')
                trainedfilelist.write(OUTPUT_FILENAME+"\n")
                trainedfilelist.close()
                stream.stop_stream()
                stream.close()
                audio.terminate()
                waveFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
                waveFile.setnchannels(CHANNELS)
                waveFile.setsampwidth(audio.get_sample_size(FORMAT))
                waveFile.setframerate(RATE)
                waveFile.writeframes(b''.join(Recordframes))
                waveFile.close()
                train_model()
        #-----------------------------------------------------------------------
        def addvoice():
                x = T.Thread(target=addv)
                x.start()            
        def reg():
            n,e,p=(NAME.get()).lower(),EMAIL.get(),PASSWORD.get()
            fname =  n+'.gmm'
            flist = os.listdir('./')
            if n=='' or e=='' or p=='':
                tkMessageBox.showinfo('VoiceVault','All Fields Are Mendatory To Fill')
            elif '@' not in e or '.' not in e:
                tkMessageBox.showinfo('VoiceVault','Please Enter A Valid Email Address')
                EMAIL.set('')
            elif len(p)<6:
                tkMessageBox.showinfo('VoiceVault','Password Length Must Be Greater Then Six')
                PASSWORD.set('')
            elif fname not in flist:
                 tkMessageBox.showinfo('VoiceVault','Please Add Voice Sample')
            else:
                Database()
                print("---",n,e,p)
                cursor.execute('''INSERT INTO users(Name, Username, Password) VALUES(%s,%s,%s)''' , (n,e,p))
                create_user_table(n)
                mydb.commit()
                tkMessageBox.showinfo('VoiceVault','User Registered Successfully')
                regwindow.destroy()
                voiceverificationlogin()

        

        #-----------------------------------------------------------------------
        def switchwin3():
            regwindow.destroy()
            voiceverificationlogin()

        l1 = Label(regwindow, text="Name         : ", bg="white",font = ('Arial',13,'bold'), fg="#2a72af")
        l1.place(x=100, y=250)    
        l2 = Label(regwindow, text="Email ID    : ", bg="white",font = ('Arial',13,'bold'), fg="#2a72af")
        l2.place(x=100, y=280)
        l3 = Label(regwindow, text="Password : ", bg="white",font = ('Arial',13,'bold'), fg="#2a72af")
        l3.place(x=100, y=310)
        l4=Label(regwindow,text="Read the phrase :",bg="white",font=('Arial',13,'bold'), fg="#2a72af")
        l4.place(x=100,y=340)
        e1 = Entry(regwindow, textvariable=NAME, bg="#e6f2ff",width = 17,font = ('Arial',13,'bold'), fg="#2a72af")
        e1.place(x=200, y=250)
        e2 = Entry(regwindow, textvariable=EMAIL, bg="#e6f2ff",width = 17,font = ('Arial',13,'bold'), fg="#2a72af")
        e2.place(x=200, y=280)
        e3 = Entry(regwindow, textvariable=PASSWORD, bg="#e6f2ff",width = 17,font = ('Arial',13,'bold'), fg="#2a72af")
        e3.place(x=200, y=310)
        
        
        m=pyjokes.get_joke(language="en", category="neutral")
        
        e4 = Label(regwindow, text=m, bg="white",font = ('Arial',13,'bold'), fg="#2a72af")
        e4.place(x=70, y=380)    
        
        
        b1 = Button(regwindow, text="ADD THE VOICE SAMPLE", width="21", bg="#1E1D6C", highlightthickness = 0,relief = FLAT, bd = 1, borderwidth=0,font = ('Arial',15,'bold'), fg="#F5FAFE", command=addvoice)
        b1.place(x=100, y=490)

    
        b2 =  Button(regwindow, text="REGISTER", width="21", bg="#1E1D6C", highlightthickness = 0,relief = FLAT, bd = 1, borderwidth=0,font = ('Arial',15,'bold'), fg="#F5FAFE", command=reg)
        b2.place(x=100, y=530)
        b3 = Button(regwindow, text="ALREADY REGISTERD? LOGIN TO VOICEVAULT", width="38", fg="#1E1D6C", highlightthickness = 0,relief = FLAT, bd = 0, borderwidth=0,font = ('Arial',9,'bold'), bg="white",activebackground ="white", command=switchwin3)
        b3.place(x=94, y=570)
        regwindow.mainloop()


def home(username):
    global table_name
    table_name = username

    def load_key():
        with open(key_file, 'rb') as key_file:
            key = key_file.read()
            print(key)
        return key


    def encrypt(file):
        filename = file.split("/")[-1]
        file_ext = filename.split(".")[-1]
        print(filename)

        if (file_ext == "jpg" or file_ext == "jpeg" or file_ext == "png"):
            path = file
            key = 21
            # open file for reading purpose
            fin = open(path, 'rb')

            # storing image data in variable "image"
            image = fin.read()
            fin.close()

            # converting image into byte array to
            # perform encryption easily on numeric data
            image = bytearray(image)

            # performing XOR operation on each value of bytearray
            for index, values in enumerate(image):
                image[index] = values ^ key

            # opening file for writting purpose
            fin = open("enc_" + filename, 'wb')

            # writing encrypted data in image
            fin.write(image)
            fin.close()
            print('Encryption Done...')

        elif file_ext == "txt":
            f1 = open("enc_" + filename, "w")
            with open(file) as f:
                data = f.read()
                for i in data:
                    sc = 0
                    enc_char = ord(i)
                    if (enc_char % 2 != 0):
                        enc_char += 1
                        sc = 224
                    enc_char = enc_char // 2
                    enc_char = chr(enc_char)
                    if (sc == 0):
                        f1.write(enc_char)
                    else:
                        f1.write(enc_char + chr(sc))

                    print(i, "Encrypt to ", enc_char, ord(enc_char))

            f1.close()
       


    # encrypt("x.txt")

    def decrypt(file):
        
        filename = file.split("/")[-1]
        file_ext = filename.split(".")[-1]

        if (file_ext == "jpg" or file_ext == "jpeg" or file_ext == "png"):

            path = file
            key = 21
            fin = open(path, 'rb')

            # storing image data in variable "image"
            image = fin.read()
            fin.close()

            # converting image into byte array to perform decryption easily on numeric data
            image = bytearray(image)

            # performing XOR operation on each value of bytearray
            for index, values in enumerate(image):
                image[index] = values ^ key

            # opening file for writting purpose
            print(filename)
            fin = open(D_path + "dec_" + filename, 'wb')

            # writing decryption data in image
            fin.write(image)
            fin.close()
            print('Decryption Done...')

        elif file_ext == "txt":
            f1 = open(D_path + "dec_" + filename, "w")

            with open(file) as f:
                data = f.read()
                for i in range(len(data)):
                    enc_char = ord(data[i]) * 2
                    if (ord(data[i]) == 224):
                        continue
                    try:
                        if (ord(data[i + 1]) == 224):
                            enc_char = enc_char - 1
                    except:
                        pass
                    enc_char = chr(enc_char)
                    f1.write(enc_char)
                # print(i,"Decrypt to ",enc_char)
       


    def convertToBinaryData(filename):
        # Convert digital data to binary format
        with open(filename, 'rb') as file:
            binaryData = file.read()
        return binaryData


    def getUrlnName(fileurl):
        all_f = fileurl()

        url = ""
        filename = all_f[-1]

        for i in range(len(all_f)-1):
            url += all_f[i] + '/'

        return url, filename


    def upload_file(fileurl):
        global statusbar
        path, filename = getUrlnName(fileurl)
        print(path)
        print(filename)

        pth = f'{path}/{filename}'
        encrypt(pth)

        file_ext = filename.split('.')[-1]
        filename = "enc_" + filename

        print(filename)

        if (file_ext == "jpg" or file_ext == "png" or file_ext == "jpeg"):
            copyfile(filename, "C:/Users/prasa/OneDrive/Desktop/VoiceVault-main/localdata" + filename)
        
        print('************************************************')
        fileurl = filename
        try:
            mycursor = mydb.cursor()

            file_data = convertToBinaryData(fileurl)

            query = """INSERT INTO """ + table_name + """ (FileName,File) VALUES (%s,%s) """
            values_tuple = (filename, file_data)
            mycursor.execute(query, values_tuple)
            mydb.commit()
            # print(mycursor)
            print("Successfully File Uploaded.")
            tkMessageBox.showinfo("Success", "Successfully Uploaded")
            statusbar['text'] = ''' UPLOADED '''
        except Exception as e:
            print(e)
            tkMessageBox.showwarning("Warning!", e)


    def getImageFile(filename):
        D_path = "Downloads\\"
        print(D_path + filename)
        copyfile("C:/Users/prasa/OneDrive/Desktop/VoiceVault-main/localdata" + filename, D_path + filename)


    def write_file(data, filename):
        # Convert binary data to proper format and write it on Hard Disk
        with open(filename, 'wb') as file:
            file.write(data)


    def download_file(id=None):
        D_path = "./Downloads/"
        try:
            mycursor = mydb.cursor()

            query = """select * from """ + table_name + """ where ID=""" + str(id)

            mycursor.execute(query)
            for i in mycursor:
                print("id : ", i[0])
                print("filename:", i[1])
                # filename = i[i]
                # print('File data:',i[2])

                filename = i[1]
                file_ext = filename.split('.')[-1]

                if (file_ext == "png" or file_ext == "jpg" or file_ext == "jpeg"):
                    getImageFile(filename)
                else:
                    write_file(i[2], D_path + i[1])
                decrypt(D_path + i[1])
                print("\n")

            # print(mycursor)
            print("Successfully Files Saved.")
            tkMessageBox.showinfo("Success", "Successfully Downloaded")
            D_path = "./Downloads/"
            os.remove(D_path + filename)
        except Exception as e:
            print(e)
            tkMessageBox.showwarning("Warning!", e)


    # ----------------------------------------------------------------------
    window = Toplevel()
    window.title('VoiceVault')
    window.resizable(0, 0)
    # -----------------------------------------------------------------------
    user32 = ctypes.windll.user32
    user32.SetProcessDPIAware()
    [w, h] = [user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)]
    lt = [w, h]
    a = str(lt[0] // 2 - 525)
    b = str(lt[1] // 2 - 345)
    window.geometry("1050x640+" + a + "+" + b)
    window.config(bg='#203647')


    # ---------------------------------------------------------------------------
    def upload():
        global filename, statusbar
        canvas = Canvas(window, height=800, width=847, highlightthickness=0, bd=0, bg='#203647')
        canvas.place(x=0, y=0)
        statusbar = Label(canvas, font=("Arial", 16, "italic bold"), background='#12232E', fg='#EEFBFB', width=65, height=1,
                          highlightthickness=0, bd=3)
        statusbar.place(x=0, y=610)
        statusbar["text"] = '''Currently Selected File : None'''

        def browse():
            global filename
            filename = filedialog.askopenfilename(initialdir=os.getcwd(), title="Select file",
                                                  filetypes=(("All Files", "*.*"), ("Text Files", ".txt")))
            f = filename.split('/')[-1]
            lt = list(f)
            c = 0
            x = ''
            for i in lt:
                c += 1
                if c < 40:
                    x += i
                if c == 40:
                    x = x + '...'
                    break
            statusbar["text"] = '''Currently Selected File : ''' + x
            extension = "." + f.split(".")[-1]

            vid_fm = [".flv", ".avi", ".mp4", ".3gp", ".mov", ".webm", ".ogg", ".qt", ".avchd"]
            aud_fm = [".flac", ".mp3", ".wav", ".wma", ".aac"]

            if extension in vid_fm:
                tkMessageBox.showerror(title="Video File!",
                                       message="Free version of this server doesn't allow storing of video file!")
                browse()
            elif extension in aud_fm:
                tkMessageBox.showerror(title="Audio File!",
                                       message="Free version of this server doesn't allow storing of audio file!")
                browse()
            else:
                return filename.split('/')

        heading = Label(window, text="--- Encrypt And Upload File On Server ---", fg="#EEFBFB",
                        font=('Calibiri', 28, 'bold'), bg="#203647")
        heading.place(x=70, y=30)
        subheading = Label(window, text="-:  Browse File :-", fg="#EEFBFB", font=('Calibiri', 18, 'bold'), bg="#203647")
        subheading.place(x=330, y=120)
        imgfile = Image.open(ImagePath+'browse.png')
        imgfile = imgfile.resize((300, 300))
        browse_img = ImageTk.PhotoImage(imgfile)
        panel2 = Button(canvas, image=browse_img, bg="#203647", highlightthickness=0, bd=0, activebackground="#203647",
                        command=browse)
        panel2.image = browse_img
        panel2.place(x=290, y=200)
        b = Button(window, text="Upload File", width=20, bg="#EEFBFB", highlightthickness=0, font=('Calibiri', 24, 'bold'),
                   bd=0, fg="#203647", activebackground="#4DA8DA", command=lambda: upload_file(browse))
        b.place(x=250, y=450)


    def download():
        global flag, id_selected
        global statusbar
        flag = False
        canvas = Canvas(window, height=800, width=847, highlightthickness=0, bd=0, bg='#203647')
        canvas.place(x=0, y=0)
        # Creating A View Item Window
        Topwindow = Frame(canvas, bd=5, relief=SOLID)
        Topwindow.pack(side=TOP, fill=X)
        Midwindow = Frame(canvas, width=500, bg='#203647')
        Midwindow.pack()
        lbl_text = Label(Topwindow, text="Avilable Files On Server", font=('calibri', 23, 'bold'), width=52, bg="#203647",
                         fg='white')
        lbl_text.pack()
        scrollbarx = Scrollbar(Midwindow, orient=HORIZONTAL)
        scrollbary = Scrollbar(Midwindow, orient=VERTICAL)
        tree = ttk.Treeview(Midwindow,
                            columns=('ID',
                                     'FileName'),
                            selectmode="extended", height=24, yscrollcommand=scrollbary.set, xscrollcommand=scrollbarx.set)

        scrollbary.config(command=tree.yview)
        scrollbary.pack(side=RIGHT, fill=Y)
        scrollbarx.config(command=tree.xview)
        scrollbarx.pack(side=BOTTOM, fill=X)

        style = ttk.Style(Midwindow)
        # set ttk theme to "clam" which support the fieldbackground option
        style.theme_use("clam")
        style.configure("Treeview", background="white", fieldbackground="white", foreground="#203647", font=(3))

        tree.heading('ID', text="ID", anchor=W)
        tree.heading('FileName', text="Filename", anchor=W)

        tree.column('#0', stretch=NO, minwidth=0, width=0)
        tree.column('#1', stretch=NO, minwidth=0, width=70)
        tree.column('#2', stretch=NO, minwidth=0, width=750)

        def selected(a):
            global flag, id_selected
            flag = True
            curItem = tree.focus()
            try:
                id_selected = tree.item(curItem)['values'][0]
            except:
                pass

        def download_item():
            global flag, id_selected
            if flag == True:
                download_file(id_selected)
                flag = False
            else:
                tkMessageBox.showerror(title="File Not Selected", message="Select File to Download !")

        def view_files():
            try:
                mycursor = mydb.cursor()
                query = """select * from """ + table_name
                mycursor.execute(query)
                for i in mycursor:
                    lt = [i[0], i[1]]
                    tree.insert('', 'end', values=(lt))
            except Exception as e:
                print(e)

        tree.bind('<ButtonRelease-1>', selected)
        tree.pack()
        Button(Midwindow, text='Download', font=('calibri', 21, 'bold'), width=54, bg="#203647", fg='white',
               command=download_item).pack()
        thread = threading.Thread(target=view_files)
        thread.start()


    def about():
        canvas = Canvas(window, height=800, width=847, highlightthickness=0, bd=0, bg='#203647')
        imgq = Image.open(ImagePath+"abc.png")
        image1 = ImageTk.PhotoImage(imgq)
        panel1 = Label(canvas, image=image1, highlightthickness=0, bd=0)
        panel1.image = image1  # keep a reference
        panel1.pack(side='top', fill='both', expand='yes')
        canvas.place(x=0, y=0)


    def Exit():
        # Function To Get Pop Up A Exit Window
        result = tkMessageBox.askquestion('VoiceVault', 'Are you sure you want to exit?', icon="warning")
        if result == 'yes':
            window.destroy()
            exit()
        else:
            tkMessageBox.showinfo('Return', 'You will now return to the application screen')

    def logout():
        window.destroy()
        voiceverificationlogin()

    canvas = Canvas(window, height=800, width=700, highlightthickness=0, bd=0, bg='#EEFBFB')
    canvas.place(x=848, y=0)

    head = Label(window, text=" ```VOICEVAULT```", bg="#EEFBFB", font=('Calibiri', 17, 'bold'), fg="#203647")
    head.place(x=850, y=10)

    file_img = Image.open(ImagePath+'icon.png')
    file_img = file_img.resize((195, 275))
    icon_img = ImageTk.PhotoImage(file_img)
    panel = Label(window, image=icon_img, bg="#EEFBFB")
    panel.place(x=850, y=60)

    b1 = Button(window, text="Upload", width=14, fg="#EEFBFB", highlightthickness=0, font=('Calibiri', 17, 'bold'), bd=0,
                bg="#203647", activebackground="#EEFBFB", command=upload)
    b1.place(x=849, y=350)
    b2 = Button(window, text="Download", width=14, fg="#EEFBFB", highlightthickness=0, font=('Calibiri', 17, 'bold'), bd=0,
                bg="#203647", activebackground="#EEFBFB", command=download)
    b2.place(x=849, y=412)
    b3 = Button(window, text="About", width=14, fg="#EEFBFB", highlightthickness=0, font=('Calibiri', 17, 'bold'), bd=0,
                bg="#203647", activebackground="#EEFBFB", command=about)
    b3.place(x=849, y=474)

    b4 = Button(window, text="Logout", width=14, fg="#EEFBFB", highlightthickness=0, font=('Calibiri', 17, 'bold'), bd=0,
                bg="#203647", activebackground="#EEFBFB", command=logout)
    b4.place(x=849, y=536)

    b4 = Button(window, text="Exit", width=14, fg="#EEFBFB", highlightthickness=0, font=('Calibiri', 17, 'bold'), bd=0,
                bg="#203647", activebackground="#EEFBFB", command=Exit)
    b4.place(x=849, y=588)
    about()
    window.mainloop()



    

# sysVerify()
voiceverificationlogin()
