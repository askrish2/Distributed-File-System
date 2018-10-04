import sys
import threading
from socket import *
import re
import time
import marshal
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

K=3
MACHINE = 'fa17-cs425-g25-{server_id}.cs.illinois.edu'
all_members = ['01', '02', '04', '05', '06', '07', '08', '09', '10']
JOINMSG = 'join-{server_name}'
SERVERNAME = sys.argv[1]
myHost = ''

replica_time_mutex = Lock()
members_mutex = Lock()
pre_mutex = Lock()
suc_mutex = Lock()
memberlist_mutex = Lock()
failed_mutex = Lock()
replicas_mutex = Lock()
workers_mutex = Lock()

serverPort = 2000
clientPort = 2000
workerPort = 2001
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

job = None
MASTER = '02'
workers = 0

def send_master_message(message):
	d = socket(AF_INET, SOCK_DGRAM)
		address = MACHINE.format(MASTER)
        serverHost = (address, serverPort)
	try:
		data = marshal.dump(message)
    	d.sendto(data, serverHost)
	except error:
		break
	finally:
    	d.close()

def get_command():	
	while (1):
		print 'Enter a job class:'
		line = sys.stdin.readline().strip('\n')
		if line:
			job = line
			send_master_message(line)
		return line

def introducer():
    sock = socket(AF_INET, SOCK_DGRAM)
    server_addr = (myHost, JOINPORT)
    sock.bind(server_addr)
    while 1:
	    data, address = sock.recvfrom(4096)
	    data = marshal.loads(data)
	    if 'join' in data:
	            num = data.split('-')[1]
	            if num in memberlist:
                    time = str(datetime.datetime.utcnow())
                    (times, active) = memberlist[num]
                    times.append(time)
					memberlist_mutex.acquire()
	                memberlist[num] = (times, True)
					memberlist_mutex.release()
                else:
                    time =  str(datetime.datetime.utcnow())
					memberlist_mutex.acquire()
	                memberlist[num] = ([time], True)
					memberlist_mutex.release()
                try:
                    print 'Machine', num, 'joined:', memberlist
                    thread = Thread(target = gossip)
					thread.daemon = True
					thread.start()
					if num == '03':
						sleep(3)
						workers_mutex.acquire()
						memberlist_mutex.acquire()
						while 1:
							if workers == len(memberlist) - 1
								break
						memberlist_mutex.release()
						workers_mutex.release()
						send_master_message(job)
                except error as e:
                    print 'join error - sending memberlist to new join',
	sock.close()

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

def send_member(member, sock, memberlist_send):
		if member != SERVERNAME:
	        	address = MACHINE.format(server_id=member)
	        	sock.sendto(memberlist_send, (address, GOSSPORT))

def ping(server):
	try:	
		sock = socket(AF_INET, SOCK_DGRAM)
		sock.settimeout(7)
		server_addr = (MACHINE.format(server), pingPort)
		message = marshal.dumps('ping')
		sock.sendto(message, server_addr)
		ack = sock.recvfrom(4096)
		if ack:
			return True
	except:
		return False
	finally:
		sock.close()
	return False

def ping_req(server):

	if len(member_keys)>=3:
		chosen_members = np.random.choice(member_keys, K, replace=False)
		for member in chosen_members:
			try:
				sock = socket(AF_INET, SOCK_DGRAM)
				sock.settimeout(7)
				server_addr = (MACHINE.format(member), pingPort)
				message = marshal.dumps(("ping req", server))
				sock.sendto(message, server_addr)
				ack = sock.recvfrom(4096)
				if ack:
					return True
			except:
				continue
			finally:
				sock.close()
		return False

def swim():
	while 1:
		if len(member_keys)>=3:
			chosen_members = np.random.choice(member_keys, K, replace=False)
			for member in chosen_members:
				ack = ping(member)
				if not ack:
					ack = ping_req(member)
					if not ack:
						del memberlist[k]
						if k == '01':
							MASTER = '03'
							sock = socket(AF_INET, SOCK_DGRAM)
    						server_addr = (MACHINE.format('01'), JOINPORT)
    						message = marshal.dumps(JOINMSG.format('03'))
    						sock.sendto(message, server_addr)

						create_rep_thread = Thread(target = create_replica, args=(k, ))
                        create_rep_thread.daemon = True
                        create_rep_thread.start()

						gossip_thread = Thread(target = gossip)
						gossip_thread.daemon = True
						gossip_thread.start()	

def send_replicas(file_name, machines):
		sock = socket(AF_INET, SOCK_DGRAM)
		memberlist_mutex.acquire()
		for m in memberlist:
			address = MACHINE.format(server_id=m)
			replicas_send = marshal.dumps((file_name, machines))
			sock.sendto(replicas_send, (address, GOSSREP_PORT))
		memberlist_mutex.release()
		sock.close()

def listen_iteration_completion():
	sock = socket(AF_INET, SOCK_DGRAM)
    server_addr = (myHost, masterPort)
    sock.bind(server_addr)
    while 1:
	    data, address = sock.recvfrom(4096)
	    data = marshal.loads(data)
	    if data:
	    	workers_mutex.acquire()
			workers += 1
			workers_mutex.release()

def listen_gossip_replicas():
	sock = socket(AF_INET, SOCK_DGRAM)
    server_addr = (myHost, GOSSREP_PORT)
    sock.bind(server_addr)
    while 1:
	    data, address = sock.recvfrom(4096)
	    data = marshal.loads(data)
	    if data:
	    	(file_name, servers) = data
	    	replicas_mutex.acquire()
	    	replicas[file_name] = servers
	    	replicas_mutex.release()
			thread = Thread(target = send_replicas, args=(file_name, servers,))
			thread.daemon = True
			thread.start()	    	

def create_replica(fail):
	replicas_mutex.acquire()
    for (k,v) in replicas.items():
    	if fail in v:
			replicas[k].remove(fail)
            for member in v:
                if member != SERVERNAME and member != fail:
                    rep = MACHINE.format(server_id=member)
                    sock = socket(AF_INT, SOCK_DGRAM)
                    sock.settimeout(1)
                    server_addr = (rep, CREATE_REP)
                    create_message = marshal.dumps(k)
                    sock.sendto(create_message, server_addr)
            	try:
                	response, address = sock.recvfrom(4096)
                	if response:    
                        sock.close()
						replicas_mutex.release()
                       	return
               		else:
                        sock.close()
                        continue
            	except timeout:
                    	print 'replica timeout'
            	except error as e:
                    	print 'replica error', e
	replicas_mutex.release()

if __name__ == "__main__":
	get_thread = Thread(target = get_command)
	get_thread.daemon = True
	get_thread.start()
	rep_thread = Thread(target = listen_gossip_replicas)
	rep_thread.daemon = True
	rep_thread.start()
	memberlist[SERVERNAME] = ([str(datetime.datetime.utcnow())], True)


