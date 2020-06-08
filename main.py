from PyQt5 import QtGui, QtWidgets, QtCore
from ui import LogonForm, ServerPanel, PackDialog, SettingsDialog, GamerulesDialog, PackWidget
import config_manager, inethandler, proto
import sys, time, math, os, zipfile, shutil, json


class Window(QtWidgets.QMainWindow):
	def __init__(self, from_):
		super().__init__()
		self.window = from_()
		self.window.setupUi(self)


class Dialog(QtWidgets.QDialog):
	def __init__(self, type_):
		super().__init__()
		if type_ == 'packs':
			self.dialog = PackDialog.Ui_Dialog()
			self.dialog.setupUi(self)
			self.dialog.globalPacks.setAcceptDrops(True)
			self.dialog.globalPacks.dragEnterEvent = Dialog._dragEnterEvent
			self.dialog.globalPacks.dropEvent = Dialog._dropEvent

		elif type_ == 'settings':
			self.dialog = SettingsDialog.Ui_Dialog()
			self.dialog.setupUi(self)

		elif type_ == 'gamerules':
			self.dialog = GamerulesDialog.Ui_Dialog()
			self.dialog.setupUi(self)

		self.setModal(True)
		self.additional_data = None

	def _dragEnterEvent(self, event):
		if event.mimeData().hasUrls():
			event.accept()
		else:
			event.ignore()

	def _dropEvent(self, event):
		files = [unicode(u.toLocalFile()) for u in event.mimeData().urls()]
		for file in files:
			self._call_importer(drangndrop = True, file = file)

	def drop_connect(self, slot):
		self.dialog.globalPacks._call_importer = slot


class QPackWidget(QtWidgets.QWidget):
	def __init__(self, path, name, version, uuid, side):
		super().__init__()
		self.ui = PackWidget.Ui_Form()
		self.ui.setupUi(self)
		self.uuid = uuid
		self.version = version
		self.ui.packVer.setText(str(version))
		self.name = name
		self.ui.packName.setText(name)
		self.path = path
		self.side = side
		if side == 1:
			self.ui.unimport.hide()


class World(QtWidgets.QListWidgetItem):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.worldname = ''


class ClientApp:
	def __init__(self):
		self.appcore = QtWidgets.QApplication(sys.argv)

		self.inethandler = None


		self.values = {
		'servername': '',
		'console_log': [],
		'online': 0,
		'backup_interval': 0,
		'checkupdate_interval': 0,
		'reboot_inteval': 0,
		'startup_action': '',
		'serverprop': None,
		'selected': '',
		'selected_worldinfo': {},
		'players_online': {},
		'world_list': [],
		'gamerules': {}

		}

		self.rpacks = {}
		self.bpacks = {}

		self.serverdata = {
		'ip': None,
		'port': None,
		'password': ''
		}

		self.pending_event_buffer = []
		self.waiting_event = {'event:key:value': 'function'}


		self.confs = config_manager.Config()

		self.logon = Window(LogonForm.Ui_Logon)
		self.panel = Window(ServerPanel.Ui_MainWindow)

		self.logon.setWindowTitle("BDSM")

		self.logon.window.nextb.clicked.connect(self.next_button_logon)
		self.logon.window.ip.returnPressed.connect(self.next_button_logon)
		self.logon.window.port.returnPressed.connect(self.logon.window.ip.setFocus)
		self.logon.window.saves.currentTextChanged.connect(self.change_save)
		self.logon.window.settings.clicked.connect(self.open_settings)

		self.logon_state = 0
		self.logon_onllock = False
		self.dontshow_logon = False
		self.panel_showed = False


		self.logon.window.status.setText('')


		if self.confs.mconf['settings']['autoconnect'] and self.confs.mconf['settings']['current_save']:
			self.create_connection(self.confs.mconf['saves'][self.confs.mconf['settings']['current_save']])
			self.dontshow_logon = True
			return
		elif not len(self.confs.mconf['saves']):
			self.logon.window.saves.hide()
			self.logon.window.hint1.hide()
		elif self.confs.mconf['settings']['current_save'] and len(self.confs.mconf['saves']):
			self.logon.window.saves.setEnabled(True)
			self.logon.window.ip.setText(self.confs.mconf['saves'][self.confs.mconf['settings']['current_save']][0])
			self.logon.window.port.setText(str(self.confs.mconf['saves'][self.confs.mconf['settings']['current_save']][1]))
			self.serverdata['password'] == self.confs.mconf['saves'][self.confs.mconf['settings']['current_save']][2]

	def apprun(self):
		if not self.dontshow_logon:
			self.logon.show()
		self.appcore.exec_()

	def change_save(self, name):

		self.confs.change_settings('current_save', name)


	def next_button_logon(self):
		if self.logon_state == 0:
			self.logon.window.ip.setEnabled(False)
			self.logon.window.port.setEnabled(False)
			self.logon.window.nextb.setEnabled(False)
			self.logon.window.status.setStyleSheet("QLabel { color : black; }")
			self.logon.window.status.setText('Connecting...')
			self.logon.setWindowTitle('BDSM - Connecting...')
			self.create_connection([self.logon.window.ip.text(), int(self.logon.window.port.text())])
		elif self.logon_state == 1:
			self.try_auth(self.logon.window.ip.text())

	def create_connection(self, datalist):
		self.inethandler = inethandler.Handler(datalist[:2], self.connected, self.error, self.readyread_slot, self.disconnected)
		if len(datalist) == 3:
			self.logon_onllock = True
			self.try_auth(datalist[2])

	def connected(self):
		print('a')
		self.logon_state = 1
		self.serverdata['ip'] = self.logon.window.ip.text()
		self.serverdata['port'] = int(self.logon.window.port.text())
		self.logon.setWindowTitle('BDSM - Waiting for password')
		self.logon.window.port.hide()
		self.logon.window.ip.clear()
		self.logon.window.ip.setPlaceholderText('Password')
		if self.serverdata['password']:
			self.logon.window.ip.setText(self.serverdata['password'])
		if not self.logon_onllock:
			self.logon.window.ip.setEnabled(True)
			self.logon.window.nextb.setEnabled(True)
		self.logon.window.status.setText('')
		self.logon.window.hint.setText('Enter password:')

	def disconnected(self):
		print('b')
		self.return_to_logon()

	def error(self, code):
		print('c')
		print(code)
		if self.logon_state == 0:
			self.logon.setWindowTitle('BDSM')
			self.logon.window.ip.setEnabled(True)
			self.logon.window.port.setEnabled(True)
			self.logon.window.nextb.setEnabled(True)
			self.logon.window.status.setText(self.inethandler.socket.errorString())
			self.logon.window.status.setStyleSheet("QLabel { color : red; }")
			self.logon.window.ip.returnPressed.connect(self.next_button_logon)
			self.logon.window.port.returnPressed.connect(self.logon.window.ip.setFocus)
			if self.logon_onllock:
				self.logon_onllock = False
				self.confs.change_settings('current_save', None)

	def try_auth(self, password):
		self.logon.setWindowTitle('BDSM - Checking password')
		self.logon.window.status.setStyleSheet("QLabel { color : black; }")
		self.logon.window.status.setText('Checking password...')
		self.logon.window.ip.setEnabled(False)
		self.logon.window.nextb.setEnabled(False)
		self.inethandler.auth(password, self.auth_result)

	def auth_result(self, result):
		if result == 0:
			self.logon.window.status.setText('Getting informations...')
			self.get_data()
			if self.logon.window.autologin.isChecked():
				self.confs.new_save(self.serverdata['ip'], self.serverdata['port'], self.serverdata['password'])
		elif result == -1:
			self.logon.setWindowTitle('BDSM - Waiting for password')
			self.logon.window.ip.setEnabled(True)
			self.logon.window.nextb.setEnabled(True)
			self.logon.window.status.setText('Password incorrect')
			self.logon.window.status.setStyleSheet("QLabel { color : red; }")

	def readyread_slot(self):
		while len(self.inethandler.buffer):
			event = self.inethandler.get()
			self.event_reader(event)



	def get_data(self):
		self.inethandler.put(proto.Event(name = 'get', data = {'value': 'servername'}))
		self.inethandler.put(proto.Event(name = 'get', data = {'value': 'is_online'}))
		self.inethandler.put(proto.Event(name = 'get', data = {'value': 'backup_interval'}))
		self.inethandler.put(proto.Event(name = 'get', data = {'value': 'checkupdate_interval'}))
		self.inethandler.put(proto.Event(name = 'get', data = {'value': 'reboot_interval'}))
		self.inethandler.put(proto.Event(name = 'get', data = {'value': 'startup_action'}))
		self.inethandler.put(proto.Event(name = 'get', data = {'value': 'selected_world'}))
		self.inethandler.put(proto.Event(name = 'get', data = {'value': 'players_online'}))
		self.inethandler.put(proto.Event(name = 'get', data = {'value': 'worlds'}))
		self.waiting_event['answer:worlds'] = self.go_to_panel
		self.waiting_event['answer:selected_world'] = self.selectedcall


	def selectedcall(self):
		if self.values['selected']:
			self.inethandler.put(proto.Event(name = 'get', data = {'value': 'world_info', 'args': self.values['selected']}))
		else:
			self.event_reader(proto.Event(name = 'world_info', data = {'name': 'None'}))
			self.panel.window.packs.setEnabled(False)
			self.panel.window.gamerules.setEnabled(False)


	def go_to_panel(self):
		self.logon.hide()

		self.logon_state = 2
		self.panel.setWindowTitle(self.values['servername'])
		self.panel.window.console_input.returnPressed.connect(self.send_console)
		self.panel.window.start_stop.clicked.connect(self.send_start_or_stop)
		self.panel.window.restart.clicked.connect(self.send_restart)
		self.panel.window.checkupdates.clicked.connect(self.send_checkupdates)
		self.panel.window.exit.clicked.connect(self.inethandler.disconnect)
		self.panel.window.new.clicked.connect(self.send_newworld)
		self.panel.window.delete.clicked.connect(self.send_rmworld)
		self.panel.window.select.clicked.connect(self.send_select)
		self.panel.window.ban.clicked.connect(self.send_ban)
		self.panel.window.kick.clicked.connect(self.send_kick)
		self.panel.window.set_startup.clicked.connect(self.set_startup)
		self.panel.window.set_checkupdate.clicked.connect(self.set_checkupdate)
		self.panel.window.set_reboot.clicked.connect(self.set_reboot)
		self.panel.window.set_backup.clicked.connect(self.set_backup)
		self.panel.window.open_gamerules.clicked.connect(self.open_gamerules)
		self.panel.window.open_packs.clicked.connect(self.open_packs)


		#default_set
		self.panel.window.levelname.setText('Loading...')
		self.panel.window.console.clear()
		for line in self.values['console_log']:
			if line.startswith('0'):
				line = QtWidgets.QListWidgetItem(line[1:])
				brush = QtGui.QBrush()
				brush.setColor(QtGui.QColor(128, 128, 128))
				line.setForeground(brush)
				self.panel.window.console.addItem(line)
				self.panel.window.console.addItem(line)
			elif line.startswith('1'):
				line = QtWidgets.QListWidgetItem(line[1:])
				self.panel.window.console.addItem(line)
			elif line.startswith('2'):
				line = QtWidgets.QListWidgetItem(line[1:])
				brush = QtGui.QBrush()
				brush.setColor(QtGui.QColor(245, 169, 169))
				line.setForeground(brush)
				self.panel.window.console.addItem(line)

		self.panel.window.players.clear()
		for name in self.values['players_online'].keys():
			self.panel.window.players.addItem(name)

		self.panel.window.worlds.clear()
		for worldname, levelname in self.values['world_list'].items():
			w = World(levelname['levelname'])
			w.worldname = worldname
			self.panel.window.worlds.addItem(w)

		#signal-to-slot
		self.panel.window.players.itemClicked.connect(self.activate_pbuttons)
		self.panel.window.worlds.itemClicked.connect(self.activate_wbuttons)

		self.panel.show()
		self.panel_showed = True


	#Panel slots
	def send_console(self):
		text = self.panel.window.console_input.text()
		self.panel.window.console_input.clear()
		if text == 'changePassword':
			self.set_password()
			return
		elif text == 'servername':
			self.set_servername()
			return
		event = proto.Event(name = 'write_console', data = {'text': text})
		self.inethandler.put(event)

	def send_start_or_stop(self):
		if self.values['online'] == 0:
			self.lock_buttons(True)
			event = proto.Event(name = 'start')
			self.inethandler.put(event)
		elif self.values['online'] == 1:
			self.lock_buttons(True)
			event = proto.Event(name = 'stop')
			self.inethandler.put(event)

	def send_restart(self):
		if self.values['online'] == 1:
			self.lock_buttons(True)
			event = proto.Event(name = 'restart')
		elif self.values['online'] == 0:
			self.panel.window.restart.setEnabled(False)

	def send_checkupdates(self):
		event = proto.Event(name = 'check_updates')
		self.inethandler.put(event)

	def send_newworld(self):
		dio = QtWidgets.QInputDialog()
		dio.setOkButtonText('Create')
		text, ok = dio.getText(self.panel, 'Creating new world', 'Enter world name:')
		if ok:
			event = proto.Event(name = 'new_world', data = {'levelname': text})
			self.inethandler.put(event)

	def send_rmworld(self):
		row = self.panel.window.worlds.currentRow()
		if row:
			item = self.panel.window.worlds.item(row)
			event = proto.Event(name = 'delete_world', data = {'worldname': item.worldname})
			self.inethandler.put(event)

	def send_select(self):
		row = self.panel.window.worlds.currentRow()
		if row:
			item = self.panel.window.worlds.item(row)
			event = proto.Event(name = 'select_world', data = {'worldname': item.worldname})
			self.inethandler.put(event)

	def send_ban(self):
		row = self.panel.window.players.currentRow()
		if row:
			item = self.panel.window.players.item(row)
			event = proto.Event(name = 'ban', data = {'nickname': item.text()})
			self.inethandler.put(event)

	def send_kick(self):
		row = self.panel.window.players.currentRow()
		if row:
			item = self.panel.window.players.item(row)
			event = proto.Event(name = 'kick', data = {'nickname': item.text()})
			self.inethandler.put(event)

	def set_startup(self):
		dio = QtWidgets.QInputDialog()
		item, ok = dio.getItem(self.panel, 'Startup action', 'Choose startup action:', ['Nothing', 'Start'], editable = False)
		if item == 'Start': item = 'start'
		if ok:
			event = proto.Event(name = 'set', data = {'name': 'startup_action', 'value': item})
			self.inethandler.put(event)

	def set_checkupdate(self):
		dio = QtWidgets.QInputDialog()
		dio.setIntMinimum(120)
		dio.setIntValue(self.values['checkupdate_interval'])
		integer, ok = dio.getInt(self.panel, 'Check updates interval', 'Set interval:')
		if ok:
			event = proto.Event(name = 'set', data = {'name': 'checkupdate_interval', 'value': integer})
			self.inethandler.put(event)

	def set_backup(self):
		dio = QtWidgets.QInputDialog()
		dio.setIntMinimum(1)
		dio.setIntValue(round(self.values['backup_interval'] / 3600))
		integer, ok = dio.getInt(self.panel, 'Backup interval', 'Set interval(in hours):')
		if ok:
			event = proto.Event(name = 'set', data = {'name': 'backup_interval', 'value': 3600 * integer})
			self.inethandler.put(event)

	def set_reboot(self):
		dio = QtWidgets.QInputDialog()
		dio.setIntMinimum(1)
		dio.setIntValue(round(self.values['reboot_interval'] / 86400))
		integer, ok = dio.getInt(self.panel, 'Reboot interval', 'Set interval(in days):')
		if ok:
			event = proto.Event(name = 'set', data = {'name': 'reboot_interval', 'value':  86400 * integer})
			self.inethandler.put(event)

	def set_password(self):
		dio = QtWidgets.QInputDialog()
		text, ok = dio.getText(self.panel, 'Change password', 'New password:')
		if ok:
			event = proto.Event(name = 'set', data = {'name': 'password', 'value':  text})
			self.inethandler.put(event)

	def set_servername(self):
		dio = QtWidgets.QInputDialog()
		text, ok = dio.getText(self.panel, 'Change servername', 'New servername:')
		if ok:
			event = proto.Event(name = 'set', data = {'name': 'servername', 'value':  text})
			self.inethandler.put(event)

	def open_gamerules(self):
		self.waiting_event['answer:gamerules'] = self._open_gamerules

	def _open_gamerules(self):
		dio = Dialog('gamerules')
		for key, value in self.values['gamerules'].items():
			if isinstance(value, bool):
				check = QtWidgets.QCheckBox(key, self)
				check.stateChanged.connect(lambda x: self._change_gamerule(key, x))
				check.setChecked(value)
				dio.dialog.verticalLayout.addWidget(check, stretch = 1)
			else:
				label = QtWidgets.QLabel(key + ':', self)
				lineedit = QtWidgets.QLineEdit(self)
				lineedit.setText(str(value))
				lineedit.returnPressed.connect(lambda: self._change_gamerule(key, lineedit.text()))
				dio.dialog.verticalLayout.addWidget(label, stretch = 1)
				dio.dialog.verticalLayout.addWidget(lineedit, stretch = 2)
		dio.open()

	def _change_gamerule(self, rule, state):
		if state == 1:
			state = 'true'
		elif state == 0:
			state = 'false'
		event = proto.Event(name = 'write_console', data = {'text': 'gamerule {} {}'.format(rule, state)})
		self.inethandler.put(event)

	def open_settings(self):
		dio = Dialog('settings')
		dio.dialog.autoconnect.stateChanged.connect(lambda x: self.confs.change_settings('autoconnect', x))
		for i in self.confs.mconf['saves']:
			dio.dialog.saveslist.addItem(i)
		dio.dialog.rmbutton.clicked.connect(lambda: self._rmsave(dio))
		dio.open()

	def _rmsave(self, dialog):
		row = dialog.dialog.saveslist.currentRow()
		if row:
			item = dialog.dialog.saveslist.takeItem(row)
			self.confs.remove_save(item.text())


	def open_packs(self):
		self.inethandler.put(proto.Event(name = 'get', data = {'value': 'rpacks'}))
		self.inethandler.put(proto.Event(name = 'get', data = {'value': 'bpacks'}))
		self.waiting_event['answer:rpacks'] = self._open_packs

	def _open_packs(self):
		print(self.values['selected_worldinfo'])
		dio = Dialog('packs')
		dio.setWindowTitle('Managing world resource packs')
		dio.dialog.hint.setText('{} - Resource packs'.format(self.values['selected_worldinfo']['world']['levelname']))
		dio.additional_data = 'rpacks'
		dio.dialog.apply.hide()
		dio.dialog.discard.hide()
		rpacks = self.rpacks
		world_rpacks = []
		for pack in self.values['selected_worldinfo']['resources']:
			for gindex, gpack in enumerate(rpacks):
				if gpack['uuid'] == pack['pack_id'] and gpack['version'] == pack['version']:
					world_rpacks.append(rpacks.pop(gindex))
					break

		for pack in rpacks:
			item = QtWidgets.QListWidgetItem(dio.dialog.globalPacks)
			packWidget = QPackWidget(pack['path'], pack['name'], pack['version'], pack['uuid'], 0)
			packWidget.ui.action.clicked.connect(lambda: self._pack_action(dio, item))
			packWidget.ui.unimport.clicked.connect(lambda: self._pack_unimport(packWidget))
			dio.dialog.globalPacks.addItem(item)
			dio.dialog.globalPacks.setItemWidget(item, packWidget)

		for pack in world_rpacks:
			item = QtWidgets.QListWidgetItem(dio.dialog.worldPacks)
			packWidget = QPackWidget(pack['path'], pack['name'], pack['version'], pack['uuid'], 1)
			packWidget.ui.action.clicked.connect(lambda: self._pack_action(dio, item))
			packWidget.ui.unimport.clicked.connect(lambda: self._pack_unimport(packWidget.ui))
			dio.dialog.worldPacks.addItem(item)
			dio.dialog.worldPacks.setItemWidget(item, packWidget)
			
		dio.dialog.Import.clicked.connect(lambda: self._import_pack(dio))
		dio.dialog.changetype.clicked.connect(lambda: self._packs_change_context(dialog = dio))
		dio.drop_connect(self._import_pack)

		dio.open()

	def _pack_action(self, dialog, item):
		widget = item.listWidget().itemWidget(item)
		if widget.side == 0:
			dialog.dialog.globalPacks.takeItem(dialog.dialog.globalPacks.row(item))
			dialog.dialog.worldPacks.addItem(item)
			widget.side = 1
			widget.ui.unimport.hide()
			event = proto.Event(name = 'apply_to_world', data = {'worldname': self.values['selected'], 'path': widget.path})
			self.inethandler.put(event)


		elif widget.side == 1:
			dialog.dialog.worldPacks.takeItem(dialog.dialog.globalPacks.row(item))
			dialog.dialog.globalPacks.addItem(item)
			widget.side = 0
			widget.ui.unimport.show()
			event = proto.Event(name = 'discard_from_world', data = {'worldname': self.values['selected'], 'uuid': widget.uuid, 'ver': widget.version})
			self.inethandler.put(event)

	def _pack_unimport(self, widget):
		msg = QtWidgets.QMessageBox()
		msg.setWindowTitle('Remove global pack')
		msg.setText('Are you sure want to remove pack from global?')
		msg.setInformativeText('This action can not be canceled.')
		result = msg.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
		retval = msg.exec_()
		if retval == QtWidgets.QMessageBox.Ok:
			widget.hide()
			event = proto.Event(name = 'unimport', data = {'uuid': widget.uuid.encode(), 'ver': json.dumps(widget.version)})
			self.inethandler.put(event)

	def _packs_change_context(self, dialog):
		if dialog.additional_data == 'rpacks':
			self.inethandler.put(proto.Event(name = 'get', data = {'value': 'rpacks'}))
			packs = self.bpacks
			target = 'behaviors'
			dialog.additional_data = 'bpacks'
			dialog.setWindowTitle('Managing world behavior packs')
			dialog.dialog.changetype.setText('Resource packs')
			dialog.dialog.hint.setText('{} - Behavior packs'.format(self.values['selected_worldinfo']['world']['levelname']))

		elif dialog.additional_data == 'bpacks':
			self.inethandler.put(proto.Event(name = 'get', data = {'value': 'bpacks'}))
			packs = self.rpacks
			target = 'resources'
			dialog.additional_data = 'rpacks'
			dialog.setWindowTitle('Managing world resource packs')
			dialog.dialog.changetype.setText('Behavior packs')
			dialog.dialog.hint.setText('{} - Resource packs'.format(self.values['selected_worldinfo']['world']['levelname']))


		dialog.dialog.globalPacks.clear()
		dialog.dialog.worldPacks.clear()
		world_packs = []

		for pack in self.values['selected_worldinfo'][target]:
			for gindex, gpack in enumerate(packs):
				if gpack['uuid'] == pack['pack_id'] and gpack['version'] == pack['version']:
					world_packs.append(packs.pop(gindex))
					break

		for pack in packs:
			item = QtWidgets.QListWidgetItem(dialog.dialog.globalPacks)
			packWidget = QPackWidget(pack['path'], pack['name'], pack['version'], pack['uuid'], 0)
			packWidget.action.clicked.connect(lambda: self._pack_action(dialog, item))
			packWidget.unimport.clicked.connect(lambda: self._pack_unimport(packWidget))
			dialog.dialog.globalPacks.addItem(item)
			dialog.dialog.globalPacks.setItemWidget(item, packWidget)

		for pack in world_packs:
			item = QtWidgets.QListWidgetItem(dialog.dialog.worldPacks)
			packWidget = QPackWidget(pack['path'], pack['name'], pack['version'], pack['uuid'], 1)
			packWidget.action.clicked.connect(lambda: self._pack_action(dialog, item))
			packWidget.unimport.clicked.connect(lambda: self._pack_unimport(packWidget))
			dialog.dialog.worldPacks.addItem(item)
			dialog.dialog.worldPacks.setItemWidget(item, packWidget)

	def _import_pack(self, dialog = None, drangndrop = False, file = None):
		if not drangndrop:
			file = QtWidgets.QFileDialog.getOpenFileName(dialog, 'Choose file to import', './', 'Minecraft pack file (*.mcpack *.mcaddon)')[0]
		print(file.split('.')[-1])
		if file.split('.')[-1] == u'.mcaddon':
			with zipfile.ZipFile(file, 'r') as mcaddon:
				os.mkdir('./.temp')
				mcaddon.extractall(path = './.temp')
			files = os.listdir('./.temp')
			progr = QtWidgets.QProgressDialog('Uploading files', 'Uploading -/-', 0, 0)
			progr.open()
			for i, en in enumerate(files):
				lent = math.ceil(os.path.getsize(en)/1024)
				progr.setMaximum(lent)
				progr.setCancelButton(None)
				fileno = open(en, 'rb')
				progr.setLabelText('Uploading {}/{}...'.format(i, len(files)))
				self.inethandler.put(proto.Event(name = 'upload', data = {'size': os.path.getsize(en)}), fileno = fileno, callback = progr.setValue)
			self.waiting_event['replyfileno'] = progr.close
			shutil.rmtree('./.temp')

		else:
			fileno =  open(file, 'rb')
			lent = math.ceil(os.path.getsize(file)/1024)
			progr = QtWidgets.QProgressDialog('Uploading file', 'Uploaded 0/{} chuncks...'.format(lent), 0, lent)
			progr.open()
			self.inethandler.put(proto.Event(name = 'upload', data = {'size': os.path.getsize(file)}), fileno = fileno, callback = lambda x: self.progress(progr, lent, x))
			self.waiting_event['replyfileno'] = progr.close

	def progress(self, dialog, lent, value):
		dialog.setValue(value)
		dialog.setLabelText('Uploaded {}/{} chuncks...'.format(value, lent))

	def lock_buttons(self, state):
		if state:
			state = False
		else:
			state = True

		self.panel.window.restart.setEnabled(state)
		self.panel.window.start_stop.setEnabled(state)
		self.panel.window.console_input.setEnabled(state)

	def activate_wbuttons(self):
		self.panel.window.select.setEnabled(True)
		self.panel.window.new.setEnabled(True)
		self.panel.window.delete.setEnabled(True)

	def activate_pbuttons(self):
		self.panel.window.kick.setEnabled(True)
		self.panel.window.ban.setEnabled(True)

	def event_reader(self, event):
		print(event.name, event.data)
		if event.name == 'console':
			self.values['console_log'].append(event.data['line'].decode())
			if self.panel_showed:
				line = event.data['line'].decode()
				if line.startswith('0'):
					line = QtWidgets.QListWidgetItem(line[1:])
					brush = QtGui.QBrush()
					brush.setColor(QtGui.QColor(128, 128, 128))
					line.setForeground(brush)
					self.panel.window.console.addItem(line)
					self.panel.window.console.addItem(line)
				elif line.startswith('1'):
					line = QtWidgets.QListWidgetItem(line[1:])
					self.panel.window.console.addItem(line)
				elif line.startswith('2'):
					line = QtWidgets.QListWidgetItem(line[1:])
					brush = QtGui.QBrush()
					brush.setColor(QtGui.QColor(245, 169, 169))
					line.setForeground(brush)
					self.panel.window.console.addItem(line)

		elif event.name == 'value_changed':
			if event.data['name'] == 'is_online':
				self.values['online'] = event.data['value']

			elif event.data['name'] == 'backup_interval':
				self.values['backup_interval'] = event.data['value']

			elif event.data['name'] == 'checkupdate_interval':
				self.values['checkupdate_interval'] = event.data['value']

			elif event.data['name'] == 'reboot_interval':
				self.values['reboot_interval'] = event.data['value']

			elif event.data['name'] == 'servername':
				self.values['servername'] = event.data['value'].decode()
				if self.panel_showed:
					self.panel.setWindowTitle(event.data['value'].decode())

			elif event.data['name'] == 'rpacks':
				self.rpacks = json.loads(event.data['value'].decode())

			elif event.data['name'] == 'bpacks':
				self.bpacks = json.loads(event.data['value'].decode())

			elif event.data['name'] == 'selected_world':
				self.values['selected'] = event.data['value'].decode()

			elif event.data['name'] == 'worlds':
				self.values['world_list'] = json.loads(event.data['value'].decode())

			elif event.data['name'] == 'world_info':
				self.values['selected_worldinfo'] = json.loads(event.data['value'].decode())
				if self.panel_showed:
					self.panel.window.levelname.setText(json.loads(event.data['value'].decode())['world']['levelname'])

			elif event.data['name'] == 'players_online':
				self.values['players_online'] = jdon.loads(event.data['value'].decode())

			elif event.data['name'] == 'world_backup_list':
				self.values['backups'] = json.loads(event.data['value'].decode())

			elif event.data['name'] == 'prop':
				self.values['serverprop'] = event.data['value'].decode()

			elif event.data['name'] == 'gamerules':
				self.values['gamerules'] = json.loads(event.data['value'].decode())

		elif event.name == 'answer':
			if event.data['name'] == 'is_online':
				self.values['online'] = event.data['value']
				if self.panel_showed:
					if event.data['value']:
						self.panel.window.start_stop.setText('Stop')
					else:
						self.panel.window.start_stop.setText('Start')

			elif event.data['name'] == 'backup_interval':
				self.values['backup_interval'] = event.data['value']

			elif event.data['name'] == 'checkupdate_interval':
				self.values['checkupdate_interval'] = event.data['value']

			elif event.data['name'] == 'reboot_interval':
				self.values['reboot_interval'] = event.data['value']

			elif event.data['name'] == 'servername':
				self.values['servername'] = event.data['value'].decode()
				if self.panel_showed:
					self.panel.setWindowTitle(event.data['value'].decode())

			elif event.data['name'] == 'rpacks':
				self.rpacks = json.loads(event.data['value'].decode())

			elif event.data['name'] == 'bpacks':
				self.bpacks = json.loads(event.data['value'].decode())

			elif event.data['name'] == 'selected_world':
				self.values['selected'] = event.data['value'].decode()

			elif event.data['name'] == 'worlds':
				self.values['world_list'] = json.loads(event.data['value'].decode())

			elif event.data['name'] == 'world_info':
				print(self.values['selected'], json.loads(event.data['value'].decode()))
				if self.values['selected'] in json.loads(event.data['value'].decode()):
					print(True)
					self.values['selected_worldinfo'] = json.loads(event.data['value'].decode())[self.values['selected']]
					self.rpacks = self.values['selected_worldinfo']['resources']
					self.bpacks = self.values['selected_worldinfo']['behaviors']
					if self.panel_showed:
						self.panel.window.levelname.setText(json.loads(event.data['value'].decode())[self.values['selected']]['world']['levelname'])

			elif event.data['name'] == 'players_online':
				self.values['players_online'] = json.loads(event.data['value'].decode())

			elif event.data['name'] == 'world_backup_list':
				self.values['backups'] = json.loads(event.data['value'].decode())

			elif event.data['name'] == 'prop':
				self.values['serverprop'] = event.data['value'].decode()

			elif event.data['name'] == 'gamerules':
				self.values['gamerules'] = json.loads(event.data['value'].decode())

		elif event.name == 'started':
			self.lock_buttons(False)
			self.values['online'] = 1
			self.panel.window.start_stop.setText('Stop')

		elif event.name == 'stopped':
			self.lock_buttons(False)
			self.values['online'] = 0
			self.panel.window.console_input.setEnabled(False)
			self.panel.window.start_stop.setText('Start')

		elif event.name == 'new_world':
			world = World()
			world.worldname = event.data['name'].decode()
			self.inethandler.put(proto.Event(name = 'get', data = {'name': 'world_info', 'args': world.worldname}))
			self.waiting_event['answer:world_info'] = lambda x: self._add_world(world, x)

		elif event.name == 'rem_world':
			count = self.panel.window.worlds.count()
			i = 0
			while i < count-1:
				item = self.panel.window.worlds.item(i)
				if item.worldname == event.data['name'].decode():
					self.panel.window.worlds.takeItem(i)
					break

		elif event.name == 'online_event':
			if event.data['type'] == 0:
				self.panel.window.players.addItem(event.data['name'].decode())
			else:
				count = self.panel.window.players.count()
				i = 0
				while i < count-1:
					item = self.panel.window.players.item(i)
					if item.text() == event.data['name'].decode():
						self.panel.window.players.takeItem(i)
						break

		elif event.name == 'restart':
			self.lock_buttons(True)
			self.waiting_event['stopped'] = lambda: self.lock_buttons(True)

		elif event.name == 'select_world':
			self.values['selected'] == event.data['name'].decode()
			self.inethandler.put(proto.Event(name = 'get', data = {'value': 'world_info', 'args': event.data['name'].decode()}))

		elif event.name == 'updating':
			self.lock_buttons(True)
			self.waiting_event['stopped'] = lambda: self.lock_buttons(True)

		elif event.name == 'pack_imported':
			self.inethandler.put(proto.Event(name = 'get', data = {'value': 'rpacks'}))
			self.inethandler.put(proto.Event(name = 'get', data = {'value': 'bpacks'}))

		elif event.name == 'pack_deleted':
			self.inethandler.put(proto.Event(name = 'get', data = {'value': 'rpacks'}))
			self.inethandler.put(proto.Event(name = 'get', data = {'value': 'bpacks'}))

		elif event.name == 'server.prop_edited':
			self.values['serverprop'] = event.data['text'].decode()

		elif event.name == 'replyfileno':
			self.inethandler.put(proto.Event(name = 'import', data = {'fileno': event.data['fileno']}))

		elif event.name == 'error':
			self.error(event.data['code'])

		print(1)
		if event.name in self.waiting_event:
			print(2)
			self.waiting_event.pop(event.name)()
		elif event.name == 'answer':
			print(3)
			if 'answer:{}'.format(event.data['name']) in self.waiting_event:
				print(4)
				calb = self.waiting_event.pop('answer:{}'.format(event.data['name']))
				if event.data['name'] == 'world_info':
					calb(json.loads(event.data['value'].decode())['world']['levelname'])
				else:
					calb()

	def _add_world(self, world, levelname):
		world.setText(levelname)
		self.panel.window.worlds.addItem(world)

	def return_to_logon(self):
		self.logon_state = 0
		self.panel.hide()
		self.panel_showed = False
		self.logon.window.hint.setText("Enter ip/domen")
		self.logon.window.ip.setPlaceholderText("ex.127.0.0.1")
		self.logon.window.port.setText("19130")
		self.logon.window.nextb.setText("Connect")
		self.logon.window.autologin.setText("Remember me")
		self.logon.window.status.setText("")
		self.logon.window.hint1.setText("Saved ips")
		self.logon.window.settings.setText("Settings")
		self.logon.window.nextb.show()
		self.logon.window.nextb.setEnabled(True)

		self.logon.show()




if __name__ == '__main__':
	client = ClientApp()
	client.apprun()