from subprocess import call
import subprocess
from Adafruit_Thermal import *
import Image,ImageFilter
import RPi.GPIO as GPIO
import time
import os
from os import listdir
from os.path import isfile,join
from datetime import datetime, timedelta

FORMAT = '%Y_%m_%d_%H_%M_%S'
EXTENSION = '.jpg'
printPath = '/home/pi/dropbox_pic/lobby'
savePath = "/home/pi/workSpace/Python-Thermal-Printer/resource/"
fileDict = dict()

def fmt(date):
    if date<10:
        return '0'+str(date)
    else:
        return str(date)

def makeTimeStamp():
    now = datetime.now()
    timeStamp = now.strftime(FORMAT)
    return timeStamp

def parseTimeStamp(timeStamp):
    fileTime = datetime.strptime(timeStamp, FORMAT)
    return fileTime

def findFileInOrder():
    fileList = []
    for filename in os.listdir(printPath):
        if filename.endswith(EXTENSION):
            filename = filename.replace(EXTENSION,'')
            fileList.append(filename)
    return sorted(fileList)
    

def takePicture(fileToSave):
    call(['fswebcam','--scale','384x288','--no-banner',fileToSave], shell=False)
        
def printImage(fileToPrint, result, timeNow, location):
    def imageProcessing(fileToPrint):
        img = Image.open(fileToPrint)
        img = img.filter(ImageFilter.EDGE_ENHANCE_MORE)
        img = img.filter(ImageFilter.SHARPEN)
        img = img.filter(ImageFilter.MedianFilter)
        img = img.rotate(180)
        return img

    def getTimeElapsed(fileToPrint):
        text = ''
        now = datetime.now()
        last = parseTimeStamp(fileToPrint)
        timeElapsed = now - last
        seconds = int(timeElapsed.seconds)
        minutes = int(round(seconds/60))
        hours = int(round(seconds/3600))
        days = int(timeElapsed.days)
        # days and hours
        if (days > 0):
            if (days == 1):
                text += str(days)+'day '
            else:
                text += str(days)+'days ' 
            if (hours > 0):
                if (hours == 1):
                    text += str(hours)+'hour '
                else:
                    text += str(hours)+'hours '
        elif (days == 0): 
            # hours and minutes
            if (hours > 0):
                if (hours == 1):
                    text += str(hours)+'hour '
                else:
                    text += str(hours)+'hours '
                minutes = minutes - 60*hours
                if (minutes > 0):
                    if (minutes == 1):
                        text += str(minutes)+'minute '
                    else:
                        text += str(minutes)+'minutes '
            else:
                # minutes and seconds
                if (minutes > 0):
                    if (minutes == 1):
                        text += str(minutes)+'minute '
                    else:
                        text += str(minutes)+'minutes '
                    seconds = seconds - minutes*60
                    if (seconds > 0):
                        if (seconds == 1):
                            text += str(seconds)+'second '
                        else:
                            text += str(seconds)+'seconds '        
                # seconds
                else:
                    text += str(seconds)+'seconds '
                
        text += 'ago @'+location       
        return text
    
    def getTimeNow(timeNow):
        text ='Printed at '
        timeNow = parseTimeStamp(timeNow)
        year = timeNow.year
        month = timeNow.month
        day = timeNow.day
        hour = timeNow.hour
        minute = timeNow.minute        
        text += fmt(year)+'.'+fmt(month)+'.'+fmt(day)+' '
        text += fmt(hour)+':'+fmt(minute)
        return text

    image  = imageProcessing(fileToPrint)
    printer = Adafruit_Thermal("/dev/ttyAMA0", 19200, timeout=5)
    printer.printImage(image, True) # This does the printing
    
    printer.upsideDownOn()
    printer.justify('C')

    timeElapsed = getTimeElapsed(result) 
    printer.println(timeElapsed)
        
    timeNow = getTimeNow(timeNow)    
    printer.println(timeNow)
    printer.upsideDownOff()
    printer.feed(3)
    
def uploadFile(localPath, timeStamp, EXTENSION):
    remotePath = '/PhysLab/' + timeStamp + EXTENSION
    # Upload the file to dropbox codeLab folder
    call(['/home/pi/Dropbox-Uploader/dropbox_uploader.sh','-s','upload',localPath,remotePath], shell=False)

def getFileToPrint(fileList):
    global fileDict
    for item in fileList:
        if item not in fileDict:
            fileDict[item] = False
    for item in fileList:
        if fileDict[item] == False:
            fileDict[item] = True
            return item
        
def main():
    # Get the current time, format it as the file name
    timeNow = makeTimeStamp() 
    fileToSave = savePath + timeNow + EXTENSION
    # Find the unprint picture
    fileList = findFileInOrder()
    if (len(fileList)==0):
        takePicture(fileToSave)
        printImage(fileToSave, timeNow, timeNow, 'A10')
    else:
        result = getFileToPrint(fileList)
        if result is None:
            takePicture(fileToSave)
            printImage(fileToSave, timeNow, timeNow, 'A10')
        else:
            fileToPrint = printPath + '/' + result + EXTENSION
            # Take the current picture
            takePicture(fileToSave)
            # Print the unprint picture
            printImage(fileToPrint, result, timeNow, 'lobby')
            # Upload the current picture
    try:
        uploadFile(fileToSave, timeNow, EXTENSION) 
    except:
        printer = Adafruit_Thermal("/dev/ttyAMA0", 19200, timeout=5)
        printer.println("Error Upload")
        
GPIO.setmode(GPIO.BCM)
GPIO.setup(25, GPIO.IN, pull_up_down=GPIO.PUD_UP)

try:
    while True:
        GPIO.wait_for_edge(25, GPIO.FALLING)
        main()
except KeyboardInterrupt:
    GPIO.cleanup()
  