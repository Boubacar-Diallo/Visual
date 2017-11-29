# Script to either listen to microphone or desktop audio output,
# pick out important words, and show images of the current word
# on screen. See my Google doc.

# need to pip install...
# SpeechRecognition
# pyaudio
# pocketsphinx

import speech_recognition as sr
from time import sleep
import nltk
# need to add support for GoogleScraper library
# so I can fetch the images, everything else seems
# to work.

'''
for index, name in enumerate(sr.Microphone.list_microphone_names()):
    print("Microphone with name \"{1}\" found for `Microphone(device_index={0})`".format(index, name))
'''


mic=sr.Microphone(device_index=1)
print mic

rec=sr.Recognizer()
#rec.energy_threshold = 20

with mic as source:
	rec.adjust_for_ambient_noise(mic)
print "Done calibrating...."

while True:

	try:
		with mic as source:
			data=rec.listen(source,timeout=1,phrase_time_limit=1)
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

