#!/usr/bin/env python

from socketserver import ThreadingUDPServer as UDP 
from socketserver import BaseRequestHandler as BRH 
from functools import partial
import socket
import threading
import queue
import time
import hmac
import pickle

def encodeMsg( msg ):
	return bytes(hmac.new( b'woshi328liucao', msg ).hexdigest(),'ascii')

class ChatMsg:
	def __init__( self, mtype, data=None, 
			name=None, time=None ):
		self.data = data
		self.time = time
		self.name = name
		self.mtype = mtype

def msgPack( msg ):
	piced = pickle.dumps( msg )
	return encodeMsg( piced ) + piced

def msgDePack( msg ):
	valid = False 
	demsg = None 

	try:
		if msg[:32] == encodeMsg( msg[32:] ):
			valid=True
			demsg=pickle.loads( msg[32:] )
	except:
		pass

	return valid, demsg

class ChatCache:
	def __init__( self ):
		self.datain = queue.Queue()
		self.datapool = dict()

	def processor( self ):
		while self.stopflag:
			data, addr = self.datain.get()
			self.datapool[addr].put(data)

	def start( self ):
		self.stopflag=True 
		a=threading.Thread( target=self.processor )
		a.setDaemon(True)
		a.start()

	def stop( self ):
		self.stopflag=False

	def putdata( self, addr, data ):
		self.datain.put( (data, addr) )

	def getaddrlist( self ):
		return list(self.datapool.keys())

	def setaddr( self, addr ):
		if addr not in self.datapool:
			self.datapool[addr] = queue.Queue()

	def getdata( self, addr ):
		try:
			return self.datapool[addr].get(timeout=0.5)
		except:
			return None

cache = ChatCache()
	
class ChatCli:
	def __init__(self, host, port ):
		self.host = host
		self.port = port
		self.sock = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
		self.cache = cache
		self.cache.setaddr( self.host )

	def send( self, data ):
		self.sock.sendto( msgPack(data), (self.host, self.port))
		self.sock.settimeout(5)
		
		beg = time.time()
		while True:
			try:
				valid=False
				msg=None
				msg, addr = self.sock.recvfrom(2048)
				valid, msg = msgDePack( msg )
			except:
				pass

			if valid and msg.mtype == 3:
				msg.time=time.time()
				self.cache.putdata(self.host, data)
				break

			if time.time() - beg > 6:
				msg = ChatMsg( mtype=1, name='system', data='Send Failed' )
				self.cache.putdata( self.host, msg )
				break

	def close( self ):
		self.sock.close()

class handle( BRH ):
	def setup( self ):
		cache.setaddr(self.client_address[0])

	def handle( self ):
		data = self.request[0].strip()
		valid, msg = msgDePack( data )
		if valid :
			sock = self.request[1]
			if msg.mtype == 1:
				sock.sendto(msgPack(ChatMsg(mtype=3,name=self.server.name)), self.client_address )
				msg.time = time.time()
				cache.putdata( self.client_address[0], msg)
			elif msg.mtype == 2:
				print('get searchmsg ', self.client_address[0]) 
				sock.sendto(msgPack(ChatMsg(mtype=2,name=self.server.name)), self.client_address )
				add = (self.client_address[0], msg.name)
				if add not in self.server.liveaddr :
					self.server.liveaddr.append( add  )


class ChatSer( UDP ):
	def __init__( self, port,name,liveaddr, handle=handle ):
		self.name=name
		self.liveaddr=liveaddr
		UDP.__init__( self, ('', port), handle )

	def start( self ):
		self.serthd=threading.Thread( target=self.serve_forever )
		self.serthd.start()

	def stop( self ):
		self.shutdown()

class ChatBox:
	def __init__( self, addr, printMethond ):
		self.addr = addr
		self.cache = cache
		self.printm = printMethond 

	def run( self ):
		while self.runflag:
			data = self.cache.getdata( self.addr )
			if data:
				self.printm( data )

	def start( self ):
		self.runflag=True
		a = threading.Thread( target=self.run )
		a.setDaemon(True)
		a.start()

	def stop( self ):
		self.runflag=False

class SerSearchSer:
	def __init__( self, broadcast, name, liveaddr , port=9130):
		self.sock = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
		self.sock.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1 )
		self.sock.setsockopt( socket.SOL_SOCKET, socket.SO_BROADCAST, 1 )
		self.ba = broadcast
		self.sock.bind( ('', port) )
		self.name = name
		self.liveaddr=liveaddr
	
	def begin( self ):
		self.sock.sendto( msgPack(ChatMsg(mtype=2,name=self.name) ), (self.ba, 9129))
		self.liveaddr[:]=[]
		self.sock.settimeout( 7 )
		beg = time.time()

		while True:
			try:
				msg, addr = self.sock.recvfrom(1024)
				valid, msg = msgDePack( msg )
				print( valid, addr )
				if valid and msg.mtype == 2:
					if (addr[0], msg.name) not in self.liveaddr:	
						self.liveaddr.append( (addr[0], msg.name) )
					print(self.liveaddr)
			except: 
				break

			if time.time() - beg > 10: 
				break

	def Sbegin( self ):
		threading.Thread( target=self.begin ).start()

	def close( self ):
		self.sock.close()

