"""
***********************************************************************
**ft-sim** - Simulation world for FISCHERTECHNIK ROBO Pro software
***********************************************************************
(c) 2020 by Greg Zaytsev
"""

import wx
import math
import thread
import socket
import sys
import binascii
from struct import *

from compression_buffer import CompressionBuffer
from expansion_buffer import ExpansionBuffer

__author__      = "Greg Zaytsev"
__copyright__   = "Copyright 2020 by Greg Zaytsev"
__credits__     = "PACPAC"
__version__     = "1.00"
__maintainer__  = "Greg Zaytsev"
__email__       = "g.zaytsev@pacpac.ru"
__status__      = "beta"
__date__        = "01.04.2020"


pos_x = 0
outputs = [0, 0, 0, 0, 0, 0, 0, 0]
inputs  = [0, 0, 0, 0, 0, 0, 0, 0]
        
class SocketReader(object):
    def __init__(self):
        self.m_pwmOutputValues = [0] * 8
        self.m_universalInputs = [0] * 8

        self.eb = ExpansionBuffer()
        self.cb = CompressionBuffer(bytearray([0]*4096))


        self.TCP_IP = ''
        self.TCP_PORT = 65000
        self.BUFFER_SIZE = 1024
        
    def run(self):
        global pos_x
        
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM,  socket.IPPROTO_TCP)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1 )
        self.s.bind((self.TCP_IP, self.TCP_PORT))
        print >>sys.stderr, 'Starting up on %s port %s' % self.s.getsockname()
        self.s.listen(1)
        self.conn, self.addr = self.s.accept()
        print >>sys.stderr, 'Connection from address:', self.addr
        
        while True:
            packet = self.conn.recv(self.BUFFER_SIZE)
            if not packet:
                print "Close connection"
                break
                
            #Packets structures according to TXT-C-Programming-Kit-4-1-6.zip
            #packet string from tuple
            #packet = packet[0]
             
            #take first 4 characters for the ID header
            txt_id = unpack('<I' , packet[0:4])
            #print 'Command ID :' + '0x' + format(txt_id[0], 'X'),
            
            #QueryStatus
            if txt_id[0] == 0xDC21219A:
              #print 'QueryStatus'
              reply_packet = pack('<I16sI', 0xBAC9723E,'FT-TXT-SIM',0x04060600)
              self.conn.send(reply_packet)
              #print
              
            
            #StartOnline
            elif txt_id[0] == 0x163FF61D:
              #print 'StartOnline'
              txt_id = unpack('<64s' , packet[4:68])
              #print 'm_name :' + format(txt_id[0], 's')
              
              reply_packet = pack('<I', 0xCA689F75)
              self.conn.send(reply_packet)
              #print
              
            
            #UpdateConfig 0x060EF27E
          
            #INT16 m_config_id;
            #INT16 m_extension_id;
            #FTX1_CONFIG m_config;
            
            # // fish.X1 config structure
            # // [shm_if_config_s], 88 bytes
            # typedef struct ftX1config
            # {
            # // TX-only: Program run state
            # UINT8           pgm_state_req;        // enum PgmState    pgm_state_req;
            # BOOL8           old_FtTransfer;
            # char            dummy[2];
            # // Configuration of motrs
            # // 0=single output O1/O2, 1=motor output M1
            # BOOL8           motor[IZ_MOTOR];
            # // Universal input mode, see enum InputMode
            # UNI_CONFIG      uni[IZ_UNI_INPUT];
            # // 0=normal, 1=inverted (not really used)
            # CNT_CONFIG      cnt[IZ_COUNTER];
            # // additional motor configuration data (currently not used)
            # INT16           motor_config[IZ_MOTOR][4];
            # } FTX1_CONFIG;

            elif txt_id[0] == 0x060EF27E:
              #print 'UpdateConfig'
              txt_id = unpack('<HH68B' , packet[4:4+2+2+68])
              #print 'm_config_id :' + format(txt_id[0], 'X')
              #print 'm_extension_id :' + format(txt_id[1], 'X')
              #print 'm_config :' + format(txt_id[2:], 's')
              #print
              
              reply_packet = pack('<I', 0x9689A68C)
              self.conn.send(reply_packet)
            
            #ExchangeData 0xCC3597BA
            elif txt_id[0] == 0xCC3597BA:
              pass
              #print 'ExchangeData'
              #print
            
            #ExchangeDataCmpr 0xFBC56F98
            #
            # Command structure
            #
            # UINT32 m_crc;
            # UINT16 m_active_extensions;
            # UINT16 m_dmy_align;
            # UINT8 m_data[0];
            
            # // Transfer order
            # // INT16 m_pwmOutputValues[ftIF2013_nPwmOutputs]; 8
            # // INT16 m_motor_master[ftIF2013_nMotorOutputs]; 4
            # // INT16 m_motor_distance[ftIF2013_nMotorOutputs]; 4
            # // INT16 m_motor_command_id[ftIF2013_nMotorOutputs]; 4
            # // INT16 m_counter_reset_command_id[ftIF2013_nCounters]; 4
            # // UINT16  m_sound_command_id;
            # // UINT16  m_sound_index;
            # // UINT16  m_sound_repeat;

            # Response structure
            #
            # // CRC16 of decompressed data
            # UINT32 m_crc;
            # // One bit for each connected extension
            # // Data is transmitted only for the master and for the bits set here
            # UINT16 m_active_extensions;
            # UINT16 m_dmy_align;
            # // Compressed data
            # // See ftIF2013Command_ExchangeData for compression scheme
            # // INT16 m_universalInputs[ftIF2013_nUniversalInputs]; 8
            # // INT16 m_counter_input[ftIF2013_nCounters]; 4
            # // INT16 m_counter_value[ftIF2013_nCounters]; 4
            # // INT16 m_counter_command_id[ftIF2013_nCounters]; 4
            # // INT16 m_motor_command_id[ftIF2013_nMotorOutputs]; 4
            # // UINT16  m_sound_command_id; 1
            # // struct IR
            # // {
            # //     INT16  m_ir_leftX;  // left  handle, horizontal, -15..15
            # //     INT16  m_ir_leftY;  // left  handle, vertical,   -15..15
            # //     INT16  m_ir_rightX; // right handle, horizontal, -15..15
            # //     INT16  m_ir_rightY; // right handle, vertical,   -15..15
            # //     UINT16 m_ir_bits;   // 2^0=on, 2^1=off, 2^2=switch1, 2^3=switch2
            # // } m_ir[5];  25
            # UINT8 m_data[0];      
            elif txt_id[0] == 0xFBC56F98:
              #print 'ExchangeDataCmpr'  
              #print 'Packet length :' + str(len(packet)); 
              data = unpack('<IIHH' , packet[4:4+4+4+2+2])
              m_extrasize = data[0]
              #print 'm_extrasize :' + '0x' + format(m_extrasize, '>08X')
              cmd_m_crc = data[1]
              #print 'm_crc :' + '0x' + format(cmd_m_crc, '>08X')
              cmd_m_active_extensions = data[2]
              #print 'm_active_extensions :' + '0b' + format(cmd_m_active_extensions, '>016b')
              #print 'm_dmy_align :' + '0x' + format(data[3], '>04X')
              
              h_size = 4+4+4+2+2
              data = packet[h_size:]
              #print 'compressed data : ' + binascii.hexlify(data)
              
              self.eb.rewind()
              self.eb.m_compressed = bytearray(data)
              
              commdata = [0] * 27
              
              for i in range(len(commdata)):
                commdata[i] = self.eb.get_uint16()
              #print 'crc :', format(self.eb.get_crc(), '>08X')
              
              global outputs
              
              for i in range(8):
                  self.m_pwmOutputValues[i] = commdata[i]
                  outputs[i] = self.m_pwmOutputValues[i]
             
              #m_id
              reply_packet = pack('<I', 0x6F3B54E6)
              
              self.cb.rewind()
              
              self.m_universalInputs[0] = self.m_pwmOutputValues[0]
              
              self.cb.add_uint16(self.m_universalInputs[0])
              for i in range(51):
                self.cb.add_uint16(0x00)
              self.cb.finish()
              
              #m_extrasize
              reply_packet+=pack('<I', self.cb.get_compressed_size());
              
              #m_crc
              #print 'response crc :', format(self.cb.get_crc(), '>08X')
              reply_packet+=pack('<I', self.cb.get_crc());
              
              #m_active_extensions
              reply_packet+=pack('<H', 0x00);

              #m_dmy_align
              reply_packet+=pack('<H', 0x00);
              
              #data
              reply_packet+=self.cb.get_buffer()[0:self.cb.get_compressed_size()];
              
              #print binascii.hexlify(reply_packet)
              
              self.conn.send(reply_packet)
              #print
            
            #StopOnline 0x9BE5082C
            elif txt_id[0] == 0x9BE5082C:
              #print 'StopOnline'
              reply_packet = pack('<I', 0xFBF600D2)
              self.conn.send(reply_packet)        
              #print              
            
            #StartCameraOnline 0x882A40A6
            elif txt_id[0] == 0x882A40A6:
              pass
              #print 'StartCameraOnline'
              #print              
            
            #StopCameraOnline 0x17C31F2F
            elif txt_id[0] == 0x17C31F2F:
              pass
        self.conn.close()
        for i in range(8):
            outputs[i] = 0

class Car(object):
    def __init__(self, x, y, color="RED"):
        self.r = 5.0
        self.l = 20.0
        self.x = x
        self.y = y
        self.omega = 0
        self.x_dot = 0
        self.y_dot = 0
        self.omega_dot = 0
        self.color = color
        self.points = [(0, -10), (30, 0), (0, 10)]
        self.wheel_l = [(-self.r, -11), (self.r, -11)]
        self.wheel_r = [(-self.r, 11), (self.r, 11)]
        
    def rotatePolygon(self, polygon, theta):
        """Rotates the given polygon which consists of corners represented as (x,y),
        around the ORIGIN, clock-wise, theta degrees"""
        theta = math.radians(theta)
        rotatedPolygon = []
        for corner in polygon :
            rotatedPolygon.append(( corner[0]*math.cos(theta)-corner[1]*math.sin(theta) , corner[0]*math.sin(theta)+corner[1]*math.cos(theta)) )
        return rotatedPolygon
    

    def draw(self, dc):
        global outputs
        dc.SetPen(wx.Pen(self.color, 1))
        r = self.r
        l = self.l
        vl = outputs[0] / 512.0
        vr = outputs[2] / 512.0
        
        omega = math.radians(self.omega)
        
        self.x_dot = r/2.0*(vr + vl) * math.cos (omega)
        self.y_dot = r/2.0*(vr + vl) * math.sin (omega)
        self.omega_dot = math.degrees(r/l * (vr - vl))
        
        self.x = self.x + self.x_dot
        self.y = self.y + self.y_dot
        self.omega = self.omega + self.omega_dot
        
        poly = self.rotatePolygon(self.points, self.omega)
        dc.DrawPolygon(poly, self.x, self.y)
        poly = self.rotatePolygon(self.wheel_l, self.omega)
        dc.DrawPolygon(poly, self.x, self.y)        
        poly = self.rotatePolygon(self.wheel_r, self.omega)
        dc.DrawPolygon(poly, self.x, self.y)
        
class DebugPanel(object):
    def __init__(self, x, y, color="GREEN"):
        self.x = x
        self.y = y
        self.color = color
                
    def draw(self, dc):
        global outputs
        global inputs
        dc.SetPen(wx.Pen(self.color, 1))
        dc.SetTextForeground(self.color)
        for i in range(8):
            dc.DrawText(format(outputs[i], 'X'), self.x+30, self.y+i*11)
            dc.DrawText(format(inputs[i], 'X'), self.x+0, self.y+i*11)
        
class Panel(wx.Window):
    def __init__(self, parent):
        wx.Window.__init__(self, parent)
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
        self.SetBackgroundColour("WHITE")
        
        width, height = self.GetSize()
        #self.car = Car(width / 2, height / 2)
        self.debugpanel = DebugPanel(10,10)
        
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_SIZE, self.on_size)

        wx.FutureCall(200, self.SetFocus)
        
    def on_size(self, event):
        width, height = self.GetClientSize()
        self._buffer = wx.EmptyBitmap(width, height)
        #self.update_drawing()

    def update_drawing(self):
        self.Refresh(False)        

    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        dc.Clear()
        x, y = self.ScreenToClient(wx.GetMousePosition())
        self.car.draw(dc)
        self.debugpanel.draw(dc)

class MainFrame(wx.Frame):
    def __init__(self, *args, **kw):
        wx.Frame.__init__(self, *args, **kw)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Bind(wx.EVT_TIMER, self.on_timer)

        self.panel = Panel(self)

        self.txt_reader = SocketReader()
        
        thread.start_new_thread(self.txt_reader.run, ())        
       
        self.timer = wx.Timer(self)
        self.timer.Start(50)

                    
    def on_close(self, event):
        self.timer.Stop()
        self.Destroy()

    def on_timer(self, event):
        self.panel.update_drawing()


app = wx.App(False)
frame = MainFrame(None, -1, "ft-sim")
frame.Show(True)

width, height = frame.panel.GetSize()
frame.panel.car = Car(width / 2, height / 2)
        
app.MainLoop()