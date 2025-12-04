import json
import time
import sys
import os
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from matterlab_balances import MTXPRBalance, MTXPRBalanceDoors
from robot.robot_control_URArm import URController
from matterlab_balances.mt_balance import MTXPRBalanceDosingError
import time

BALANCE_IP = os.environ.get("BALANCE_IP")
BALANCE_PASSWORD = os.environ.get("BALANCE_PASSWORD")

substance_name = "NaCl"
target_weight_mg = 1

balance = MTXPRBalance (host = BALANCE_IP, password = BALANCE_PASSWORD)
rob = URController()
balance.open_door(MTXPRBalanceDoors.RIGHT_OUTER)
balance.close_door(MTXPRBalanceDoors.RIGHT_OUTER)
 
rob.home()
rob.activate_gripper()

# Define well locations from A1 to D2
rows = ['A']
# cols = ['1','2','3','4']
cols = ['1']
well_locations = [f"{row}{col}" for row in rows for col in cols]
dose_loc = "A1"

# Set initial target weight
current_weight_mg = target_weight_mg

rob.dose_2_balance('A1')
for well in well_locations:
    print(f"\n--- Processing {well} --- (target_weight_mg={current_weight_mg})")
    balance.open_door(MTXPRBalanceDoors.RIGHT_OUTER)
    rob.vial_2_balance(well)
    balance.close_door(MTXPRBalanceDoors.RIGHT_OUTER)
    try:
        balance.auto_dose(substance_name=substance_name, target_weight_mg=current_weight_mg)
    except MTXPRBalanceDosingError as e:
        print(f"Dosing failed for {well}: {e}")
        # Optionally log or handle the error further
    balance.open_door(MTXPRBalanceDoors.RIGHT_OUTER)
    time.sleep(1)  # Ensure the door is fully open before moving
    rob.vial_2_OT(well)
    current_weight_mg += 0.5  # Increase by 0.5mg for next run


# rob.balance_2_home(

# 
# rob.dosehead_2_balance()
# #balance.zero()
# 
# time.sleep(1)
# balance.open_door(MTXPRBalanceDoors.RIGHT_OUTER)
# rob.home_h()
# rob.home_2_balance()

