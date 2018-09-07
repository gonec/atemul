import serial
import sys
import configparser
import os

config=configparser.ConfigParser()
config_file = 'atemul.ini'

try:
	config.read('atemul.ini')
except BaseException as e:
	print('CONFIG FILE NOT FOUND!', e)
	sys.exit(1)

com_port = config['SERIAL']['com_port']
com_baudrate = config['SERIAL']['baudrate']
com_timeout  = int( config['SERIAL']['timeout'] )
ser = serial.Serial(port = com_port, baudrate = com_baudrate, timeout = com_timeout)
print("Starting emulator, listening on %s " % ser.name)
buff = b''
WR_FILE = 1
DEL_FILE = 2
SEND_MSG = 3
UNRECOGNIZED_MSG = 4

ok_resp=b'[{"err":0}]'
err_resp=b'[{"err":1}]'
RAW = b''
tmp_folder = os.path.join(os.getcwd(), 'TMP')
if not os.path.exists(tmp_folder):
	os.mkdir(tmp_folder)

def get_file_name(buff):
	fl_start = buff.find(b'=')
	fl_end = buff.find(b'&')
	name_length = fl_end - fl_start - 1	
	start_name_pos = fl_start + 2
	name_length = name_length -2
	f_name = buff[fl_start+2: fl_end-1]	
	return f_name	

def cmd_type(cmd):
	sendmsg = buff.find(b'GNcmd.xip?sendmsg')
	wrfile  = buff.find(b'GNcmd.xip?wrfile=')
	fildel  =  buff.find(b'GNcmd.xip?fildel')

	if wrfile != -1:
		print("WRFILE")
		return WR_FILE    
	
	if fildel != -1:
		print("ENDFILE")
		return DEL_FILE 
	
	if sendmsg != -1:
		print("SEND_MSG")
		return SEND_MSG 

	return UNRECOGNIZED_MSG
file_name=b''
while True:
	s = ser.read(1)
	buff = buff + s
	k = buff.find(b'<LF>')
	if k!=-1:
		cmd = cmd_type(buff)
		if cmd == WR_FILE:
			file_name = get_file_name(buff)
			print(file_name)
			ser.write(b'>')	
			print("WRITE FILE\n")
			len_s = buff.find(b'len=')
		
			if len_s != -1:				
				length_b  = buff[len_s+4:k]
				buff_size = int(length_b)
				print(">")
				raw_data  = ser.read(buff_size)
				print("RAW ACCEPTED %s" % raw_data)
				RAW += raw_data
				ser.write(ok_resp)
		if cmd == DEL_FILE:
			print("OK_RESP\n")
			ser.write(ok_resp)     		
		
		if cmd == SEND_MSG:
			print('FILE CONFIRMED: ', RAW)
			f=open( os.path.join(tmp_folder, file_name.decode() ), 'bw')
			f.write(RAW)
			f.close()	
			RAW=b''	
			ser.write(ok_resp)
		
		buff = b''
