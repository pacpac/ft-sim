import binascii
from crc32 import CRC32

class ExpansionBuffer:

  def __init__(self):
    self.m_word_count = 0
    self.m_compressed_size = 0
    self.m_nochange_count = 0
    self.m_bitcount = 0
    self.m_bitbuffer = 0
    self.m_compressed_size_limit = 0
    self.m_previous_words = [0] * 4096
    self.m_compressed = bytearray([0] * 4096)
    self.m_crc = CRC32()
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
    self.m_crc.reset();
    
  def get_bits(self, count):
    
    while (self.m_bitcount < count):
      self.m_bitbuffer |= self.m_compressed[self.m_compressed_size] << self.m_bitcount
      self.m_compressed_size += 1
      self.m_bitcount += 8
    
    r = self.m_bitbuffer & (0xFFFFFFFF >> (32-count))
    self.m_bitbuffer >>= count
    self.m_bitcount -= count
    return r
    
  def get_uint16(self):
    word = 0
    
    if (self.m_nochange_count > 0) :
      self.m_nochange_count -= 1
      word = self.m_previous_words[self.m_word_count]
    else:
      head = self.get_bits(2)
      if (head == 0):
        # 00 NoChange 1x16 bit
        word = self.m_previous_words[self.m_word_count]
      elif (head == 1):    
        # 01 00 NoChange 2x16 bit
        # 01 01 NoChange 3x16 bit
        # 01 10 NoChange 4x16 bit
        # 01 11 xxxx NoChange 5..19x16 bit
        # 01 11 1111 xxxxxxxx NoChange 20..274 x16 bit
        # 01 11 1111 11111111 xxxxxxxx-xxxxxxxx NoChange 275... x16 bit      
        word = self.m_previous_words[self.m_word_count]
        count = self.get_bits(2)
        if (count < 3):
          self.m_nochange_count = count+2-1
        else:
          count = self.get_bits(4)
          if (count < 15):
            self.m_nochange_count = count+5-1
          else:
            count = self.get_bits(8)
            if (count < 255):
              self.m_nochange_count = count+20-1
            else:
              count = self.get_bits(16)
              self.m_nochange_count = count+275-1
              
      elif (head == 2):
        # 10 Toggle (0 to 1, everything else to 0
        if (self.m_previous_words[self.m_word_count]) > 0:
          word = 0
        else:
          word = 1
          
      elif (head == 3):
        # 11 16 bit follow immediately
        word = self.get_bits(16)
        
    self.m_previous_words[self.m_word_count] = word
    self.m_word_count += 1
    self.m_crc.add16bit(word);
    
    return word
    
  def get_crc(self) :
    return self.m_crc.m_crc
  
  def print_state(self):
    print 'ExpansionBuffer State'
    print 'm_word_count :', str(self.m_word_count)
    print 'm_compressed_size :', str(self.m_compressed_size)
    print 'm_nochange_count :', str(self.m_nochange_count)
    print 'm_bitcount :', str(self.m_bitcount)
    print 'm_bitbuffer :', str(self.m_bitbuffer)
    print 'm_compressed_size_limit :', str(self.m_compressed_size_limit)
    print 'm_compressed :', binascii.hexlify(self.m_compressed)
    print 'm_previous_words :', self.m_previous_words[:self.m_word_count]
    print