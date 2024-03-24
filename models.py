class Datapoint(object):
  _watt_const = 3.190

  def __init__(self):
        self.serial_number="none"
        self.watt = 0

  @staticmethod
  def parse(bytestring):
      a_new = Datapoint() 
      a_new.serial_number = format(int.from_bytes(bytestring[19:23], 'little'), '02x')
      a_new.watt = int(round(int.from_bytes(bytestring[26:27], 'little') * Datapoint()._watt_const))
      return a_new

  def to_bytearray(self):
    # Berechnet den Wert für das mittlere Byte basierend auf der gewünschten Leistung
    power = int(self.watt / Datapoint()._watt_const)

    # Konvertiert die Seriennummer in eine Byte-Sequenz
    sn = int(self.serial_number, 16).to_bytes(4, 'little')

    # Erstellt die binären Daten mit dem berechneten mittleren Byte und der Seriennummer
    return bytes([
     #------#------#------#------#------#------#------#------#
        0x79,  0x26,  0x00,  0x40,  0x14,  0x00,  0x00,  0x0f, # 8
     #------#------#------#------#------#------#------#------#
        0x0f,  0x0f,  0x0f,  0x00,  0x00,  0x1c,  0x00,  0xc3, # 8
     #------#------#------#-------SERIAL-NUMBER-------#------#
        0xc3,  0xc3,  0xc3, sn[0], sn[1], sn[2], sn[3],  0x00, # 8
     #------#-V-AC-#-P-AC-#------#------#------#------#------#
        0x00,  0x5a, power,  0x9d,  0x16,  0x80,  0x0f,  0x05, # 8
     #------#------#------#------#------#------#------#------#
        0x02,  0xa6,  0x31,  0xd0,  0x0a,  0x11,  0x03,  0x05, # 8
     #------#------#------#------#------#
        0x8a,  0x63,  0x17,  0xc0,  0x34  # 5
    ])


  def __str__(self):
    return f"serial_number={self.serial_number}, watt={self.watt}"

  @property
  def serial_number(self):
      return self.serial_number

  @serial_number.setter
  def serial_number(self, val):
        type(self).serial_number = val

  @property
  def watt(self):
        return self.watt 
  @watt.setter
  def watt(self, val):
        type(self).watt = val

if __name__ == "__main__":
      dp = Datapoint()
      print(f"datapoint: {dp}")
      dp.serial_number = "30c577e1"
      dp.watt = 3
      print(f"datapoint with set property: {dp}")
      bytearray = dp.to_bytearray()
      print(f"bytestring: {bytearray}")

      Datapoint().parse(bytearray)
      print(f"datapoint from array: {dp}")
