from PyQt5 import QtCore, QtNetwork
import time, os, queue, struct, datetime, threading
import proto, hashlib

class Handler(QtCore.QObject):
	def __init__(self, address, connected_callback, error_callback, readyread_callback, disconnected_callback):
		super().__init__()

		#properties
		self.connected = False
		self._address = address

		self.authed = 0

		self.buffer = []

		self.readyread = readyread_callback

		self._written = 0

		self.socket = QtNetwork.QTcpSocket()
		self.socket.connected.connect(connected_callback)
		self.socket.error.connect(error_callback)
		self.socket.disconnected.connect(disconnected_callback)
		self.socket.bytesWritten.connect(self._handle_written)

		self.socket.waitForConnected(1000)
		self.socket.connectToHost(address[0], address[1])

	def put(self, event, raw_bytes = None, fileno = None, callback = None):
		self.socket.write(proto.encode_event(0, event))
		if raw_bytes:
			for i, d in enumerate(raw_bytes):
				b = struct.pack('>H', len(d)) + d
				self.socket.write(b)
				if callback: callback(i+1)
		if fileno:
			threading.Thread(target = self.send_file, args = (fileno, None)).start()

	def _handle_readyread(self):
		buf = self.socket.readAll()
		while buf:
			lent = buf[:2]
			buf = buf[2:]
			data = buf[:struct.unpack('>H', lent)[0]]
			buf = buf[struct.unpack('>H', lent)[0]:]
			self.buffer.append(data)
			self.readyread()

	def auth(self, password, callback):
		password = hashlib.sha512(datetime.datetime.now().minute.to_bytes(1, byteorder='big') + password.encode()).digest()
		self.socket.write(proto.encode_event(0, proto.Event(name = 'send_password', data = {'password': password})))
		self.auth_callback = callback
		self._wait_auth()

	def _wait_auth(self):
		self.socket.waitForReadyRead()
		self.socket.readyRead.connect(self._handle_readyread)
		lent = self.socket.read(2)
		data = self.socket.read(struct.unpack('>H', lent)[0])
		print(data)
		event = proto.decode_event(0, data, 0)
		print(event.name)
		if event.name == 'socket_connected':
			self.authed = 1
			self.auth_callback(0)
			return
		elif event.name == 'error':
			self.socket.readyRead.connect(self._wait_auth)
			self.auth_callback(event.data['code'])

	def send_file(self, fileno, callback):
		ind = 0
		chunck = 1
		while chunck:
			chunck = fileno.read(1024)
			header = struct.pack('>H', len(chunck))
			self.socket.write(header + chunck)
			if ind % 20 == 0 and callback: callback(ind+1)
			ind += 1
		fileno.close()


	def get(self):
		event = proto.decode_event(0, self.buffer.pop(0), 0)
		print(event.name)
		return event

	def _handle_written(self, amount):
		self._written = amount

	def disconnect(self):
		self.socket.disconnectFromHost()


