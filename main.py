# Script to either listen to microphone or desktop audio output,
# pick out important words, and show images of the current word
# on screen. See my Google doc.

# need to pip install...
# SpeechRecognition
# pyaudio
# pocketsphinx
# nltk (+ data for it)

import speech_recognition as sr
from time import sleep,time
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

# for the gui
from PyQt4.QtGui import *
from PyQt4.QtCore import *
import sys

# print out all available microphones on current computer
def print_mics():
	for index, name in enumerate(sr.Microphone.list_microphone_names()):
		print("Microphone with name \"{1}\" found for `Microphone(device_index={0})`".format(index, name))


# saves 100 images related to 'query' into Pictures directory
def fetch_images(query,n=1):

	# prepare query if it contains more than one word
	if len(query.split(' '))>1:
		query='+'.join(query.split(" "))

	def get_soup(url,header):
		return BeautifulSoup(urllib2.urlopen(urllib2.Request(url,headers=header)),'html.parser')

	print 'Fetching picture of %s'%query

	image_type="ActiOn"
	query= query.split()
	query='+'.join(query)
	url="https://www.google.co.in/search?q="+query+"&source=lnms&tbm=isch"
	#print url
	#add the directory for your image here
	DIR="Pictures"
	header={'User-Agent':"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.134 Safari/537.36"
	}
	soup = get_soup(url,header)

	ActualImages=[]# contains the link for Large original images, type of  image
	i=0
	for a in soup.find_all("div",{"class":"rg_meta"}):

		if i>2+n:
			break

		link , Type =json.loads(a.text)["ou"]  ,json.loads(a.text)["ity"]
		ActualImages.append((link,Type))
		i+=1

	#print  "there are total" , len(ActualImages),"images"

	if not os.path.exists(DIR):
				os.mkdir(DIR)
	DIR = os.path.join(DIR, query.split()[0])

	if not os.path.exists(DIR):
				os.mkdir(DIR)
	###print images
	found_image=False
	for i , (img , Type) in enumerate( ActualImages):

		try:
			req = urllib2.Request(img, headers={'User-Agent' : header})
			raw_img = urllib2.urlopen(req).read()

			cntr = len([i for i in os.listdir(DIR) if image_type in i]) + 1
			#print cntr
			if len(Type)==0:
				fname=os.path.join(DIR , image_type + "_"+ str(cntr)+".jpg")
				f = open(os.path.join(DIR , image_type + "_"+ str(cntr)+".jpg"), 'wb')
			else :
				fname=os.path.join(DIR , image_type + "_"+ str(cntr)+"."+Type)
				f = open(os.path.join(DIR , image_type + "_"+ str(cntr)+"."+Type), 'wb')

			f.write(raw_img)
			f.close()
			return fname

		except Exception as e:
			print "could not load : "+img
			print e
	return None

def listen_to_mic(mic,rec,timeout=1,phrase_time_limit=1):
	try:
		print 'Listening...'
		sys.stdout.flush() # flush terminal output (was having issues before)
		with mic as source:
			data=rec.listen(source,timeout,phrase_time_limit)
		text=rec.recognize_sphinx(data)
		print 'Raw text:',text
		return text
	except:
		print 'Error listening to mic.'
		sleep(1) # sleep to allow for exit
		return None

def process_text(text):

	try:
		print 'Processing text...'

		tokens=nltk.word_tokenize(text)
		#print 'Tokens:',tokens

		tagged=nltk.pos_tag(tokens)
		print 'Tagged:',tagged 

		#entities=nltk.chunk.ne_chunk(tagged)
		#print 'Entities',entities

		nouns={} # dict, maps from noun to it's count
		for t in tagged:
			if t[1]=='NN':
				noun=t[0].capitalize()
				if noun not in nouns:
					nouns[noun]=1 # add to dict
				else:
					nouns[noun]+=1
		if len(nouns)==0:
			print "No nouns were heard!"
			return None
		else:
			most_freq_noun=None
			for key,val in nouns.items():
				if most_freq_noun==None or val>nouns[most_freq_noun]:
					most_freq_noun=key 
			return most_freq_noun
	except:
		print 'Error processing text...'
		return None

# class to handle pushing new images to the main window
class frame_manager(QThread):
	update_gui=pyqtSignal() # signal used to update the main UI window

	def __init__(self,parent): # parent is the main UI window
		QThread.__init__(self,parent)
		self.connect(self,SIGNAL('update_gui()'),parent.update_picture)
		self.init_vars()

	def init_vars(self):
		self.stop=False
		self.pause=True
		self.pic_path=None
		self.refresh_rate=10 # seconds
		device_index=1
		self.mic=sr.Microphone(device_index)
		print self.mic
		self.rec=sr.Recognizer()
		#rec.energy_threshold = 20
		with self.mic as source:
			self.rec.adjust_for_ambient_noise(source)
		print "Done calibrating...."

	def run(self):
		while True:
			while self.pause:
				sleep(1)
			if self.stop:
				break
			#word=get_important_word(self.mic,self.rec,timeout=5,phrase_time_limit=10)
			text=listen_to_mic(self.mic,self.rec,timeout=1,phrase_time_limit=3)
			if text is not None:
				#word=process_text(text)
				word=text
				if word is not None:
					t0=time()
					fname=fetch_images(word)
					print 'Took %0.5f seconds to load image.'%(time()-t0)
					if fname is not None:
						self.pic_path=fname
						self.update_gui.emit()
					else:
						print "Couldn't find any images."
				else:
					print "No important words."

			else:
				print "Didn't hear any words."

# main UI window
class main_window(QWidget):
	def __init__(self):
		super(main_window,self).__init__()
		self.init_system() # create required folders/files
		self.init_vars() # initialize any class variables
		self.init_ui() # initialize the user interface
		self.start_listening() # tell worker to start

	def init_system(self):
		# ensure the pictures folder exists
		if not os.path.exists('pictures'):
			print 'Created pictures directory.'
			os.makedir('pictures')
		else:
			print 'pictures directory already exists.'

	def init_vars(self):
		# initialize any class variables
		self.min_width=600
		self.min_height=600

	def init_ui(self):
		# initialize GUI window
		self.setWindowTitle('Visual')
		self.window_layout=QVBoxLayout(self)
		self.main_image=QLabel() # push images into this
		main_row=QHBoxLayout()
		main_row.addStretch()
		main_row.addWidget(self.main_image)
		main_row.addStretch()
		self.window_layout.addLayout(main_row,2)
		self.resize(self.min_width,self.min_height)
		self.show()

		# separate thread to handle updating window
		self.update_manager=frame_manager(self) 
		self.update_manager.start() # start thread

	def update_picture(self):
		if self.update_manager.pic_path==None:
			print 'Update manager is being lazy.'
		else:
			print 'Updating picture w/%s.'%self.update_manager.pic_path
			try:
				self.current_frame=QPixmap(self.update_manager.pic_path)
				#self.current_frame=self.current_frame.scaled(555,520)
				self.current_frame=self.current_frame.scaled(self.size().width()-50,self.size().height()-50)
				self.main_image.setPixmap(self.current_frame)
			except:
				print 'Could not load new frame.'

	def resizeEvent(self,e):
		# called when user resizes the window, should re-scale the current image
		if hasattr(self,'current_frame'):
			# if we have an image
			self.current_frame=self.current_frame.scaled(self.size().width()-50,self.size().height()-50)
			self.main_image.setPixmap(self.current_frame)

	def start_listening(self):
		self.update_manager.pause=False

def main():
	
	# testing around with different functions
	#fetch_images('horse')
	#print_mics()
	#listen_to_mic(1,1,5)

	#'''
	# to open the GUI window
	app=QApplication(sys.argv)
	_=main_window()
	sys.exit(app.exec_())
	#'''

if __name__ == '__main__':
	main()




