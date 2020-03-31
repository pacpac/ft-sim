import binascii
from crc32 import CRC32

class CompressionBuffer:

  def __init__(self, buffer):
    self.m_previous_words = [0] * 4096
    self.m_compressed = buffer
    self.m_word_count = 0
    self.m_compressed_size = 0
    self.m_nochange_count = 0
    self.m_bitbuffer = 0
    self.m_bitcount = 0
    self.m_crc = CRC32()
    self.m_error = 0     
    self.reset()
    
  def reset(self):
    self.rewind()
    
  def rewind(self):
    self.m_word_count = 0
    self.m_compressed_size = 0
    self.m_nochange_count = 0
    self.m_bitcount = 0
    self.m_bitbuffer = 0L
    self.m_compressed_size_limit = 0
    self.m_crc.reset()
    
  def push_bits(self, count, bits):
    self.m_bitbuffer = 0xFFFFFFFF & (self.m_bitbuffer | (bits << self.m_bitcount))
    self.m_bitcount += count
    
    while (self.m_bitcount >= 8):
      self.m_bitcount -= 8
      self.m_compressed[self.m_compressed_size] = self.m_bitbuffer & 0xff
      self.m_compressed_size += 1
      self.m_bitbuffer >>= 8
    
  def encode_no_change_count(self):
    # 00 NoChange 1x16 bit
    # 01 00 NoChange 2x16 bit
    # 01 01 NoChange 3x16 bit
    # 01 10 NoChange 4x16 bit
    # 01 11 xxxx NoChange 5..19x16 bit
    # 01 11 1111 xxxxxxxx  NoChange 20..274 x16 bit
    # 01 11 1111 11111111 xxxxxxxx-xxxxxxxx NoChange 275... bit
    
    while (self.m_nochange_count > 0):
      if(self.m_nochange_count == 1):
        self.push_bits(2, 0)
        break
        
      elif(self.m_nochange_count <= 4):
        self.push_bits(2, 1)
        self.push_bits(2, self.m_nochange_count-2)
        break
        
      elif(self.m_nochange_count <= 4+15):
        self.push_bits(2, 1)
        self.push_bits(2, 3)
        self.push_bits(4, self.m_nochange_count-4-1)
        break
        
      elif(self.m_nochange_count <= 4+15+255):
        self.push_bits(2, 1)
        self.push_bits(2, 3)
        self.push_bits(4, 15)
        self.push_bits(8, self.m_nochange_count-4-15-1)
        break
        
      elif(self.m_nochange_count <= 4+15+255+4096):
        self.push_bits(2, 1)
        self.push_bits(2, 3)
        self.push_bits(4, 15)
        self.push_bits(8, 255)
        self.push_bits(16, self.m_nochange_count-4-15-255-1)
        break
        
      else:
        self.push_bits(2, 1)
        self.push_bits(2, 3)
        self.push_bits(4, 15)
        self.push_bits(8, 255)
        self.push_bits(16, 4095)
        self.m_nochange_count += -4-15-255-4096

    self.m_nochange_count = 0
      
  def add_uint16(self, word):
    self.m_crc.add16bit(word)

    if (word == self.m_previous_words[self.m_word_count]):
      self.m_nochange_count += 1
      self.m_word_count += 1
    else:
      self.encode_no_change_count()
      if ((word == 1 and self.m_previous_words[self.m_word_count] == 0) or (word == 0 and self.m_previous_words[self.m_word_count] != 0)):
        # 10 Toggle (0 to 1, everything else to 0
        self.push_bits(2, 2)
      else:
        # 11 16 bit follow immediately
        self.push_bits(2, 3)
        self.push_bits(16, word)
        
      self.m_previous_words[self.m_word_count] = word
      self.m_word_count += 1
      
  def finish(self):
    self.encode_no_change_count()
    if( self.m_bitcount ): 
      self.push_bits(8 - self.m_bitcount, 0)
  
  def get_crc(self):
    return self.m_crc.m_crc
    
  def get_error(self):
    return self.m_error
    
  def get_compressed_size(self):
    return self.m_compressed_size
    
  def get_buffer(self):
    return self.m_compressed
    
  def get_word_count(self):
    return self.m_word_count
    
  def get_prev_word(self):
    return self.m_previous_words[i]