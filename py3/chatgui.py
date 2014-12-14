#!/usr/bin/env python

from tkinter import *
from chat import *
from time import ctime

class mainWindow( Frame ):
	def __init__( self, master=None):
		self.root=master
		self.root.protocol( 'WM_DELETE_WINDOW', self.stopEverySer )
		self.chatlist=[]
		self.liveaddr=[]

		Frame.__init__( self, self.root, bg='lightblue' )

		self.pname=StringVar(value='Name: ')

		nameLbl = Label( self,textvariable=self.pname,bg='lightblue' )
		f = Frame( self )
		self.hostliveList = Listbox( f, height=15, width=40 )
		listScr = Scrollbar( f, command=self.hostliveList.yview )
		self.hostliveList.configure( yscrollcommand=listScr.set )
		self.hostliveList.bind( '<Double-Button-1>', self.getChatWin)
		self.searBut = Button( self, text='Search Hosts', command=self.search )
		quitBut = Button( self, text='Quit', command=self.stopEverySer)
		flushBut = Button( self, text='Fresh', command=self.flush)

		nameLbl.grid( column=0, row=0, pady=5 )
		self.hostliveList.pack(side=LEFT, expand=1, fill=BOTH)
		listScr.pack( side=RIGHT, fill=Y)
		f.grid( row=1, column=0, columnspan=2, 
								sticky=N+E+W+S	)
		flushBut.grid( row=2, column=0, columnspan=2, sticky=N+E+W+S )
		self.searBut.grid( row=3, column=0, columnspan=2, sticky=N+E+W+S )
		quitBut.grid( row=4, column=0, columnspan=2, sticky=N+E+W+S )
		self.grid()

	def enterBox( self ):
		def commit( ):
			self.pname.set(self.pname.get()+nameEty.get())
			self.name = nameEty.get()
			self.brip = bripEty.get()
			root.withdraw()
			self.startEverySer()
		root = Toplevel( self, bg='lightgreen' )
		root.transient( self )
		root.resizable(0,0)
		bripLbl = Label( root, text='BroadCast IP:', bg='lightgreen' )
		nameLbl = Label( root, text='Name:', bg='lightgreen' )
		nameEty = Entry( root, width=15 )
		bripEty = Entry( root, width=15 )
		quitBut = Button( root, text='Quit', command=self.quit )
		commBut = Button( root, text='Commit', command=commit )

		nameLbl.grid( column=0, row=0, stick=W, pady=5,padx=5 )
		bripLbl.grid( column=0, row=1, stick=W, pady=5,padx=5 )
		nameEty.grid( column=1, row=0, pady=5,padx=5 )
		bripEty.grid( column=1,row=1, padx=5, pady=5 ) 
		quitBut.grid( column=0, row=2, pady=5, padx=5 )
		commBut.grid( column=1, row=2, pady=5, padx=5 )
		root.grid()

	def alertWin( self, word ):
		top = Toplevel( self, bg='red' )
		Label( top, text=word ).grid(
			sticky=N+W+E+S )
		top.geometry('300x300+200+200')
		Button(top, text='Quit', command=self.quit ).grid( sticky=E )

	def startEverySer( self ):
		try:
			self.ser = ChatSer( 9129,self.name,self.liveaddr )
			self.sear = SerSearchSer( self.brip, self.name, self.liveaddr )
			cache.start()
			self.ser.start()
		except:
			self.alertWin('Please quit, there are something wrong')
			
	def stopEverySer( self ):
		self.root.quit()
		self.ser.stop()
		cache.stop()
		
	def search( self ):
		self.sear.Sbegin()
		
	def flush( self ):
		self.hostliveList.delete(0,END)
		for x in self.liveaddr:
			self.hostliveList.insert(END,'## '+ x[1] + ' ##')

	def getChatWin( self, event ):
		def sendMsg( ):
			cli.send( ChatMsg( mtype=1,data=senText.get(0.0,END), name=self.name ) )
			senText.delete(0.0,END)

		def close( ):
			self.chatlist.remove(num)	
			cli.close()
			box.stop()
			root.withdraw()

		def printm( data ):
			if data.name == 'system':
				recText.insert( END, '## system ##\n'+data.data+'\n', 'system' )
			elif data.name == self.name:
				recText.insert( END, data.name+'  |  '+ctime(data.time)+'>\n', 'selfName' )
				recText.insert( END, data.data )
			else :
				recText.insert( END, data.name+'  |  '+ctime(data.time)+'>\n', 'recvName' )
				recText.insert( END, data.data )
			recText.yview_moveto(1)

		try:
			num = self.hostliveList.curselection()[0]
		except:
			return 

		if num in self.chatlist:
			print('O no')
			return 

		self.chatlist.append( num )
		addr, name = self.liveaddr[num]
		cli=ChatCli( addr, 9129 )
		
		root = Toplevel( self )
		root.resizable(0,0)
		root.protocol('WM_DELETE_WINDOW', close )
		recText = Text( root, height=10, width=50 )
		recText.bind( '<KeyPress>', lambda e: 'break' )
		recText.tag_config( 'system', foreground='red' )
		recText.tag_config( 'recvName', foreground='blue')
		recText.tag_config( 'selfName', foreground='green')

		box = ChatBox( addr, printm )

		senText = Text( root, height=5, width=40 )
		senBut = Button( root, text='Send', command=sendMsg )
		cloBut = Button( root, text='Close', command=close )

		recText.grid( row=0, column=0, columnspan=2 )
		senText.grid( row=1, column=0, rowspan=2, pady=5 )
		senBut.grid( row=1, column=1,sticky=N+S+E+W, padx=5,pady=5 )
		cloBut.grid( row=2, column=1,sticky=N+S+E+W, padx=5  )
		
		box.start()

if __name__ == '__main__':
	root = Tk()
	mainwin = mainWindow(root)
	mainwin.enterBox()
	root.resizable(0,0)
	root.mainloop()

