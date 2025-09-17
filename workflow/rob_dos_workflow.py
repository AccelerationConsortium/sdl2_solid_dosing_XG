import json
import time
import sys
import os
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from matterlab_balances import MTXPRBalance, MTXPRBalanceDoors
from robot.robot_control import URController
import time

BALANCE_IP = "192.168.254.83"
BALANCE_PASSWORD = "Accelerate"

substance_name = "NaCl"
target_weight_mg = 5

balance = MTXPRBalance (host = BALANCE_IP, password = BALANCE_PASSWORD)
rob = URController()


rob.activate_gripper()
balance.open_door(MTXPRBalanceDoors.RIGHT_OUTER)
rob.home()
rob.vial_2_balance()
balance.close_door(MTXPRBalanceDoors.RIGHT_OUTER)
# rob.dose_2_balance()
# balance.auto_dose (substance_name = substance_name, target_weight_mg= target_weight_mg)
# balance.open_door(MTXPRBalanceDoors.RIGHT_OUTER)
# rob.vial_2_OT()
# balance.close_door(MTXPRBalanceDoors.RIGHT_OUTER)
# #rob.vial_2_balance() 
# rob.balance_2_home()

# 
# rob.dosehead_2_balance()
# #balance.zero()
# 
# time.sleep(1)
# balance.open_door(MTXPRBalanceDoors.RIGHT_OUTER)
# rob.home_h()
# rob.home_2_balance()
# rob.balance_2_ot_2_home()

