import grpc

from ..common import cochlear_sense_pb2
from ..common import cochlear_sense_pb2_grpc

import pyaudio
from six.moves import queue

list_of_files = ['speech_detector', 'music_detector', 'age_gender', \
 				'music_genre', 'music_mood', 'music_tempo', 'music_key', 'event']
list_of_streams = ['speech_detector_stream', 'music_detector_stream', \
				'age_gender_stream', 'music_genre_stream', 'music_mood_stream', 'event_stream']

def sense_file(filename,apikey,file_format,task,subtask=None):

	host = '35.236.162.35:50051'
	# host = 'beta.cochlear.ai'

	channel = grpc.insecure_channel(host)
	stub = cochlear_sense_pb2_grpc.cochlear_senseStub(channel)

	CHUNK = 1024*1024

	def get_file_chunks(filename):
		with open(filename,'rb') as f:
			while True:
				piece = f.read(CHUNK);
				if len(piece) == 0:
					return
				yield cochlear_sense_pb2.input(data=piece,apikey=apikey,format=file_format,subtask=subtask)

	chunks_generator = get_file_chunks(filename)

	assert task in list_of_files, 'wrong task: {}'.format(task)
	
	if task == 'speech_detector':
		response = stub.speech_detector(chunks_generator)
	elif task == 'music_detector':
		response = stub.music_detector(chunks_generator)
	elif task == 'age_gender':
		response = stub.age_gender(chunks_generator)
	elif task == 'music_genre':
		response = stub.music_genre(chunks_generator)
	elif task == 'music_mood':
		response = stub.music_mood(chunks_generator)
	elif task == 'music_tempo':
		response = stub.music_tempo(chunks_generator)
	elif task == 'music_key':
		response = stub.music_key(chunks_generator)
	elif task == 'event':
		response = stub.event(chunks_generator)

	return response.pred


class SenseStreamer(object):
	def __init__(self,task):
		assert task in list_of_streams, 'wrong task: {}'.format(task)

		if task == 'speech_detector_stream':
			rate = 16000
			chunk = int(rate / 2)
		elif task == 'music_detector_stream':
			rate = 16000
			chunk = int(rate / 2)
		elif task == 'age_gender_stream':
			rate = 16000
			chunk = int(rate / 2)
		elif task == 'music_genre_stream':
			rate = 22050
			chunk = int(rate / 2)
		elif task == 'music_mood_stream':
			rate = 22050
			chunk = int(rate / 2)
		elif task == 'event_stream':
			rate = 22050
			chunk = int(rate / 2)

		self._rate = rate
		self._chunk = chunk
		self._buff = queue.Queue()
		self.closed = True

	def __enter__(self):
		self._audio_interface = pyaudio.PyAudio()
		self._audio_stream = self._audio_interface.open(
			format=pyaudio.paFloat32,
			channels=1, rate=self._rate,
			input=True, frames_per_buffer=self._chunk,
			stream_callback=self._fill_buffer,
		)

		self.closed = False
		return self

	def __exit__(self, type, value, traceback):
		self._audio_stream.stop_stream()
		self._audio_stream.close()
		self.closed = True
		self._buff.put(None)
		self._audio_interface.terminate()

	def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
		self._buff.put(in_data)
		return None, pyaudio.paContinue

	def generator(self):
		while not self.closed:
			chunk = self._buff.get()
			if chunk is None:
				return
			data = [chunk]

			while True:
				try:
					chunk = self._buff.get(block=False)
					if chunk is None:
						return
					data.append(chunk)
				except queue.Empty:
					break
			yield b''.join(data)

def sense_stream_request(audio_generator,apikey,task,subtask=None):

	host = '35.236.162.35:50051'
	# host = 'beta.cochlear.ai'

	channel = grpc.insecure_channel(host)
	stub = cochlear_sense_pb2_grpc.cochlear_senseStub(channel)

	assert task in list_of_streams, 'worng task request: {}'.format(task)

	if task == 'speech_detector_stream':
		sr = 16000
	elif task == 'music_detector_stream':
		sr = 16000
	elif task == 'age_gender_stream':
		sr = 16000
	elif task == 'music_genre_stream':
		sr = 22050
	elif task == 'music_mood_stream':
		sr = 22050
	elif task == 'event_stream':
		sr = 22050

	requests = (cochlear_sense_pb2.input(data=content,apikey=apikey,subtask=subtask,sr=sr) 
					for content in audio_generator)
	
	return requests

def sense_stream_response(requests,task):

	host = '35.236.162.35:50051'
	# host = 'beta.cochlear.ai'

	channel = grpc.insecure_channel(host)
	stub = cochlear_sense_pb2_grpc.cochlear_senseStub(channel)

	assert task in list_of_streams, 'wrong task from the server: {}'.format(task)

	if task == 'speech_detector_stream':
		responses = stub.speech_detector_stream(requests)
	elif task == 'music_detector_stream':
		responses = stub.music_detector_stream(requests)
	elif task == 'age_gender_stream':
		responses = stub.age_gender_stream(requests)
	elif task == 'music_genre_stream':
		responses = stub.music_genre_stream(requests)
	elif task == 'music_mood_stream':
		responses = stub.music_mood_stream(requests)
	elif task == 'event_stream':
		responses = stub.event_stream(requests)

	return responses