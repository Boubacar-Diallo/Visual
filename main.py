# Script to either listen to microphone or desktop audio output,
# pick out important words, and show images of the current word
# on screen. See my Google doc.

# need to pip install...
# SpeechRecognition
# pyaudio
# pocketsphinx
# nltk (+ data for it)

import speech_recognition as sr
from time import sleep
import nltk
# need to add support for GoogleScraper library
# so I can fetch the images, everything else seems
# to work.

# from top comment here: https://stackoverflow.com/questions/20716842/python-download-images-from-google-image-search
from bs4 import BeautifulSoup
import requests
import re
import urllib2
import os
import cookielib
import json


# print out all available microphones on current computer
def print_mics():
	for index, name in enumerate(sr.Microphone.list_microphone_names()):
	    print("Microphone with name \"{1}\" found for `Microphone(device_index={0})`".format(index, name))


# saves 100 images related to 'query' into Pictures directory
def fetch_images(query):
	def get_soup(url,header):
	    return BeautifulSoup(urllib2.urlopen(urllib2.Request(url,headers=header)),'html.parser')

	image_type="ActiOn"
	query= query.split()
	query='+'.join(query)
	url="https://www.google.co.in/search?q="+query+"&source=lnms&tbm=isch"
	print url
	#add the directory for your image here
	DIR="Pictures"
	header={'User-Agent':"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.134 Safari/537.36"
	}
	soup = get_soup(url,header)

	ActualImages=[]# contains the link for Large original images, type of  image
	for a in soup.find_all("div",{"class":"rg_meta"}):
	    link , Type =json.loads(a.text)["ou"]  ,json.loads(a.text)["ity"]
	    ActualImages.append((link,Type))

	print  "there are total" , len(ActualImages),"images"

	if not os.path.exists(DIR):
	            os.mkdir(DIR)
	DIR = os.path.join(DIR, query.split()[0])

	if not os.path.exists(DIR):
	            os.mkdir(DIR)
	###print images
	for i , (img , Type) in enumerate( ActualImages):
	    try:
	        req = urllib2.Request(img, headers={'User-Agent' : header})
	        raw_img = urllib2.urlopen(req).read()

	        cntr = len([i for i in os.listdir(DIR) if image_type in i]) + 1
	        print cntr
	        if len(Type)==0:
	            f = open(os.path.join(DIR , image_type + "_"+ str(cntr)+".jpg"), 'wb')
	        else :
	            f = open(os.path.join(DIR , image_type + "_"+ str(cntr)+"."+Type), 'wb')


	        f.write(raw_img)
	        f.close()
	    except Exception as e:
	        print "could not load : "+img
	        print e


def listen_to_mic(device_index=1,timeout=1,phrase_time_limit=1):
	mic=sr.Microphone(device_index)
	print mic

	rec=sr.Recognizer()
	#rec.energy_threshold = 20

	with mic as source:
		rec.adjust_for_ambient_noise(mic)
	print "Done calibrating...."

	while True:

		try:
			with mic as source:
				data=rec.listen(source,timeout,phrase_time_limit)
			text=rec.recognize_sphinx(data)
			print "Raw text:",text

			tokens=nltk.word_tokenize(text)
			print "Tokens:",tokens 

			tagged=nltk.pos_tag(tokens)
			print "Tagged:",tagged 

			entities=nltk.chunk.ne_chunk(tagged)
			print "Entities:",entities

			for t in tagged:
				if t[1]=='NN':
					print "\n\n%s\n\n"%(t[0].capitalize())

		except:
			print "T'was an error"
			sleep(1) # sleep to allow for exit


#fetch_images('horse')
#print_mics()
listen_to_mic(0,1,5)




