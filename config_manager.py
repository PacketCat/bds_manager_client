import json, os

class Config:
	def __init__(self):
		if not os.path.exists('bdsm.json'):
			self.mconf = \
			{
			"version": "0.0.1",
			"settings":
				{
					"autoconnect": False,
					"current_save": None,
					"d": False
				},
			"saves": {}
			}
		else:
			with open('bdsm.json', 'r') as conf:
				self.mconf = json.load(conf)

	def _sync(self):
		with open('bdsm.json', 'w') as confw:
			json.dump(self.mconf, confw)

	def change_settings(self, param, value):
		self.mconf['settings'][param] = value
		self._sync()

	def new_save(self, ip, port, passw):
		self.mconf['saves'].append({ip+str(port): (ip, port, passw)})
		self.change_settings('current_save', ip+str(port))
		self._sync()

	def remove_save(self, name):
		self.mconf['saves'].pop(name)
		self._sync()
