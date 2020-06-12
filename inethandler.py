import socket, select, queue, proto, time, datetime, hashlib, struct, sys

_ADDRESS = ('', 19130)

LOADED_FILENOS = {}

DEBUG = None

print(DEBUG)

class FileWriter:
	def __init__(self, length):
		self.buffer = b''
		self.total = length
		self.received = 0
		self.fileno = 0
	def __repr__(self):
		return "< FileWriter object, saved {}% >".format(round(self.received/self.total*100, 1))

	def put(self, data):
		if DEBUG: print(self.procent())
		self.buffer += data
		self.received += len(data)
		if self.received == self.total:
			with open('./.temp/{}'.format(time.time()), 'wb') as file:
				file.write(self.buffer)
				LOADED_FILENOS[len(LOADED_FILENOS)] = file.name
				self.fileno = len(LOADED_FILENOS)-1
		elif self.received > self.total:
			self.fileno = -1

	def procent(self):
		return round(self.received/self.total*100, 1)

class InetHandler:
	def __init__(self, input_queue, outq, password, db):
		global _ADDRESS
		self.log = db.log
		self.input_queue = input_queue
		self.outp = outq
		self.pswd = password
		self.db = db
		self.return_var = None

		if 'ip:port' in self.db.mconf['serverconfig'].keys():
			_ADDRESS = self.db.mconf['serverconfig']['ip:port']


		self.listener = socket.create_server(_ADDRESS)
		self.clientsockets = {}
		self.clientstate = {}

		self.epoll = select.epoll()

	def run(self):
		try:
			self.return_var = self._run()
		except Exception as e:
			self.log.error('main', e)
			self.return_var = -1
			#self.run()

	def _run(self):
		self.listener.setblocking(0)
		self.listener.listen()
		self.epoll.register(self.listener.fileno(), select.EPOLLIN)

		while True:
			events = self.epoll.poll(0.5)
			for fd, event in events:

				if fd == self.listener.fileno():
					clientsock, address = self.listener.accept()
					clientsock.setblocking(0)
					self.epoll.register(clientsock.fileno(), select.EPOLLIN)
					self.clientsockets[clientsock.fileno()] = clientsock
					self.clientstate[clientsock.fileno()] = 'waitpass'
					self.log.debug('main', 'чилипиздрик connected')

				elif event & select.EPOLLHUP:
					self.log.debug('main', 'чилипиздрик disconnected')
					try:
						self.clientsockets[fd].close()
						self.clientsockets.pop(fd)
						self.clientstate.pop(fd)
					except KeyError:
						pass
					self.epoll.unregister(fd)

				elif event & select.EPOLLIN:
					mess = self.clientsockets[fd].recv(2)
					if not mess:
						self.log.debug('main', 'чилипиздрик disconnected')
						self.clientsockets[fd].close()
						self.clientsockets.pop(fd)
						self.clientstate.pop(fd)
						self.epoll.unregister(fd)
						continue
					lent = struct.unpack('>H', mess)[0]
					packet = self.clientsockets[fd].recv(lent)
					try:
						in_event = proto.decode_event(1, packet, fd)
						if DEBUG: print(in_event.name, in_event.data)
					except Exception as e:
						self.log.error('main', e)
						in_event = None

					if self.clientstate[fd] == 'waitpass':
						#print(in_event.data['password'], hashlib.sha512(datetime.datetime.now().minute.to_bytes(1, byteorder='big') + password.encode()).digest())
						if in_event and in_event.name == 'send_password':
							if in_event.data['password'] == hashlib.sha512(datetime.datetime.now().minute.to_bytes(1, byteorder='big') + self.pswd.encode()).digest() or in_event.data['password'] == hashlib.sha512((datetime.datetime.now().minute-1).to_bytes(1, byteorder='big') + self.pswd.encode()).digest():
								self.clientstate[fd] = 0
								self.outp.put(proto.Event(name = 'socket_connected', data = {}, from_fd = fd))
								for line in self.log.get_past_lines():
									self.outp.put(proto.Event(name = 'console', data = {'line': line[:1510]}, from_fd = fd))
								self.log.debug('main', 'чилипиздрик logged in')

							else:
								self.outp.put(proto.Event(name = 'error', data = {'code': -1}, from_fd = fd))

						else:
							self.outp.put(proto.Event(name = 'error', data = {'code': 400}, from_fd = fd))

					elif isinstance(self.clientstate[fd], dict):
						if 'upload_handler' in self.clientstate[fd].keys():
							self.clientstate[fd]['upload_handler'].put(packet)
							if self.clientstate[fd]['upload_handler'].fileno == -1:
								self.outp.put(proto.Event(name = 'error', data = {'code': 400}, from_fd = fd))

							elif self.clientstate[fd]['upload_handler'].fileno > 0:
								self.outp.put(proto.Event(name = 'replyfileno', data = {'fileno': self.clientstate[fd]['upload_handler'].fileno}, from_fd = fd))
								self.clientstate[fd] = 0

					elif self.clientstate[fd] == 0:
						if in_event and in_event.name == 'disconnect':
							self.clientsockets[fd].close()
							self.clientstate.pop[fd]
							self.epoll.unregister(fd)
							self.log.debug('main', 'чилипиздрик disconnected')

						elif in_event and in_event.name == 'upload':
							self.clientstate[fd] = {'upload_handler': FileWriter(in_event.data['size'])}

						elif in_event:
							self.input_queue.put(in_event)

						else:
							self.outp.put(proto.Event(name = 'error', data = {'code': -2}, from_fd = fd))



			while not self.outp.empty():
				outcomming_event = self.outp.get()
				if DEBUG: print('main', outcomming_event.data)
				if outcomming_event.from_fd == 0:
					for key, value in self.clientsockets.items():
						if self.clientstate[value.fileno()] != 'waitpass':
							value.send(proto.encode_event(1, outcomming_event))
				else:
					try:
						self.clientsockets[outcomming_event.from_fd].send(proto.encode_event(1, outcomming_event))
					except BrokenPipeError:
						self.clientsockets.pop(outcomming_event.from_fd)
						self.epoll.unregister(fd)





