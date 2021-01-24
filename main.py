#!/usr/bin/env python3
from collections import defaultdict, deque
from typing import Deque, DefaultDict, Dict, List

from aiohttp import web

app = web.Application()
routes = web.RouteTableDef()


class Measurement:
	def __init__(self, timestamp: int, data: bytes):
		self.timestamp, self.data = timestamp, data


# typedef
PublicKey = bytes
Password = str

datasets: DefaultDict[PublicKey, Deque[Measurement]] = defaultdict(lambda: deque(maxlen=24*60))		# max 24h of data
dataset_pass: Dict[PublicKey, Password] = {}


@routes.post('/measurement')
async def get_measurements(req: web.Request):
	# set - dataset public keys, newer_than (optional) - min ts for measurements
	data = await req.post()
	if not 'set' in data:
		raise web.HTTPBadRequest()

	try:
		min_ts = int(data['newer_than']) if 'newer_than' in data else 0
	except Exception:
		raise web.HTTPBadRequest()

	if data['set'] not in datasets:
		raise web.HTTPNotFound()

	out: List[bytes] = []
	for m in datasets[data['set']]:
		if m.timestamp > min_ts:
			out.append(m.data)

	return web.json_response(out)


@routes.post('/add_measurement')
async def add_measurement(req: web.Request):
	# ts - timestamp, pw - dataset upload password, set - dataset public key, data - measurement encrypted data
	post = await req.post()
	print(post)

	if not ('set' in post and 'pw' in post and 'ts' in post and 'data' in post):
		raise web.HTTPBadRequest()

	try:
		ts = int(post['ts'])
	except Exception:
		raise web.HTTPBadRequest()

	if post['set'] in dataset_pass:
		if dataset_pass[post['set']] != post['pw']:
			raise web.HTTPForbidden()
	else:
		dataset_pass[post['set']] = post['pw']

	datasets[post['set']].append(Measurement(ts, post['data']))

app.add_routes(routes)


if __name__ == '__main__':
	web.run_app(app, port=9999)

