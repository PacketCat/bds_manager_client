#PROTO
import dataclasses, struct, sys

DEBUG = None
if '-d' in sys.argv:
	DEBUG = True

class Event:
	def __init__(self, name = '', data = {}, from_fd = 0):
		self.name = name
		self.data = data
		self.from_fd = from_fd

CL_HEADERS = {
	'cpassword': struct.pack('>H', 0),
	'cdisconnect': struct.pack('>H', 1),
	'cconsole': struct.pack('>H', 2),
	'cget': struct.pack('>H', 3),
	'cset': struct.pack('>H', 4),
	'cstart': struct.pack('>H', 5),
	'cstop': struct.pack('>H', 6),
	'ckick': struct.pack('>H', 7),
	'cban': struct.pack('>H', 8),
	'crecover': struct.pack('>H', 9),
	'cselect': struct.pack('>H', 10),
	'cnew': struct.pack('>H', 11),
	'cdelete': struct.pack('>H', 12),
	'cupdate': struct.pack('>H', 13),
	'capply': struct.pack('>H', 14),
	'cdiscard': struct.pack('>H', 15),
	'crestart': struct.pack('>H', 16),
	'cimport': struct.pack('>H', 17),
	'cunimport': struct.pack('>H', 18),
	'cexport': struct.pack('>H', 19),
	'cedit': struct.pack('>H', 20),
	'cdownload': struct.pack('>H', 21),
	'cupload': struct.pack('>H', 22)
}

S_HEADERS = {

	'sconnected': struct.pack('>H', 0),
	'sline': struct.pack('>H', 1),
	'sset': struct.pack('>H', 2),
	'sstart': struct.pack('>H', 3),
	'sstop': struct.pack('>H', 4),
	'sgetansw': struct.pack('>H', 5),
	'snewworld': struct.pack('>H', 6),
	'sdelworld': struct.pack('>H', 7),
	'sonline': struct.pack('>H', 8),
	'srestart': struct.pack('>H', 9),
	'sselect': struct.pack('>H', 10),
	'snewpack': struct.pack('>H', 11),
	'sdelpack': struct.pack('>H', 12),
	'supdate': struct.pack('>H', 13),
	'sedit': struct.pack('>H', 14),
	'sdownload': struct.pack('>H', 15),
	'supload': struct.pack('>H', 16),
	'serror': struct.pack('>H', 17)

}
VALUES_IDS = {
	'is_online': 1,
	'password': 14,
	'backup_interval': 2,
	'checkupdate_interval': 3,
	'reboot_interval': 4,
	'servername': 5,
	'startup_action': 6,
	'rpacks': 7,
	'bpacks': 8,
	'selected_world': 9,
	'worlds': 10,
	'world_info': 11,
	'players_online': 12,
	'world_backups_list': 13,
	'prop': 15,
	'gamerules': 16
}





LOG = None

MTU_MAX_SIZE = 1512



def setlog(log):
	global LOG
	LOG = log

def iterdicts(side, value):
	if side:
		dicti = CL_HEADERS
	else:
		dicti = S_HEADERS
	for key, value_ in dicti.items():
		if value_ == value:
			return key

def itervalids(value):
	for key, value_ in VALUES_IDS.items():
		if value_ == value:
			return key

def unpack_from(format, packet, offset):
	unpackd = struct.unpack_from(format, packet, offset)
	if len(unpackd) == 1:
		unpackd = unpackd[0]
	return unpackd

def decode_event(side, packet, fromfd):
	event_key = iterdicts(side, packet[:2])
	if not side:

		if event_key == 'sconnected':
			event =	Event(name='socket_connected', from_fd=fromfd)
			return event

		elif event_key == 'sline':
			data = { 'line': unpack_from('>1510s', packet, 2).rstrip(b'\x00')}
			return Event(name='console', data=data, from_fd=fromfd)
			
		elif event_key == 'sset':
			data = {'name': itervalids(unpack_from('>H', packet, 2))}
			if unpack_from('>H', packet, 2) < 5:
				data['value'] = unpack_from('>L', packet, 4)
			else:
				data['value'] = unpack_from('>1508s', packet, 4).rstrip(b'\x00')
			event = Event(name='value_changed', data=data, from_fd=fromfd)
			return event
			
		elif event_key == 'sstart':
			event =	Event(name='started', from_fd=fromfd)
			return event

		elif event_key == 'sstop':
			event =	Event(name='stopped', from_fd=fromfd)
			return event
			
		elif event_key == 'sgetansw':
			data = {'name': itervalids(unpack_from('>H', packet, 2))}
			if unpack_from('>H', packet, 2) < 5:
				data['value'] = unpack_from('>L', packet, 4)
			else:
				data['value'] = unpack_from('>15120s', packet, 4).rstrip(b'\x00')
			event = Event(name='answer', data=data, from_fd=fromfd)
			return event
			
			
		elif event_key == 'snewworld':
			data = {'name': unpack_from('>1510s', packet, 2).rstrip(b'\x00')}
			event = Event(name = 'new_world', data = data, from_fd = fromfd)
			return event

		elif event_key == 'sdelworld':
			data = {'name': unpack_from('>1510s', packet, 2).rstrip(b'\x00')}
			event = Event(name = 'rem_world', data = data, from_fd = fromfd)
			return event

		elif event_key == 'sonline':
			data = {
			'type': unpack_from('>H', packet, 2),
			'name': unpack_from('>12s', packet, 4).rstrip(b'\x00'),
			'xuid': unpack_from('>Q', packet, struct.calcsize('>HH12s'))
			}
			event = Event(name = 'online_event', data = data, from_fd = fromfd)
			return event

		elif event_key == 'srestart':
			event =	Event(name='restart', from_fd=fromfd)
			return event
			
		elif event_key == 'sselect':
			data = {'name': unpack_from('>1510s', packet, 2).rstrip(b'\x00')}
			event = Event(name = 'select_world', data = data, from_fd = fromfd)
			return event
			
		elif event_key == 'snewpack':
			event =	Event(name='pack_imported', from_fd=fromfd)
			return event

		elif event_key == 'sdelpack':
			event =	Event(name='pack_deleted', from_fd=fromfd)
			return event

		elif event_key == 'supdate':
			event =	Event(name='updating', from_fd=fromfd)
			return event

		elif event_key == 'sedit':
			data = {'text': unpack_from('>5120s', packet, 2).rstrip(b'\x00')}
			event = Event(name = 'server.prop_edited', data = data, from_fd = fromfd)
			return event

		elif event_key == 'sdownload':
			data = {'raw': unpack_from('>15120s', packet, 2).rstrip(b'\x00')}
			event = Event(name = 'send_file_part', data = data, from_fd = fromfd)
			return event

		elif event_key == 'supload':
			data = {'fileno': unpack_from('>H', packet, 2)}
			event = Event(name = 'replyfileno', data = data, from_fd = fromfd)
			return event

		elif event_key == 'serror':
			data = {'code': unpack_from('>h', packet, 2)}
			event = Event(name = 'error', data = data, from_fd = fromfd)
			return event

	else:

		if event_key == 'cpassword':
			data = {'password': unpack_from('>64s', packet, 2)}
			event = Event(name = 'send_password', data = data, from_fd = fromfd)
			return event
			
		elif event_key == 'cdisconnect':
			data = {}
			event = Event(name = 'disconnect', data = data, from_fd = fromfd)
			return event
			
		elif event_key == 'cconsole':
			data = {'text': unpack_from('>1510s', packet, 2).rstrip(b'\x00')}
			event = Event(name = 'write_console', data = data, from_fd = fromfd)
			return event
			
		elif event_key == 'cget':
			data = {'name': unpack_from('>H', packet, 2)}
			if data['name'] == 11 or data['name'] == 13:
				data['args'] = unpack_from('>1510s', packet, 4).rstrip(b'\x00')
			data['name'] = itervalids(data['name'])
			event = Event(name = 'get', data = data, from_fd = fromfd)
			return event
			
		elif event_key == 'cset':
			data = {'name': unpack_from('>H', packet, 2)}
			if data['name'] < 5:
				data['value'] = unpack_from('>L', packet, 4)
			else:
				data['value'] = unpack_from('>1510s', packet, 4).rstrip(b'\x00')
			data['name'] = itervalids(data['name'])
			event = Event(name = 'set', data = data, from_fd = fromfd)
			return event
			
		elif event_key == 'cstart':
			data = {}
			event = Event(name = 'start', data = data, from_fd = fromfd)
			return event
			
		elif event_key == 'cstop':
			data = {}
			event = Event(name = 'stop', data = data, from_fd = fromfd)
			return event
			
		elif event_key == 'ckick':
			data = {'nickname': unpack_from('>12s', packet, 2)}
			event = Event(name = 'kick', data = data, from_fd = fromfd)
			return event

		elif event_key == 'cban':
			data = {'nickname': unpack_from('>12s', packet, 2)}
			event = Event(name = 'ban', data = data, from_fd = fromfd)
			return event
			
		elif event_key == 'crecover':
			data = {'filename': unpack_from('>1510s', packet, 2).rstrip(b'\x00')}
			event = Event(name = 'recover_fr_backup', data = data, from_fd = fromfd)
			return event
			
		elif event_key == 'cselect':
			data = {'worldname': unpack_from('>1510s', packet, 2).rstrip(b'\x00')}
			event = Event(name = 'select_world', data = data, from_fd = fromfd)
			return event
			
		elif event_key == 'cnew':
			data = {'levelname': unpack_from('>1510s', packet, 2).rstrip(b'\x00')}
			event = Event(name = 'new_world', data = data, from_fd = fromfd)
			return event
			
		elif event_key == 'cdelete':
			data = {'worldname': unpack_from('>1510s', packet, 2).rstrip(b'\x00')}
			event = Event(name = 'delete_world', data = data, from_fd = fromfd)
			return event
			
		elif event_key == 'cupdate':
			data = {}
			event = Event(name = 'check_updates', data = data, from_fd = fromfd)
			return event
			
		elif event_key == 'capply':
			data = {
			'worldname': unpack_from('>1510s', packet, 2).rstrip(b'\x00'),
			'path': unpack_from('>1510s', packet, struct.calcsize('>H1510s')).rstrip(b'\x00')
			}
			event = Event(name = 'apply_to_world', data = data, from_fd = fromfd)
			return event
			
		elif event_key == 'cdiscard':
			data = {
			'worldname': unpack_from('>1510s', packet, 2).rstrip(b'\x00'),
			'uuid': unpack_from('>36s', packet, struct.calcsize('>H1510s')),
			'ver': unpack_from('>256s', packet, struct.calcsize('>H1510s36s')).rstrip(b'\x00')
			}
			event = Event(name = 'discard_from_world', data = data, from_fd = fromfd)
			return event
			
		elif event_key == 'crestart':
			data = {}
			event = Event(name = 'restart', data = data, from_fd = fromfd)
			return event
			
		elif event_key == 'cimport':
			data = {'fileno': unpack_from('>L', packet, 2)}
			event = Event(name = 'import', data = data, from_fd = fromfd)
			return event
			
		elif event_key == 'cunimport':
			data = {
			'uuid': unpack_from('>36s', packet, 2),
			'ver': unpack_from('>256s', packet, struct.calcsize('>H36s')).rstrip(b'\x00')
			}
			event = Event(name = 'unimport', data = data, from_fd = fromfd)
			return event
			
		elif event_key == 'cexport':
			data = {
			'worldname': unpack_from('>1510s', packet, 2).rstrip(b'\x00')
			}
			event = Event(name = 'export', data = data, from_fd = fromfd)
			return event
			
		elif event_key == 'cedit':
			data = {
			'prop': unpack_from('>5120s', packet, 2).rstrip(b'\x00')
			}
			event = Event(name = 'prop_edit', data = data, from_fd = fromfd)
			return event
			
		elif event_key == 'cdownload':
			data = {'fileno': unpack_from('>H', packet, 2)}
			event = Event(name = 'download', data = data, from_fd = fromfd)
			return event
			
		elif event_key == 'cupload':
			data = {'size': unpack_from('>L', packet, 2)}
			event = Event(name = 'upload', data = data, from_fd = fromfd)
			return event

def encode_event(side, event):
	data = _encode_event(side, event)
	if DEBUG: print(data)
	header = struct.pack('>H', len(data))
	return header+data

def _encode_event(side, event):
	if side:
		if event.name == 'socket_connected':
			packet = S_HEADERS['sconnected']
			if LOG:
				LOG.debug('main', 'Formed packet of {} event: {}'.format(event.name, packet))
			return packet

		elif event.name == 'console':
			packet = S_HEADERS['sline']
			llen = len(event.data['line'].encode())
			packet += struct.pack('>1510s', event.data['line'].encode())

			if LOG:
				LOG.debug('main', 'Formed packet of {} event: {}'.format(event.name, packet))
			return packet
			
		elif event.name == 'value_changed':
			packet = S_HEADERS['sset']
			if VALUES_IDS[event.data['name']] < 5:
				packet += struct.pack('>HL', VALUES_IDS[event.data['name']], event.data['value'])
			else:
				packet += struct.pack('>H1508s', VALUES_IDS[event.data['name']], event.data['value'].encode())
			if LOG:
				LOG.debug('main', 'Formed packet of {} event: {}'.format(event.name, packet))
			return packet
			
		elif event.name == 'started':
			packet = S_HEADERS['sstart']
			if LOG:
				LOG.debug('main', 'Formed packet of {} event: {}'.format(event.name, packet))
			return packet

		elif event.name == 'stopped':
			packet = S_HEADERS['sstop']
			if LOG:
				LOG.debug('main', 'Formed packet of {} event: {}'.format(event.name, packet))
			return packet
			
		elif event.name == 'answer':
			packet = S_HEADERS['sgetansw']
			if VALUES_IDS[event.data['name']] < 5:
				packet += struct.pack('>HL', VALUES_IDS[event.data['name']], event.data['value'])
			else:
				packet += struct.pack('>H15120s', VALUES_IDS[event.data['name']], event.data['value'].encode())
			if LOG:
				LOG.debug('main', 'Formed packet of {} event: {}'.format(event.name, packet))
			return packet
			
		elif event.name == 'new_world':
			packet = S_HEADERS['snewworld'] + struct.pack('>1510s', event.data['name'].encode())
			if LOG:
				LOG.debug('main', 'Formed packet of {} event: {}'.format(event.name, packet))
			return packet

		elif event.name == 'rem_world':
			packet = S_HEADERS['sdelworld'] + struct.pack('>1510s', event.data['name'].encode())
			if LOG:
				LOG.debug('main', 'Formed packet of {} event: {}'.format(event.name, packet))
			return packet

		elif event.name == 'online_event':
			packet = S_HEADERS['sonline'] + struct.pack('>H12sQ', event.data['type'], event.data['name'].encode(), event.data['xuid'])
			if LOG:
				LOG.debug('main', 'Formed packet of {} event: {}'.format(event.name, packet))
			return packet

		elif event.name == 'restart':
			packet = S_HEADERS['srestart']
			if LOG:
				LOG.debug('main', 'Formed packet of {} event: {}'.format(event.name, packet))
			return packet
			
		elif event.name == 'select_world':
			packet = S_HEADERS['sselect'] + struct.pack('>1510s', event.data['name'].encode())
			if LOG:
				LOG.debug('main', 'Formed packet of {} event: {}'.format(event.name, packet))
			return packet
			
		elif event.name == 'pack_imported':
			packet = S_HEADERS['snewpack']
			if LOG:
				LOG.debug('main', 'Formed packet of {} event: {}'.format(event.name, packet))
			return packet

		elif event.name == 'pack_deleted':
			packet = S_HEADERS['sdelpack']
			if LOG:
				LOG.debug('main', 'Formed packet of {} event: {}'.format(event.name, packet))
			return packet

		elif event.name == 'updating':
			packet = S_HEADERS['supdate']
			if LOG:
				LOG.debug('main', 'Formed packet of {} event: {}'.format(event.name, packet))
			return packet

		elif event.name == 'server.prop_edited':
			packet = S_HEADERS['sedit'] + struct.pack('>5120s', event.data['text'].encode())
			if LOG:
				LOG.debug('main', 'Formed packet of {} event: {}'.format(event.name, packet))
			return packet

		elif event.name == 'send_file_part':
			packet = S_HEADERS['sdownload'] + struct.pack('>15120s', event.data['raw'])
			if LOG:
				LOG.debug('main', 'Formed packet of {} event: {}'.format(event.name, packet))
			return packet

		elif event.name == 'replyfileno':
			packet = S_HEADERS['supload'] + struct.pack('>H', event.data['fileno'])
			if LOG:
				LOG.debug('main', 'Formed packet of {} event: {}'.format(event.name, packet))
			return packet

		elif event.name == 'error':
			packet = S_HEADERS['serror'] + struct.pack('>h', event.data['code'])
			if LOG:
				LOG.debug('main', 'Formed packet of {} event: {}'.format(event.name, packet))
			return packet
		else:
			print(event.name, event.data)
			raise Exception('ebalo zavali')

	else:

		if event.name == 'send_password':
			packet = CL_HEADERS['cpassword'] + struct.pack('>64s', event.data['password'])
			return packet
			
		elif event.name == 'disconnect':
			packet = CL_HEADERS['cdisconnect']
			return packet
			
		elif event.name == 'write_console':
			packet = CL_HEADERS['cconsole'] + struct.pack('>1510s', event.data['text'].encode())
			return packet
			
		elif event.name == 'get':
			packet = CL_HEADERS['cget']
			if VALUES_IDS[event.data['value']] == 11 or VALUES_IDS[event.data['value']] == 13:
				packet += struct.pack('>H1510s', VALUES_IDS[event.data['value']], event.data['args'].encode())
			else:
				packet += struct.pack('>H', VALUES_IDS[event.data['value']])
			return packet
			
		elif event.name == 'set':
			packet = CL_HEADERS['cset']
			if VALUES_IDS[event.data['name']] < 5:
				packet += struct.pack('>HL', VALUES_IDS[event.data['name']], event.data['value'])
			else:
				packet += struct.pack('>H1510s', VALUES_IDS[event.data['name']], event.data['value'].encode())
			if LOG:
				LOG.debug('main', 'Formed packet of {} event: {}'.format(event.name, packet))
			return packet
			
		elif event.name == 'start':
			packet = CL_HEADERS['cstart']
			if LOG:
				LOG.debug('main', 'Formed packet of {} event: {}'.format(event.name, packet))
			return packet
			
		elif event.name == 'stop':
			packet = CL_HEADERS['cstop']
			if LOG:
				LOG.debug('main', 'Formed packet of {} event: {}'.format(event.name, packet))
			return packet
			
		elif event.name == 'kick':
			packet = CL_HEADERS['ckick'] + struct.pack('>12s', event.data['nickname'].encode())
			if LOG:
				LOG.debug('main', 'Formed packet of {} event: {}'.format(event.name, packet))
			return packet
			
		elif event.name == 'ban':
			packet = packet = CL_HEADERS['cban'] + struct.pack('>12s', event.data['nickname'].encode())
			if LOG:
				LOG.debug('main', 'Formed packet of {} event: {}'.format(event.name, packet))
			return packet
			
		elif event.name == 'recover_fr_backup':
			packet = CL_HEADERS['crecover'] + struct.pack('>1510s', event.data['filename'].encode())
			if LOG:
				LOG.debug('main', 'Formed packet of {} event: {}'.format(event.name, packet))
			return packet
			
		elif event.name == 'select_world':
			packet = CL_HEADERS['cselect'] + struct.pack('>1510s', event.data['worldname'].encode())
			if LOG:
				LOG.debug('main', 'Formed packet of {} event: {}'.format(event.name, packet))
			return packet
			
		elif event.name == 'new_world':
			packet = CL_HEADERS['cnew'] + struct.pack('>1510s', event.data['levelname'].encode())
			if LOG:
				LOG.debug('main', 'Formed packet of {} event: {}'.format(event.name, packet))
			return packet
			
		elif event.name == 'delete_world':
			packet = CL_HEADERS['cdelete'] + struct.pack('>1510s', event.data['worldname'].encode())
			if LOG:
				LOG.debug('main', 'Formed packet of {} event: {}'.format(event.name, packet))
			return packet
			
		elif event.name == 'check_updates':
			packet = CL_HEADERS['cupdate']
			if LOG:
				LOG.debug('main', 'Formed packet of {} event: {}'.format(event.name, packet))
			return packet
			
		elif event.name == 'apply_to_world':
			packet = CL_HEADERS['capply'] + struct.pack('>1510s1510s', event.data['worldname'].encode(), event.data['path'].encode())
			if LOG:
				LOG.debug('main', 'Formed packet of {} event: {}'.format(event.name, packet))
			return packet
			
		elif event.name == 'discard_from_world':
			packet = CL_HEADERS['cdiscard'] + struct.pack('>1510s36s256s', event.data['worldname'].encode(), event.data['uuid'].encode(), event.data['ver'].encode())
			if LOG:
				LOG.debug('main', 'Formed packet of {} event: {}'.format(event.name, packet))
			return packet
			
		elif event.name == 'restart':
			packet = CL_HEADERS['crestart']
			if LOG:
				LOG.debug('main', 'Formed packet of {} event: {}'.format(event.name, packet))
			return packet
			
		elif event.name == 'import':
			packet = CL_HEADERS['cimport'] + struct.pack('>L', event.data['fileno'])
			if LOG:
				LOG.debug('main', 'Formed packet of {} event: {}'.format(event.name, packet))
			return packet
			
		elif event.name == 'unimport':
			packet = CL_HEADERS['cunimport'] + struct.pack('>36s256s', event.data['uuid'], event.data['ver'].encode())
			if LOG:
				LOG.debug('main', 'Formed packet of {} event: {}'.format(event.name, packet))
			return packet
			
		elif event.name == 'export':
			packet = CL_HEADERS['cexport'] + struct.pack('>1510s', self.data['worldname'])
			if LOG:
				LOG.debug('main', 'Formed packet of {} event: {}'.format(event.name, packet))
			return packet
			
		elif event.name == 'prop_edit':
			packet = CL_HEADERS['cedit'] + struct.pack('>5120s', event.data['prop'])
			if LOG:
				LOG.debug('main', 'Formed packet of {} event: {}'.format(event.name, packet))
			return packet
			
		elif event.name == 'download':
			packet = CL_HEADERS['cdownload'] + struct.pack('>H', event.data['fileno'])
			if LOG:
				LOG.debug('main', 'Formed packet of {} event: {}'.format(event.name, packet))
			return packet
			
		elif event.name == 'upload':
			packet = CL_HEADERS['cupload'] + struct.pack('>L', event.data['size'])
			if LOG:
				LOG.debug('main', 'Formed packet of {} event: {}'.format(event.name, packet))
			return packet

		else:
			print(event.name, event.data)
			raise Exception('ebalo zavali')