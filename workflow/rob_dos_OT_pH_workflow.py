import json
import time
import sys
import os
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from matterlab_balances import MTXPRBalance, MTXPRBalanceDoors
# from robot.robot_control import URController
from robot.robot_control_URArm import URController
from matterlab_balances.mt_balance import MTXPRBalanceDosingError
import time

BALANCE_IP = os.environ.get("BALANCE_IP")
BALANCE_PASSWORD = os.environ.get("BALANCE_PASSWORD")

substance_name = "NaCl"
target_weight_mg = 0.2

balance = MTXPRBalance (host = BALANCE_IP, password = BALANCE_PASSWORD)
rob = URController()


# rob.gripper_pos(rob.gripper_dist["open"]["dose"])
# rob.movej("safe_rack")
#balance.open_door(MTXPRBalanceDoors.RIGHT_OUTER)
# rob.home()
#rob.vial_2_balance()
#balance.close_door(MTXPRBalanceDoors.RIGHT_OUTER)
# rob.dose_2_balance()
	
# max_retries = 3
# for attempt in range(max_retries):
# 	try:
# 		balance.auto_dose(substance_name=substance_name, target_weight_mg=target_weight_mg)
# 		break  # Success
# 	except MTXPRBalanceDosingError as e:
# 		print(f"Attempt {attempt+1}: {e}")
# 		if "SubstanceFlowTooLow" in str(e) and attempt < max_retries - 1:
# 			print("Retrying dosing operation...")
# 				# Optionally add a delay here, e.g., time.sleep(2)
# 		else:
# 			print("Dosing failed due to low flow. Please check hardware.")
balance.close_door(MTXPRBalanceDoors.RIGHT_OUTER)

balance.open_door(MTXPRBalanceDoors.RIGHT_OUTER)
 
rob.home()
rob.activate_gripper()
# rob.vial_2_balance() 
# rob.dose_2_balance()
# rob.balance_2_home(

# 
# rob.dosehead_2_balance()
# #balance.zero()
# 
# time.sleep(1)
# balance.open_door(MTXPRBalanceDoors.RIGHT_OUTER)
# rob.home_h()
# rob.home_2_balance()
# rob.balance_2_ot_2_home()

