import serverhandler, database, updatehelper, inethandler, proto, json, time, sys, os, queue
from threading import Thread

VERSION = '0.0.1a'


class Manager:
	def __init__(self):
		print('BDSM(Bedrock Dedicated Server Manager) ver. {}, Initialization...'.format(VERSION))

		if '-d' in sys.argv:
			self.db = database.Database(debug=True)
			inethandler.DEBUG = True
		else:
			self.db = database.Database()

		self.log = self.db.log
		self.thread_dict = {'inethandler': None, 'update': None, 'serveroutput': None, 'q_out': None}

		self.serverhandler = None
		self.serverstate = 0

		self.checking_updates = False
		self.update_result = None

		self.last_reboot = 0
		self.last_updatecheck = 0
		self.last_reboot_message = None

		self.q_in = queue.Queue()
		self.q_out = queue.Queue()

		if not self.db.mconf['serverconfig']['password']:
			self.db.set_password(self.get_password())

		self.inethandler = inethandler.InetHandler(self.q_in, self.q_out, self.db.mconf['serverconfig']['password'], self.db)


	def error_occured(self):
		self.stop()

	def get_password(self):
		print('Remote access is not set, enter it to continue')
		password = ''
		while not password:
			password = input('Enter password: ').rstrip().lstrip()
			if not password:
				print("Very funny, but you really can't skip this step")
		return password

	def start(self):
		self.serverstate = 'prestart_update_check'
		if updatehelper.check_server_updates(self.log) == 1:
			updatehelper.extract(self.log, servername=self.db.mconf['serverconfig']['servername'])
		else:
			if not os.path.exists('./environ'):
				return -2
		self.last_updatecheck = time.time()
		self.serverstate = 0
		if not self.db.mconf['serverconfig']['current_world']:
			if 'w0' in self.db.mconf['worlds'].keys():
				self.db.select_world('w0')
			self.db.select_world(self.db.new_world('Untitled BDS world'))
		self.db.set_online(True)
		try:
			self.serverhandler = serverhandler.Handler(self.db.mconf['serverconfig']['current_world'], self.db, self.db.mconf['serverconfig']['backup_interval'], self.error_occured)
		except Exception as e:
			self.log.error('main', e)
			self.db.set_online(False)
			return -1
		self.db.players_online = {}
		self.serverstate = 1
		self.db.firststart = 0
		self.last_reboot = time.time()

	def stop(self, message = None, reason = None):
		#§
		if message:
			self.serverhandler.put('tellraw @a {{"rawtext": [{{"text": "{}"}}]}}'.format(message))
		else:
			self.serverhandler.put('tellraw @a {{"rawtext": [{{"text": "{}"}}]}}'.format('§eServer will shut down in few seconds, prepare to it!'))
		time.sleep(5)
		if reason:
			self.serverhandler.stop(reason=reason)
		else:
			self.serverhandler.stop()
		self.serverstate = 0
		self.db.set_online(0)
		self.q_out.put(proto.Event(name = 'stopped', data = {}, from_fd = 0))

	def reboot(self):
		self.q_out.put(proto.Event(name = 'restart'))
		self.serverhandler.stop(reason = 'Server rebooted')
		self.serverstate = 0
		self.db.set_online(0)
		self.q_out.put(proto.Event(name = 'stopped', data = {}, from_fd = 0))
		self.start()
		self.last_reboot = time.time()

	def recover(self, filename):
		if os.path.exists('./backups/{}/{}'.format(self.db.mconf['serverconfig']['current_world'], filename)):
			self.serverhandler.recovfrom_backup('./backups/{}/{}'.format(self.db.mconf['serverconfig']['current_world'], filename))
		else:
			return -1

	def parse_gamerules(self, line):
		for i in line.split(', '):
			key_item = i.split(' = ')
			self.db.gamerules[key_item[0]] = key_item[1]

	def _ServerOutputThreadFunction(self):

		while True:
			if self.serverstate == 1: 
				try:
					line = self.serverhandler.get()
					if '] Player connected:' in line:
						self.db.players_online[line.split('connected: ')[1].split(',')[0]] = int(line.split('xuid: ')[1][:-1])
						event = proto.Event(name = 'online_event', data = {'type': 0, 'name': line.split('connected: ')[1].split(',')[0], 'xuid': int(line.split('xuid: ')[1][:-1])})
						self.q_out.put(event)
					elif '] Player disconnected:' in line:
						try:
							xuid = self.db.players_online.pop(line.split('disconnected: ')[1].split(',')[0])
							event = proto.Event(name = 'online_event', data = {'type': 1, 'name': line.split('disconnected: ')[1].split(',')[0], 'xuid': xuid})
							self.q_out.put(event)
						except:
							pass
					elif 'Server started.' in line:
						self.q_out.put(proto.Event(name = 'started', data = {}, from_fd = 0))
					elif 'commandblockoutput = ' in line:
						self.parse_gamerules(line)
					elif 'Kicked' in line:
						xuid = self.db.players_online.pop(line.split()[1])
						event = proto.Event(name = 'online_event', data = {'type': 1, 'name': line.split()[1], 'xuid': xuid})
						self.q_out.put(event)
					elif 'Banned' in line:
						xuid = self.db.players_online.pop(line.split()[1])
						event = proto.Event(name = 'online_event', data = {'type': 1, 'name': line.split()[1], 'xuid': xuid})
						self.q_out.put(event)


					self.log.raw(line)
				except:
					self.serverhandler = None
					self.serverstate = 0
			time.sleep(0.1)

	def _q_out_thread(self):
		poller = []
		empty_count = 0
		self.log.add2poll(poller)
		while True:
			if poller:
				item = poller.pop(0)
				if item == '1':
					empty_count += 1
					continue
				if empty_count == 3:
					empty_count = 0
					self.q_out.put(proto.Event(name = 'error', data = {'code': 106}, from_fd = event.from_fd))
					continue
				self.q_out.put(proto.Event(name = 'console', data = {'line': item}, from_fd = 0))
			time.sleep(0.1)


	def _update_thread(self):
		self.checking_updates = True
		self.update_result = updatehelper.check_server_updates(self.log)


	def mainloop(self):
		self.thread_dict['inethandler'] = Thread(target = self.inethandler.run, daemon = True)
		self.thread_dict['serveroutput'] = Thread(target = self._ServerOutputThreadFunction, daemon = True)
		self.thread_dict['q_out'] = Thread(target = self._q_out_thread, daemon = True)

		aoa = 0

		print('Starting threads...')

		self.thread_dict['inethandler'].start()
		self.thread_dict['serveroutput'].start()
		self.thread_dict['q_out'].start()

		print('Successfully started!')

		if self.db.mconf['serverconfig']['startup_action'] == 'start':
			self.start()

		while True:

			if not self.db.firststart and not self.checking_updates:
				if self.db.mconf['serverconfig']['checkupdate_interval'] and self.last_updatecheck + self.db.mconf['serverconfig']['checkupdate_interval'] <= time.time():
					self.thread_dict['update'] = Thread(target = self._update_thread())

			if self.checking_updates:
				if self.update_result == 1:
					if self.serverstate == 1:
						self.stop(message = '§aNew Bedrock Dedicated Server version is available, server will shutdown to update in few seconds, prepare to it!', reason = '§aServer is updating now, please come back later.')
						self.serverstate = 'updating'
						self.q_out.put(proto.Event(name = 'updating', from_fd = 0))
						updatehelper.extract(self.log, servername = self.db.mconf['serverconfig']['servername'])
						self.start()
						self.checking_updates = False
					else:
						self.q_out.put(proto.Event(name = 'updating', from_fd = 0))
						updatehelper.extract(self.log, servername = self.db.mconf['serverconfig']['servername'])
						self.checking_updates = False

				if self.update_result != None:
					self.last_updatecheck = time.time()
					self.update_result = None
					self.checking_updates = False

			if not self.q_in.empty():
				event = self.q_in.get()

				if event.name == 'start':
					if self.serverstate == 0:
						stra =  self.start()
						if stra == -2:
							self.q_out.put(proto.Event(name = 'error', data = {'code': 12}, from_fd = event.from_fd))
						elif stra == -1:
							self.q_out.put(proto.Event(name = 'error', data = {'code': 105}, from_fd = event.from_fd))

					else:
						self.q_out.put(proto.Event(name = 'error', data = {'code': 1}, from_fd = event.from_fd))

				elif event.name == 'stop':
					if self.serverstate == 1:
						self.stop()
					else:
						self.q_out.put(proto.Event(name = 'error', data = {'code': 1}, from_fd = event.from_fd))

				elif event.name == 'write_console':
					if self.serverstate == 1:
						self.log.rawconsole(event.data['text'].decode())
						self.serverhandler.put(event.data['text'].decode())
					else:
						self.q_out.put(proto.Event(name = 'error', data = {'code': 2}, from_fd = event.from_fd))

				elif event.name == 'get':
					if event.data['name'] == 'is_online':
						self.q_out.put(proto.Event(
							name = 'answer',
							data = {'name': 'is_online', 'value': self.db.is_online},
							from_fd = event.from_fd
							))

					elif event.data['name'] == 'backup_interval':
						self.q_out.put(proto.Event(
							name = 'answer',
							data = {'name': 'backup_interval', 'value': self.db.mconf['serverconfig']['backup_interval']},
							from_fd = event.from_fd
							))

					elif event.data['name'] == 'checkupdate_interval':
						self.q_out.put(proto.Event(
							name = 'answer',
							data = {'name': 'checkupdate_interval', 'value': self.db.mconf['serverconfig']['checkupdate_interval']},
							from_fd = event.from_fd
							))

					elif event.data['name'] == 'reboot_interval':
						self.q_out.put(proto.Event(
							name = 'answer',
							data = {'name': 'reboot_interval', 'value': self.db.mconf['serverconfig']['reboot_interval']},
							from_fd = event.from_fd
							))

					elif event.data['name'] == 'servername':
						self.q_out.put(proto.Event(
							name = 'answer',
							data = {'name': 'servername', 'value': self.db.mconf['serverconfig']['servername']},
							from_fd = event.from_fd
							))

					elif event.data['name'] == 'startup_action':
						self.q_out.put(proto.Event(
							name = 'answer',
							data = {'name': 'startup_action', 'value': self.db.mconf['serverconfig']['startup_action']},
							from_fd = event.from_fd
							))

					elif event.data['name'] == 'rpacks':
						packs = self.db.list_rpacks()
						self.q_out.put(proto.Event(
							name = 'answer',
							data = {'name': 'rpacks', 'value': packs},
							from_fd = event.from_fd
							))

					elif event.data['name'] == 'bpacks':
						packs = self.db.list_bpacks()
						self.q_out.put(proto.Event(
							name = 'answer',
							data = {'name': 'bpacks', 'value': packs},
							from_fd = event.from_fd
							))

					elif event.data['name'] == 'selected_world':
						self.q_out.put(proto.Event(
							name = 'answer',
							data = {'name': 'selected_world', 'value': self.db.mconf['serverconfig']['current_world']},
							from_fd = event.from_fd
							))

					elif event.data['name'] == 'worlds':
						self.q_out.put(proto.Event(
							name = 'answer',
							data = {'name': 'worlds', 'value':  json.dumps(self.db.get_worlds())},
							from_fd = event.from_fd
							))

					elif event.data['name'] == 'world_info':
						self.q_out.put(proto.Event(
							name = 'answer',
							data = {'name': 'world_info', 'value':self.db.get_world_info(event.data['args'].decode())},
							from_fd = event.from_fd
							))

					elif event.data['name'] == 'players_online':
						self.q_out.put(proto.Event(
							name = 'answer',
							data = {'name': 'players_online', 'value': json.dumps(self.db.players_online)},
							from_fd = event.from_fd
							))

					elif event.data['name'] == 'world_backups_list':
						if os.path.exists('./backups/{}'.format(self.db.mconf['serverconfig']['current_world'])):
							l = os.listdir('./backups/{}'.format(self.db.mconf['serverconfig']['current_world']))
						else:
							l = []
						self.q_out.put(proto.Event(
							name = 'answer',
							data = {'name': 'world_backups_list', 'value': json.dumps(l)},
							from_fd = event.from_fd
							))

					elif event.data['name'] == 'prop':
						with open('./environ/server.properties', 'r') as prop:
							self.q_out.put(proto.Event(
								name = 'answer',
								data = {'name': 'text', 'value': prop.read()},
								from_fd = event.from_fd
								))

					elif event.data['name'] == 'gamerules':
						print('ebalvrot')
						self.serverhandler.put('gamerule')
						time.sleep(1)
						self.q_out.put(proto.Event(
							name = 'answer',
							data = {'gamerules': json.dumps(self.db.gamerules)},
							from_fd = event.from_fd
							))


				elif event.name == 'set':
					if event.data['name'] == 'password':
						self.db.set_password(event.data['value'].decode())
						self.inethandler.pswd = self.db.mconf['serverconfig']['password']

					elif event.data['name'] == 'backup_interval':
						self.serverhandler.b_interval = event.data['value']
						self.db.set_backup_interval(event.data['value'])
						self.q_out.put(proto.Event(
							name = 'value_changed',
							data = {'name': 'backup_interval', 'value': self.db.mconf['serverconfig']['backup_interval']},
							from_fd = 0
							))

					elif event.data['name'] == 'checkupdate_interval':
						self.last_updatecheck = time.time()
						self.db.set_checkupdate_interval(event.data['value'])
						self.q_out.put(proto.Event(
							name = 'value_changed',
							data = {'name': 'checkupdate_interval', 'value': self.db.mconf['serverconfig']['checkupdate_interval']},
							from_fd = 0
							))

					elif event.data['name'] == 'reboot_interval':
						self.last_reboot = time.time()
						self.db.set_reboot_interval(event.data['value'])
						self.q_out.put(proto.Event(
							name = 'value_changed',
							data = {'name': 'reboot_interval', 'value': self.db.mconf['serverconfig']['reboot_interval']},
							from_fd = 0
							))

					elif event.data['name'] == 'servername':
						self.db.set_servername(event.data['value'].decode())
						self.q_out.put(proto.Event(
							name = 'value_changed',
							data = {'name': 'servername', 'value': self.db.mconf['serverconfig']['servername']},
							from_fd = 0
							))

					elif event.data['name'] == 'startup_action':
						self.db.set_startup_action(event.data['value'].decode())
						self.q_out.put(proto.Event(
							name = 'value_changed',
							data = {'name': 'startup_action', 'value': self.db.mconf['serverconfig']['startup_action']},
							from_fd = 0
							))

				elif event.name == 'kick':
					nickname = event.data['nickname'].decode()
					if ' ' in nickname:
						self.serverhandler.put('kick "{}"'.format(nickname))
					else:
						self.serverhandler.put('kick {}'.format(nickname))

				elif event.name == 'ban':
					nickname = event.data['nickname'].decode()
					if ' ' in nickname:
						self.serverhandler.put('ban "{}"'.format(nickname))
					else:
						self.serverhandler.put('ban {}'.format(nickname))

				elif event.name == 'recover_fr_backup':
					if self.recover(event.data['filename'].decode()) == -1:
						self.q_out.put(proto.Event(
							name = 'error',
							data = {'code': 5},
							from_fd = event.from_fd
							))

				elif event.name == 'select_world':
					self.db.select_world(event.data['worldname'].decode())
					self.q_out.put(proto.Event(
							name = 'select_world',
							data = {'name': event.data['worldname'].decode()}
							))
					if self.serverstate == 1:
						self.reboot()

				elif event.name == 'new_world':
					self.q_out.put(proto.Event(
						name = 'new_world',
						data = {'name': self.db.new_world(event.data['levelname'].decode())}
						)) 

				elif event.name == 'delete_world':
					if self.db.delete_world(event.data['worldname'].decode()) != -1:
						self.q_out.put(proto.Event(
							name = 'rem_world',
							data = {'name': event.data['worldname'].decode()}
							)) 
					else:
						self.q_out.put(proto.Event(name = 'error', data = {'code': -55}, from_fd = event.from_fd))

				elif event.name == 'check_updates':
					self.thread_dict['update'] = Thread(target = self._update_thread)
					self.thread_dict['update'].start()

				elif event.name == 'apply_to_world':
					with open(os.path.join(event.data['path'].decode(), 'manifest.json'), 'r') as p:
						manifest = json.load(p)
						if manifest['modules'][0]['type'] == 'resources':
							type_ = 'r'
						elif manifest['modules'][0]['type'] == 'data':
							type_ = 'b'
					self.db.apply_to_world(event.data['worldname'].decode(), type_, event.data['path'].decode())

				elif event.name == 'discard_from_world':
					with open('./environ/valid_known_packs.json', 'r') as p:
						vkp = json.load(p)
						type_ = 'r'
						for i in vkp[1:]:
							if i['uuid'] == event.data['uuid'].decode() and i['version'] == '.'.join(map( str, json.loads( event.data['ver'].decode()))):
								if i['path'].startswith('resource_packs/'):
									type_ = 'r'
								elif i['path'].startswith('behavior_packs/'):
									type_ = 'b'
					self.db.disapply_to_world(event.data['worldname'].decode(), type_, event.data['uuid'].decode(), json.loads(event.data['ver'].decode()))

				elif event.name == 'restart':
					self.reboot()

				elif event.name == 'import':
					world = self.db.import_mcpack(inethandler.LOADED_FILENOS[event.data['fileno']])
					if world:
						self.q_out.put(proto.Event(
							name = 'new_world',
							data = {'name': world}
							))
					else:
						self.q_out.put(proto.Event(
							name = 'pack_imported'
							))

				elif event.name == 'unimport':
					self.db.remove_pack(event.data['uuid'].decode(), event.data['ver'].decode())
					self.q_out.put(proto.Event(
						name = 'pack_deleted'
						))

				elif event.name == 'prop_edit':
					with open('./environ/server.properties', 'w') as prop:
						prop.write(event.data['prop'].decode())
					with open('./environ/server.properties', 'r') as prop: 
						self.q_out.put(proto.Event(
							name = 'server.prop_edit',
							data = {'text': prop.read()}
							))


			if self.db.mconf['serverconfig']['reboot_interval']:
				if self.serverstate == 1:
					if round(self.last_reboot + self.db.mconf['serverconfig']['reboot_interval'] - 60) == round(time.time()) and self.last_reboot_message != 60:
						self.serverhandler.put('tellraw @a {{"rawtext": [{{"text": "{}"}}]}}'.format('§6Server will restart in one minute'))
						self.serverhandler.put('playsound note.bass @a')
						self.last_reboot_message = 60


					elif round(self.last_reboot + self.db.mconf['serverconfig']['reboot_interval'] - 30) == round(time.time()) and self.last_reboot_message != 30:
						self.serverhandler.put('tellraw @a {{"rawtext": [{{"text": "{}"}}]}}'.format('§6Server will restart in 30 seconds'))
						self.serverhandler.put('playsound note.bass @a')
						self.last_reboot_message = 30

					elif round(self.last_reboot + self.db.mconf['serverconfig']['reboot_interval'] - 10) == round(time.time()) and self.last_reboot_message != 10:
						self.serverhandler.put('tellraw @a {{"rawtext": [{{"text": "{}"}}]}}'.format('§6Server will restart in 10 seconds'))
						self.serverhandler.put('playsound note.bass @a')
						self.last_reboot_message = 10

					elif round(self.last_reboot + self.db.mconf['serverconfig']['reboot_interval'] - 5) == round(time.time()) and self.last_reboot_message != 5:
						self.serverhandler.put('tellraw @a {{"rawtext": [{{"text": "{}"}}]}}'.format('§6Server will restart in 5 seconds'))
						self.serverhandler.put('playsound note.bass @a')
						self.last_reboot_message = 5

					elif round(self.last_reboot + self.db.mconf['serverconfig']['reboot_interval'] - 4) == round(time.time()) and self.last_reboot_message != 4:
						self.serverhandler.put('tellraw @a {{"rawtext": [{{"text": "{}"}}]}}'.format('§6Server will restart in 4 seconds'))
						self.serverhandler.put('playsound note.bass @a')
						self.last_reboot_message = 4

					elif round(self.last_reboot + self.db.mconf['serverconfig']['reboot_interval'] - 3) == round(time.time()) and self.last_reboot_message != 3:
						self.serverhandler.put('tellraw @a {{"rawtext": [{{"text": "{}"}}]}}'.format('§6Server will restart in 3 seconds'))
						self.serverhandler.put('playsound note.bass @a')
						self.last_reboot_message = 3

					elif round(self.last_reboot + self.db.mconf['serverconfig']['reboot_interval'] - 2) == round(time.time()) and self.last_reboot_message != 2:
						self.serverhandler.put('tellraw @a {{"rawtext": [{{"text": "{}"}}]}}'.format('§6Server will restart in 2 seconds'))
						self.serverhandler.put('playsound note.bass @a')
						self.last_reboot_message = 2

					elif round(self.last_reboot + self.db.mconf['serverconfig']['reboot_interval'] - 1) == round(time.time()) and self.last_reboot_message != 1:
						self.serverhandler.put('tellraw @a {{"rawtext": [{{"text": "{}"}}]}}'.format('§6Server will restart in 1 second'))
						self.serverhandler.put('playsound note.bass @a')
						self.last_reboot_message = 1

					elif round(self.last_reboot + self.db.mconf['serverconfig']['reboot_interval']) < round(time.time()):
						self.reboot()



			time.sleep(0.1)


if __name__ == '__main__':
	Manager().mainloop()








