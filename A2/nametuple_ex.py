#Using python namedtuple to create any struct like object
from collections import namedtuple

##First tuple
Position = namedtuple('Position', 'x y')
p = Position(1,2) #Position(x=1, y=2)
##Second tuple
Token = namedtuple('Token', 'pos')
t = Token(p) # Token(pos=Position(x=1, y=2))

### Another example
# Wrong way implement tuple - should have 2 arguments. Uncomment to see. (TypeError)
#WrongPacket = namedtuple('Packet', "seq_num","ack_num","ack_flag","nak_flag","get_flag","dat_flag","fin_flag","reserved","data") #10 arguments were given

Packet = namedtuple('Packet', 'seq_num ack_num ack_flag nak_flag get_flag dat_flag fin_flag reserved data')
pack = Packet(0,0,0,0,0,0,0,0,0) # this is a packet instance with values
# >>> pack -> Packet(seq_num=0, ack_num=0, ack_flag=0, nak_flag=0, get_flag=0, dat_flag=0, fin_flag=0, reserved=0, data=0)
print(pack.seq_num) # Should give 0

## We can have fields
# Creating packet with fields
fields = ("seq_num","ack_num","ack_flag","nak_flag","get_flag","dat_flag","fin_flag","reserved","data")
Packet = namedtuple('NewPacket', fields, defaults = (0,)*len(fields)) #default has to be list or long tuple
pack = Packet()
print(pack.seq_num) # Should give 0

## Creating packet with defualt values
defList = [0,0,0,0,0,0,0,0,0]
Packet = namedtuple('anotherPacket', fields, defaults = defList)
pack = Packet()
print(pack.seq_num) # Should give 0

##Note: once the value has been placed it cannot be altered. So we create a new one
# (AttributeError: can't set attribute ) if we try pack.seq_num = 1
pack = Packet(seq_num = 1)
print(pack.seq_num) # Should give 1

## Another object can have the same features too
newPack = pack 
print(newPack.seq_num) # Should give 1

##New packet using old pack
fields_1 = ("seq_num","ack_num","ack_flag","nak_flag","get_flag","dat_flag","fin_flag","data")
val = [2, 1, 1, 0, 0, 1, 0]
testing = Packet(*val, data = 101)
print(testing)
Str_val = map(list,testing[2:7]) # Did not work
Str_val = list(testing[2:7])  #Works
print("Value",testing[2:7], Str_val)








