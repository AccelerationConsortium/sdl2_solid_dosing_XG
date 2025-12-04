from mt_balance import MTXPRBalance
from mt_balance import DosingHeadType
import os
import time

BALANCE_IP = os.environ.get("BALANCE_IP")
BALANCE_PASSWORD = os.environ.get("BALANCE_PASSWORD")

balance = MTXPRBalance (host = BALANCE_IP, password = BALANCE_PASSWORD)

# Need to detect automatic dosing head id as next iteration

# Reads values of current dosing head attached
value = balance.read_dosing_head()

# writes to dosing head obv
balance.write_dosing_head(head_type =  DosingHeadType.POWDER, head_id = '240182210152', info_to_write = { 'SubstanceName': 'Salt5', "LotId" : "Slot 5"})

print (value)