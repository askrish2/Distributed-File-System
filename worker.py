from socket import *
import re
import time
import numpy as np
from threading import Thread
import os
import random
from threading import Lock
import sys
import subprocess
import ast
import marshal
import datetime
import logging
import copy
import time
from multiprocessing.dummy import Pool as ThreadPool
import paramiko
import shutil
from stat import *

MACHINE = 'fa17-cs425-g25-{server_id}.cs.illinois.edu'
JOINMSG = 'join-{server_name}'
STR_DATETIME = '%Y-%m-%d %H:%M:%S.%f'
all_members = ['01', '02', '04', '05', '06', '07', '08', '09', '10']
FINISH = '02'

K=3
SERVERNAME = sys.argv[1]
num_inactive = 0
members = []
pre = ''
suc = ''
myHost = ''
memberlist = {}
failed = {}
replicas = {}
file_times = {}

replica_time = None
SSHPort = 2015
REPLICA_PORT = 2016
CREATE_REP = 2017
UPDATE_Port = 2018
masterPort = 2001
serverPort = 2002
GET_PORT = 2019
JOINPORT = 2003
GOSSPORT = 2004
GOSSREP_PORT = 2020

replica_time_mutex = Lock()
members_mutex = Lock()
pre_mutex = Lock()
suc_mutex = Lock()
memberlist_mutex = Lock()
failed_mutex = Lock()
replicas_mutex = Lock()

num_inactive_mutex = Lock()
worker_id_mutex = Lock()
partition_nums_mutex = Lock()
partition_nodes_mutex = Lock()
nodes_mutex = Lock()
peer_messages_mutex = Lock()
curr_messages_mutex = Lock()
next_messages_mutex = Lock()
finish_mutex = Lock()

class thread(threading.Thread):

    def __init__(self, thread_ID):
        threading.Thread.__init__(self)
        self.thread_ID = thread_ID
    def run(self):
        barrier.wait()

class worker:

	def __init__(self, worker_id, partition_nums, partition_nodes, divs):
		self.worker_id = worker_id
		self.partition_nums = partition_nums
		self.partition_nodes = partition_nodes
		self.divs = divs
		self.nodes = {}
		self.peer_messages = {}
		self.curr_messages = {}
		self.next_messages = {}

	def load_input(class_name):

		for (v1,v2) in self.divs[self.worker_id]:
			load_pair(v1, v2, class_name)
			load_pair(v2, v1, class_name)

		send_message():	

		for (v_id, v) in self.nodes:
			self.curr_messages[v_id] = []

	def load_pair(v1, v2, class_name):

		self.peer_messages = {}

		v = class_name(0, v1, [v2])
		if own_node(v1) and v1 not in self.nodes:
			self.nodes[v1] = v
		elif own_node(v1) and v1 in self.nodes:
			self.nodes[v1].outgoing_edges.append(v2)
		else:
			owner = find_node_owner(v1)
			message = (v, "load")
			if owner not in peer_messages:
				self.peer_messages[owner] = [message]
			else:
				self.peer_messages[owner].append(message)

		send_message()

	def reload(all_nodes):

		nodes_mutex.acquire()
		self.nodes = []
		nodes_mutex.release()

		partition_nums_mutex.acquire()
		worker_id_mutex.acquire()
		for num in partition_nums[self.worker_id]:
			partition_nodes_mutex.acquire()
			for node in partition_nodes[num]:
				nodes_mutex.acquire()
				v = all_nodes[node]
				self.nodes[node] = v
				nodes_mutex.release()
			partition_nodes.release()
		worker_id_mutex.release()
		partition_nums_mutex.release()

	def own_node(v):
		partition_nums_mutex.acquire()
		worker_id_mutex.acquire()
		for num in self.partition_nums[self.worker_id]:
			partition_nodes_mutex.acquire()
			if v in self.partition_nodes[num]:
				partition_nodes_mutex.release()
				worker_id_mutex.release()
				partition_nums_mutex.release()
				return True
			partition_nodes_mutex.release()
		worker_id_mutex.release()
		partition_nums_mutex.release()
		return False

	def find_node_owner(v):

		partition_nums_mutex.acquire()
		for (worker, num) in partition_nums.items():
			partition_nodes_mutex.acquire()
			for arr in partition_nodes[num]:
				if v in arr:
					partition_nodes_mutex.release()
					partition_nums_mutex.release()
					return worker
			partition_nodes_mutex.release()
		partition_nums_mutex.release()

	def receive_message():
		sock = socket(AF_INET, SOCK_DGRAM)
		server_addr = (myHost, serverPort)
		sock.bind(server_addr)
		while 1:
			try:
		   		data, address = sock.recvfrom(4096)
		   		if data:
			   		for (vertex, message) in data:
						if "load" in message:
							nodes_mutex.acquire()
							self.nodes[vertex.vertex_id] = vertex
							nodes_mutex.release()
							continue
				
						if "halt" in message[0]:
							num_inactive += 1

						next_messages_mutex.acquire()
						if vertex not in self.next_messages:
							self.next_messages[vertex] = message
						else:
							self.next_messages[vertex] += message
						next_messages_mutex.release()
				else:
					break
			except error:
		   		break

	def send_master_ack(message):
		d = socket(AF_INET, SOCK_DGRAM)
		finish_mutex.acquire()
        serverHost = (MACHINE.format(FINISH), masterPort)
        FINISH = '03'
        finish_mutex.release()
		try:
        	d.sendto(message, serverHost)
		except error:
			break
		finally:
        	d.close()

	def send_message():
		peer_messages_mutex.acquire()
		for (owner, message) in self.peer_messages.items():
        	d = socket(AF_INET, SOCK_DGRAM)
            serverHost = (MACHINE.format(owner), serverPort)
			try:
				data = marshal.dumps(message)
	        	d.sendto(data, serverHost)
			except error:
				break
			finally:
				self.peer_messages.remove((owner, message))
	        	d.close()
	    peer_messages_mutex.release()

	def listen_master_requests():
		sock = socket(AF_INET, SOCK_DGRAM)
		server_addr = (myHost, masterPort)
		sock.bind(server_addr)
		while 1:
			try:
		   		data, address = sock.recvfrom(4096)
		   		if data:
		   			data = marshal.loads(data)
					if ("launch", class_name) in data:
						thread = Thread(target=launch_nodes, args=(class_name,))
					    thread.daemon = True
					    thread.start()
					elif "output":
						thread = Thread(target=output_results)
					    thread.daemon = True
					    thread.start()
					elif ("update", nodes) in data:
						thread = Thread(target=add_new_nodes, args=(nodes,))
					    thread.daemon = True
					    thread.start()
					break
			except error:
		   		break

	def launch_nodes(class_name):

		load_input(class_name)

		barrier = threading.Barrier(len(partition_nums)+1)
		for num in partition_nums:
			thread = Thread(target=superstep, args=(partition,))
    		thread.daemon = True
    		thread.start()

    	barrier.wait()

    	peer_messages_mutex.acquire()
    	if len(self.peer_messages) > 0 and len(self.peer_messages) < 100:
    		send_message()
    	peer_messages_mutex.release()


    	nodes_mutex.acquire()
    	next_messages_mutex.acquire()
    	num_inactive_mutex.acquire()
    	send_master_ack(("launch", (len(self.nodes) - num_inactive) + len(self.next_messages)))
    	num_inactive_mutex.release()
    	next_messages_mutex.release()
    	nodes_mutex.release()

	def superstep(partition):

		partition_nodes_mutex.acquire()
		for node in self.partition_nodes[partition]:
			nodes_mutex.acquire()
			v = self.nodes[node]
			nodes_mutex.release()
			if v.active:
				nodes_mutex.acquire()
				curr_messages_mutex.acquire()
				vertex_messages = v.compute(v.vertex_val, self.curr_messages[node], v.outgoing_edges, self.nodes)
				curr_messages_mutex.release()
				nodes_mutex.release()

				process_vertex_messages(vertex_messages)
				peer_messages_mutex.acquire()
				if len(self.peer_messages) >= 100:
					thread = Thread(target=send_message)
				    thread.daemon = True
				    thread.start()
				peer_messages_mutex.release()
		partition_nodes_mutex.release()
	
		curr_messages_mutex.acquire()
		next_messages_mutex.acquire()
		self.curr_messages = list(self.next_messages)
		self.next_messages = []
		next_messages_mutex.release()
		curr_messages_mutex.release()

	def process_vertex_messages(vertex_messages):
		for (vertex, message) in vertex_messages:
			if own_node(vertex):
				next_messages_mutex.acquire()
				self.next_messages[vertex].append(message)
				next_messages_mutex.release()

			else:
				owner = find_node_owner(vertex)
				peer_messages_mutex.acquire()
				self.peer_messages[owner] = message
				peer_messages_mutex.release()

	def add_new_nodes(node_list):

		nodes_mutex.acquire()
		for node in self.nodes:
			self.nodes[node].vertex_val = 0
		nodes_mutex.release()

		partition_nums_mutex.acquire()
		for num in self.partition_nums:
			partition_nodes_mutex.acquire()
			for node in self.partition_nodes[num]:
				nodes_mutex.acquire()
				if node not in self.nodes:
					v = node_list[node]
					v.vertex_val = 0
					self.nodes[node] = v
				nodes_mutex.release()
			partition_nodes_mutex.release()
		partition_nums_mutex.release()

		send_master_ack("update")

	def output_results():
		with open('output' + str(SERVERNAME) + '.txt', 'r') as f:
			nodes_mutex.acquire()
			for (node, vertex) in self.nodes.items():
				f.write((vertex_val, vertex_id))
			nodes_mutex.release()
		put('output' + str(SERVERNAME) + '.txt', 'output' + str(SERVERNAME) + '.txt')
		send_master_ack("output")

	def get(filename):
		replicas_mutex.acquire()
		servers = replicas[filename]
		replicas_mutex.release()
		if filename not in replicas:
			print "the file is not available"
			return
		if SERVERNAME in servers:
			return
		N = 6
		index  = 0
		latest_server = None
		latest_time = None
		for server in servers:
			if index>=math.floor(N/2 +1):
				break
			sock = socket(AF_INET, SOCK_DGRAM)
			sock.settimeout(3)
			address = MACHINE.format(server_id=member)
			sock_send = marshal.dumps(filename)
			try:
				sock.sendto(sock_send, (address, GET_PORT))
				try:
					response, address = sock.recvfrom(4096)
					if response:
						(time, server) = marshal.loads(response)
						time = datetime.datetime.strptime(time, STR_DATETIME)
						if latest_server == None or time>latest_time:
							latest_time = time
							latest_server = server
						index+1
				except Exception as e:
                	continue
        	except Exception as e:
            	continue
			sock.close()

def send_get(filename, machine):
    ssh = createSSHClient(MACHINE.format(server_id=machine), "askrish2", "Qbmstfu1")
    sftp = ssh.open_sftp()
    sftp.put("/home/files/" + filename, "/home/files/" + filename)
    sftp.close()
    ssh.close()

def listen_get():
	sock = socket(AF_INET, SOCK_DGRAM)
	server_addr = (myHost, GET_PORT)
	sock.bind(server_addr)
	sock.settimeout(1)
	while 1:
		try:
			response, address = sock.recvfrom(4096)
			(filename, machine) = marshal.loads(response)
			if "send" in filename:
                    arr = filename.split(" ")
                    f = arr[1]
                    send_get(f, arr[2])
			if filename in replicas:
				send = marshal.dumps((str(file_times[filename]), SERVERNAME))
				try:
					sock.sendto(send, address)
				except Exception as e:
                	continue
        except Exception as e:
        	continue
    sock.close()

def update_pre_suc():
	global members, pre, suc
	members_mutex.acquire()
	memberlist_mutex.acquire()
	members = []
	for key, (hb_time, times, active, counter) in memberlist.iteritems():
		if active:
			members.append(key)	
	len_mems = len(members)
	if len_mems >= 3:
		members = sorted(members)
		my_index = members.index(SERVERNAME)
		pre_ind = my_index -1
		suc_ind = my_index +1
		pre_mutex.acquire()
		suc_mutex.acquire()
		if pre_ind is -1:
			pre = members[len_mems-1]
		else:
			pre = members[pre_ind]
		if suc_ind is (len_mems):
			suc = members[0]
		else:
			suc = members[suc_ind]
		pre_mutex.release()
		suc_mutex.release()
	memberlist_mutex.release()
	members_mutex.release()

def send_member(member, sock, memberlist_send):
	if member != SERVERNAME:
        	address = MACHINE.format(server_id=member)
        	sock.sendto(memberlist_send, (address, GOSSPORT))

def createSSHClient(server, user, password):
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(server, username=user, password=password)
    return client

def put(path, file_name):
	print "put"	
    time = datetime.datetime.utcnow()
    replica_time_mutex.acquire()
    replica_time = time
    file_times[file_name] = time
    replica_time_mutex.release()
	replicate(path, file_name)	
	shutil.copy2(path, "/home/files/"+ file_name)

def update(path, file_name, server):
    file_path = "/home/files/" + file_name
    print path, file_name, server
    ssh = createSSHClient(MACHINE.format(server_id=server), "askrish2", "Qbmstfu1")
    sftp = ssh.open_sftp()
    sftp.put(path, file_path)
    sftp.close()
    ssh.close()

def replicate(path, file_name):
	file_path = "/home/files/" + file_name
	memberlist_mutex.acquire()
	keys = memberlist.keys()
	memberlist_mutex.release()
	index = keys.index(SERVERNAME)
	replicas_mutex.acquire()

	if file_name in replicas and SERVERNAME not in replicas[file_name]:
		replicas[file_name].append(SERVERNAME)
	else:
		replicas[file_name]=[SERVERNAME]
	replicas_mutex.release()
	i = 1
	replicas_mutex.acquire()
	while len(replicas[file_name])<6:
		replicas_mutex.release()
		replica = (index + i) % len(keys)
		server = keys[replica]
		ssh = createSSHClient(MACHINE.format(server_id=server), "askrish2", "Qbmstfu1")
		sftp = ssh.open_sftp()
		sftp.put(path, file_path)
		replicas_mutex.acquire()
		if server not in replicas[file_name]:
			replicas[file_name].append(server)
		replicas_mutex.release()		
		sftp.close()
		ssh.close()
		i+=1
		replicas_mutex.acquire()
	servers = replicas[file_name]
	replicas_mutex.release()

	sock = socket(AF_INET, SOCK_DGRAM)
    server_addr = (MACHINE.format('01'), GOSSREP_PORT)
    message = marshal.dumps((file_name, servers))
    sock.sendto(message, server_addr)

def put_update(path, file_name):
    if file_name in replicas:
		index = 0
		N = len(replicas[file_name])
		for member in replicas[file_name]:
			if member == SERVERNAME:
				continue;
			if index >= math.floor(N/2 + 1):
	        	break
	        update(path, file_name, member)
			address = MACHINE.format(server_id=member)
			put_sock = socket(AF_INET, SOCK_DGRAM)
	        put_sock.settimeout(10)
			put_send = marshal.dumps((path, file_name, member))
			put_sock.sendto(put_send, (address, Update_PORT))
	        try:
				put_response, put_address = put_sock.recvfrom(4096)
		        if put_response:
			        index += 1
			    else:
			    	put_sock.close()
			    	continue
			except Exception as e:
            	print "put error " + str(e)
            finally:
            	put_sock.close()
        shutil.copy2(path, "/home/files/"+ file_name)

def do_put():
	sock = socket(AF_INET, SOCK_DGRAM)
	server_addr = (myHost, UPDATE_Port)
	sock.bind(server_addr)
	while 1:
  		try:
   			response, address = sock.recvfrom(4096)
    		if response:
    			data = marshal.loads(response)
    			(path, file_name, time) = data
				put(path, file_name)
				update_time = datetime.datetime.utcnow()
				file_times[file_name] = update_time
                put_sock = socket(AF_INET, SOCK_DGRAM)
                put_send = marshal.dumps("ack")
                try:
                	put_sock.sendto(put_send, address)
               	except:
                	"return put error"
                put_sock.close()
				
   		except Exception as error:
            print "Do put", error
            break
	sock.close()

#get command line input	
def get_command():
	while 1:
		print 'Enter "j" to join, "l" to leave, "m" to list the membership list, and "s" to list self id'
		line = sys.stdin.readline().strip('\n')
		if line == 'j':
			join_thread = Thread(target = join)
        	join_thread.daemon = True
        	join_thread.start()
		elif line == 'm':
			print memberlist
		elif line == 's':
			print SERVERNAME
		elif line == 'l':
			(times, active) = memberlist[serverName]
			time = str(datetime.datetime.utcnow())
			times.append(time)
			memberlist_mutex.acquire()
			memberlist[serverName] = (times, False)
			memberlist_mutex.release()
		 elif 'put' in line:
            arr = line.split(' ')
            local_path = arr[1]
            file_name = arr[2]
            if file_name in replicas.keys():
                    time = datetime.datetime.utcnow()
                    answer = 'y'
                    if file_name in file_times and (file_times[file_name] - time).total_seconds() < 60:
                        print 'Confirm update (y/n)'
                        i = 1
                        while i < 30:
                            yes_mutex.acquire()
                            answer = sys.stdin.readline().strip('\n')
                            yes_mutex.release()
                            if answer:
                                break
                            i+=1
                    if file_name in file_times and (file_times[file_name] - time).total_seconds() >= 60 or 'y' in answer:
                        print 'Put update'
                        put_up_thread = Thread(target = put_update, args=(local_path, file_name,))
                        put_up_thread.daemon = True
                        put_up_thread.start()
            else:
                print "New put"
                put_thread = Thread(target = put, args=(local_path, file_name,))
                put_thread.daemon = True
                put_thread.start()
		elif 'store' in line:
            replicas_mutex.acquire()
            for k, v in replicas.iteritems():
                if SERVERNAME in v:
                    print k
            replicas_mutex.release()
	    elif 'ls' in line:
            arr = line.split(' ')
            sdfs_name = arr[1].strip('\n')
            replicas_mutex.acquire()
            print replicas[sdfs_name]
            replicas_mutex.release()
	    elif 'get' in line:
            arr = line.split(' ')
            get_thread = Thread(target = get, args=(arr[1].strip('\n'),))
            get_thread.daemon = True
            get_thread.start()
	    elif 'delete' in line:
            arr = line.split(' ')
            delete_thread = Thread(target = delete, args=(arr[1].strip('\n'),))
            delete_thread.daemon = True
            delete_thread.start()

def delete(sdfs_name):
    replicas_mutex.acquire()
    servers = replicas[sdfs_name]
    del replicas[sdfs_name]
    replicas_mutex.release()
    sock = socket(AF_INET, SOCK_DGRAM)
    for server in servers:
        send_msg = marshal.dumps(sfds_name)
        sock.sendto(send_msg, (MACHINE.format(server_id=server), DELETE_PORT))

def listen_delete():
    sock = socket(AF_INET, SOCK_DGRAM)
    server_addr = (myHost, DELETE_PORT)
    sock.bind(server_addr)
    while 1:
        data, address = sock.recvfrom(4096)
        data = marshal.loads(data)
        if data:
            replicas_mutex.acquire()
            del replicas[data]
            replicas_mutex.release()
	
def listen_replicate():
	sock = socket(AF_INET, SOCK_DGRAM)
	server_addr = (myHost, CREATE_REP)
	sock.bind(server_addr)
	while 1:
		data, address = sock.recvfrom(4096)
		data = marshal.loads(data)
		if data:
			replicas_mutex.acquire()
			if len(replicas[data])>=6:
				replicas_mutex.release()
				continue
			replicas_mutex.release()
			replicate_thread = Thread(target = replicate, args=("/home/files/" + data, data))
			replicate_thread.daemon = True
			replicate_thread.start()
			sock.sendto("ack", address)
	sock.close()

#This method sends a message to the introducer in order to join
def join():
	directory = "/home/files"
	if not os.path.exists(directory):
    		os.makedirs(directory)
	else:
		shutil.rmtree(directory, ignore_errors=True)
		os.makedirs(directory)	

	os.chmod(directory, S_IRUSR|S_IWUSR|S_IXUSR|S_IWGRP|S_IXGRP|S_IRGRP|S_IROTH|S_IWOTH|S_IXOTH)		
	global memberlist
	join_message = JOINMSG.format(server_name=SERVERNAME) 

	intro = MACHINE.format(server_id='01') 		
	sock = socket(AF_INET, SOCK_DGRAM)
	sock.settimeout(1)
	server_addr = (intro, JOINPORT)
	join_message = marshal.dumps(join_message)
	sock.sendto(join_message, server_addr)
	try:
		response, address = sock.recvfrom(4096)
		if response:	
			memberlist_mutex.acquire()
			memberlist = marshal.loads(response)
			time = str(datetime.datetime.utcnow())
			memberlist_mutex.release()
			update_pre_suc()
			sock.close()
			logging.info('joined: ' + str(memberlist))
			return
		else:
			sock.close()
	except timeout:
		print 'join timeout'
	except error as e:
		print 'join error', e

	def listen_replica():
    sock = socket(AF_INET, SOCK_DGRAM)
    server_addr = (myHost, REPLICA_PORT)
    sock.bind(server_addr)
    while 1:
       try:
            response, address = sock.recvfrom(4096)
            if response:
                data = marshal.loads(response)
                (file_name, servers) = data
                replicas_mutex.acquire()
                replicas[file_name] = servers
                replicas_mutex.release()
                replica_time_mutex.acquire()
                replica_time = datetime.datetime.utcnow()
                replica_time_mutex.release()
            else:
            	break
       except error:
                break


	def listen_gossip():
        sock = socket(AF_INET, SOCK_DGRAM)
        server_addr = ('', GOSSPORT)
        sock.bind(server_addr)
        while 1:
	        try:
	            response, address = sock.recvfrom(4096)
	            if response:
					data = marshal.loads(response)
					for (k,v) in data.items():
						(times, boolean) = v
						memberlist_mutex.acquire()
						if k in memberlist and k != SERVERNAME:
							(my_times, my_boolean) = memberlist[k]
	                    	latest = times[-1]
	                   	 	latest = datetime.datetime.strptime(latest, STR_DATETIME)
	                    	my_latest = times[-1]
	                    	my_latest = datetime.datetime.strptime(my_latest, STR_DATETIME)
	                    	if latest > my_latest:
	                    		memberlist[k] = (my_times.append(latest), boolean)
	                    		update_pre_suc();
	                    if k not in memberlist and k != SERVERNAME:
	                    	memberlist[k] = v
	                    	update_pre_suc();
	                    memberlist_mutex.release()

	               	memberlist_mutex.acquire()
	                for (k,v) in memberlist.items():
	                	if k not in data:
	                		del memberlist[k]
	                		if k == '02':
	                			finish_mutex.acquire()
	                			FINISH = '01'
	                			finish_mutex.release()
	                		update_pre_suc();

	                memberlist_mutex.release()

	                thread = Thread(target=gossip)
					thread.daemon = True
					thread.start()
	            else:
                	break
           	except error as e:
				print "error", e
                break

    #select k random processes to gossip memberlist to	
	def gossip():
		memberlist_mutex.acquire()
		member_keys = memberlist.keys()
		memberlist_send = marshal.dumps(memberlist)
		memberlist_mutex.release()
		if len(member_keys)>=3:
			chosen_members = np.random.choice(member_keys, K, replace=False)
			sock = socket(AF_INET, SOCK_DGRAM)
			for member in chosen_members:
				send_thread = Thread(target = send_member, args=(member, sock, memberlist_send, ))
        		send_thread.daemon = True
        		send_thread.start()

	def listen_ping_requests():
		sock = socket(AF_INET, SOCK_DGRAM)
		server_addr = (myHost, pingPort)
		sock.bind(server_addr)
		while 1:
			try:
		   		data, address = sock.recvfrom(4096)
		   		data = marshal.loads(data)
		   		if data:
		   			if "ping" in data:
		   				thread = Thread(target=ping, args=(address,))
					    thread.daemon = True
					    thread.start()
					elif ("ping req", server) in data:	
						thread = Thread(target=ping_req, args=(server, address))
					    thread.daemon = True
					    thread.start()
					break
			except error:
		   		break

	def ping(address):
    	d = socket(AF_INET, SOCK_DGRAM)
		try:
			message = marshal.dumps("ack")
        	d.sendto(message, address)
		except error:
			break
		finally:
        	d.close()

    def ping_req(server, address):
		while 1:
			pr = socket(AF_INET, SOCK_DGRAM)
			server_addr = (MACHINE.format(server), pingPort)
			pr.settimeout(7) 
			try:
				message = marshal.dumps("ping")
				pr.sendto(message, server_addr)
				data, server = sock.recvfrom(4096)
				if data:
					message = marshal.dumps("success")
					pr.sendto(message, address)
				pr.close()
			except error:
				print('sock err')
			except timeout:
				pr.close()

if __name__ == "__main__":

	memberlist[SERVERNAME] = ([str(datetime.datetime.utcnow())], True)	
	command_thread = Thread(target = get_command)
	command_thread.daemon = True
	command_thread.start()	
    for i in range(4):
		gossip_thread = Thread(target = gossip)
	    gossip_thread.daemon = True
	    gossip_thread.start()
	listen_gossip_thread = Thread(target = listen_gossip)
    listen_gossip_thread.daemon = True
    listen_gossip_thread.start()
	listen_replicate_thread = Thread(target = listen_replicate)
	listen_replicate_thread.daemon = True
	listen_replicate_thread.start()
	listen_replica_thread = Thread(target = listen_replica)
    listen_replica_thread.daemon = True
    listen_replica_thread.start()

    listen_master_thread = Thread(target = listen_master_requests)
    listen_master_thread.daemon = True
    listen_master_thread.start()
    listen_ping_thread = Thread(target = listen_ping_requests)
    listen_ping_thread.daemon = True
    listen_ping_thread.start()
    ping_thread = Thread(target = ping)
    ping_thread.daemon = True
    ping_thread.start()	

	recv_thread = Thread(target=receive_message)
    recv_thread.daemon = True
    recv_thread.start()
    master_thread = Thread(target=listen_master_requests)
    master_thread.daemon = True
    master_thread.start()

    print("done")


