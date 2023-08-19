#!/usr/bin/python3

import json
import asyncio
import solaredge_modbus
import aiohttp
from datetime import datetime

##################################################################################
HEALTHCHECKS_IO_URL = ""

INTERVAL = 0 #SECONDS
READTIMEOUT = 5 #SECONDS

LEADER_HOST = "localhost"
LEADER_PORT = 9000

PHASE_COLOUR = "RED"
LEADER_ENABLED = 1
LEADER_STORAGE_ENABLED = 1
METER_ENABLED = 1
BATTERY1_ENABLED = 1
BATTERY2_ENABLED = 1

EMONCMS_API_KEY = ""
EMONCMS_HEADERS = {"Authorization": f"Bearer {EMONCMS_API_KEY}"}
EMONCMS_SERVER_IP = ""

##################################################################################

async def health_check(session, health, status):
	try:
		url = (health)
		payload = {
			"status": status,
			}
		async with session.post(url, json=payload, timeout=1) as response:
			response.raise_for_status()
			if response.status != 200:
				print("Error sending health check ping to healthchecks.io")
	except aiohttp.ClientError as e:
		print(f"Health check error occurred: {e}")

async def post_to_emoncms(session, node_name, data):
	url = f"http://{EMONCMS_SERVER_IP}/input/post.json?node={node_name}&fulljson={data}"
	#time = datetime.now()
	#print(f"POSTING: {node_name}: {time}")
	async with session.post(url, headers=EMONCMS_HEADERS) as response:
		response.raise_for_status()
		if response.status != 200:
			print(f"Error posting data to EmonCMS: {response.content}")
			await health_check(session, HEALTHCHECKS_IO_URL+"/log", f"Error posting data to EmonCMS: {response.content}")

async def get_device_data(session, data, type):
	master = solaredge_modbus.Inverter(host=LEADER_HOST, port=LEADER_PORT, retries=3, timeout=5, unit=1)
	if type == "leader":
		#t1 = datetime.now()
		data = master.read_all()
		#t2 = datetime.now() - t1
		#print(f"{type} {t2}")
		if not master.connected():
			data = {'power_ac': 0}
			print(f"{type}: not connected")
			return data
		if len(data) < 52 and len(data) != 1:
			print(f"Incomplete data for LEADER")
			await health_check(session, HEALTHCHECKS_IO_URL+"/log", f"Incomplete data for {type}")
			raise ValueError
		return data
	if type == "storage":
		data = solaredge_modbus.StorageInverter(parent=master).read_all()
		if not master.connected():
			data = {'storage_ac_charge_limit': 0}
			print(f"{type}: not connected")
			return data
		if len(data) < 12 and len(data) != 1:
			print(f"Incomplete data for STORAGE")
			await health_check(session, HEALTHCHECKS_IO_URL+"/log", f"Incomplete data for {type}")
			raise ValueError
		return data
	if type == "meter":
		data = solaredge_modbus.Meter(parent=master, offset=0).read_all()
		if not master.connected():
			data = {'l1_power': 0}
			print(f"{type}: not connected")
			return data
		if len(data) < 79 and len(data) != 1:
			print(f"Incomplete data for METER")
			await health_check(session, HEALTHCHECKS_IO_URL+"/log", f"Incomplete data for {type}")
			raise ValueError
		return data
	if type == "battery1":
		await asyncio.sleep(0.1)
		data = master.batteries()["Battery1"].read_all()
		if not master.connected():
			data = {'instantaneous_power': 0}
			print(f"{type}: not connected")
			return data
		if len(data) < 23 and len(data) != 1:
			print(f"Incomplete data for BATTERY1")
			await health_check(session, HEALTHCHECKS_IO_URL+"/log", f"Incomplete data for {type}")
			raise ValueError
		return data
	if type == "battery2":
		await asyncio.sleep(0.1)
		data = master.batteries()["Battery2"].read_all()
		if not master.connected():
			data = {'instantaneous_power': 0}
			print(f"{type}: not connected")
			return data
		if len(data) < 23 and len(data) != 1:
			print(f"Incomplete data for BATTERY2")
			await health_check(session, HEALTHCHECKS_IO_URL+"/log", f"Incomplete data for {type}")
			raise ValueError
		return data
	else:
		#return data.read_all()
		raise ValueError

# Device configurations
devices = {
	"LEADER": {
		"enabled": LEADER_ENABLED,
		"storage": LEADER_STORAGE_ENABLED,
		"read_storage": 1,
		"node_name": f"{PHASE_COLOUR}-INVERTER",
		"data_source": "leader",
		"storage_source": "storage"
	},
	"METER": {
		"enabled": METER_ENABLED,
		"read_storage": 0,
		"node_name": f"{PHASE_COLOUR}-METER",
		"data_source": "meter"
	},
	"BATTERY1": {
		"enabled": BATTERY1_ENABLED,
		"read_storage": 0,
		"node_name": f"{PHASE_COLOUR}-BATTERY1",
		"data_source": "battery1"
	},
	"BATTERY2": {
		"enabled": BATTERY2_ENABLED,
		"read_storage": 0,
		"node_name": f"{PHASE_COLOUR}-BATTERY2",
		"data_source": "battery2"
	}
}

async def process_device_data(device_name, device_config, session):
	try:
		task = asyncio.create_task(asyncio.wait_for(get_device_data(session, 0, device_config["data_source"]), timeout=READTIMEOUT))
		values = await task
		#print(f"{device_config['data_source']} {datetime.now()}")
		processed_data = {}
		for k, v in values.items():
			if (isinstance(v, int) or isinstance(v, float)) and "_scale" not in k:
				k_split = k.split("_")
				scale = 0
				if f"{k_split[len(k_split) - 1]}_scale" in values:
					scale = values[f"{k_split[len(k_split) - 1]}_scale"]
				elif f"{k}_scale" in values:
					scale = values[f"{k}_scale"]
				processed_data.update({k: float(v * (10 ** scale))})
				if device_config["data_source"] == "meter":
					if (isinstance(v, int) or isinstance(v, float)):
						if k == "l1_power" or k == "l2_power" or k == "l3_power":
							processed_data.update({k: float(v * (-1))})
				if device_config["data_source"] == "battery1" or device_config["data_source"] == "battery2":
					if (isinstance(v, int) or isinstance(v, float)):
						if k != "instantaneous_power":
							if v < 0:
								v = 0
								processed_data.update({k: float(v)})
		if device_config["data_source"] == "meter":
			sum_of_powers = sum(v for v in [processed_data.get('l1_power'), processed_data.get('l2_power'), processed_data.get('l3_power')] if isinstance(v, (int, float)))
			import_data, export_data = (sum_of_powers, 0) if sum_of_powers > 0 else (0, sum_of_powers)
			data = {f"{PHASE_COLOUR}-IMPORT": import_data, f"{PHASE_COLOUR}-EXPORT": export_data, f"{PHASE_COLOUR}-CONSUMPTION": 0}
			processed_data.update(data)

		if device_config["data_source"] == "battery1" or device_config["data_source"] == "battery2":
			if 'soe' in processed_data:
				if 'available_energy' in processed_data:
					soe_kwh = (processed_data['soe']/100) * processed_data['available_energy']
					data = {"soe_kwh": soe_kwh}
					processed_data.update(data)
					if 'instantaneous_power' in processed_data:
						instantaneous_power = processed_data['instantaneous_power']
						if instantaneous_power < 0: #discharging when below 0
							remaining_hours = (soe_kwh / instantaneous_power)
							data = {"remaining_hours": remaining_hours}
							#print(f"Hours until empty: {remaining_hours}")
							processed_data.update(data)
						if instantaneous_power > 0: #charging when above 0
							remaining_hours = ((processed_data['available_energy'] - soe_kwh) / instantaneous_power)
							data = {"remaining_hours": remaining_hours}
							#print(f"Hours until full: {remaining_hours}")
							processed_data.update(data)
						if instantaneous_power == 0:
						#else:
							data = {"remaining_hours": 8736}
							processed_data.update(data)
		if device_config["read_storage"]:
			if device_config["storage"]:
				storagetask = asyncio.create_task(get_device_data(session, 0, device_config["storage_source"]))
				storagevalues = await storagetask
				processed_data.update(storagevalues)

		node_name = device_config["node_name"]
		data = json.dumps(processed_data, default=float)
		return node_name, data

	except ValueError:
		pass

	except asyncio.TimeoutError:
		print(f"{device_name} Timeout error occurred!")
		await health_check(session, HEALTHCHECKS_IO_URL+"/log", f"{device_name} Timeout error occurred!")

async def update_info_and_display(session):
	tasks = []
	enabled_devices = sum(1 for device_config in devices.values() if device_config["enabled"])
	#print(f"Number of enabled devices: {enabled_devices}")
	successful_tasks = 0
	for device_name, device_config in devices.items():
		if device_config["enabled"]:
			task = asyncio.create_task(process_device_data(device_name, device_config, session))
			tasks.append(task)
			result = await task
			if result is not None:
				successful_tasks += 1
	#print(f"Number of successful tasks: {successful_tasks}")
	if successful_tasks == enabled_devices:
		for task in asyncio.as_completed(tasks):
			result = await task
			if result is not None:
				node_name, data = result
				#node_name, data = await task  # Get the node_name value from the completed task
				task = asyncio.create_task(post_to_emoncms(session, node_name, data))
	else:
		print(f"Successful tasks ({successful_tasks}) does not match number of enabled devices ({enabled_devices})")
		await health_check(session, HEALTHCHECKS_IO_URL+"/log", f"Successful tasks ({successful_tasks}) does not match number of enabled devices ({enabled_devices})")
		print("NOT POSTING")
	try:
		await asyncio.gather(*tasks)
		await health_check(session, HEALTHCHECKS_IO_URL, f"Success")

	except asyncio.TimeoutError:
		print(f"{device_name} Timeout error occurred!")
		await health_check(session, HEALTHCHECKS_IO_URL+"/log", f"{device_name} Timeout error occurred!")
	except Exception as e:
		if "Modbus Error" in str(e) and "Connection unexpectedly closed" in str(e):
			#pass  # Ignore this specific exception
			await health_check(session, HEALTHCHECKS_IO_URL+"/log", f"Error updating info: {e}")
		elif "Server disconnected" in str(e):
			pass
		else:
			print(f"Error updating info: {e}")
			await health_check(session, HEALTHCHECKS_IO_URL+"/log", f"Error updating info: {e}")


async def main():
	print("Starting up...")
	async with aiohttp.ClientSession() as session:
		await update_info_and_display(session)
		print("Running.")
		while True:
			try:
				await asyncio.sleep(INTERVAL)
				await update_info_and_display(session)
			except asyncio.TimeoutError:
				print(f"Timeout error occurred!")
				await health_check(session, HEALTHCHECKS_IO_URL+"/log", f"Timeout error occurred in main")
			except Exception as e:
				if "Modbus Error" in str(e) and "Connection unexpectedly closed" in str(e):
					await health_check(session, HEALTHCHECKS_IO_URL+"/log", f"Error in main: {e}")
					#pass  # Ignore this specific exception
				elif "name 'session' is not defined" in str(e):
					#await health_check(session, HEALTHCHECKS_IO_URL+"/log", f"Error in main: {e}")
					pass  # Ignore this specific exception
				elif "Server disconnected" in str(e):
					pass
				else:
					print(f"Error in main: {e}")
					await health_check(session, HEALTHCHECKS_IO_URL+"/log", f"Error in main: {e}")

if __name__ == "__main__":
	asyncio.run(main())
