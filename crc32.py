class CRC32:
  def __init__(self):
    self.m_crc = 0xFFFFFFFF
    self.m_table = [0] * 256
    
    for dividend in range(len(self.m_table)):
      remainder = 0xFFFFFFFF & (dividend << 24)
      bit = 8
      while bit > 0 :
        if (remainder & 0x80000000) :
          remainder = (remainder << 1) ^ 0x04C11DB7
        else :
          remainder = (remainder << 1)
        bit -= 1
        
      self.m_table[dividend] = 0xFFFFFFFF & remainder
      
  def reset(self):
    self.m_crc = 0xFFFFFFFF
  
  def add16bit(self, val):
    data = 0
    
    data = 0xFF & ((self.m_crc>>24) ^ (val >> 8))
    self.m_crc = 0xFFFFFFFF & ((self.m_crc << 8) ^ self.m_table[data])
    
    data = 0xFF & ((self.m_crc>>24) ^ (val & 0xFF))
    self.m_crc = 0xFFFFFFFF & ((self.m_crc << 8) ^ self.m_table[data])