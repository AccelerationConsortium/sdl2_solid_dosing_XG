"""
Main dosing workflow that integrates robot arm and balance operations.
"""

import json
import time
import sys
import os
from pathlib import Path

# Add parent directories to path to import modules
sys.path.append(str(Path(__file__).parent.parent))

from matterlab_balances import MTXPRBalance, MTXPRBalanceDoors
from robot.robot_control import URController  # Your actual robot control module


class DosingWorkflow:
    """Main workflow class for coordinating robot and balance operations."""
    
    def __init__(self, config_path="config/workflow_config.json"):
        """Initialize the workflow with configuration."""
        self.config = self._load_config(config_path)
        self.balance = None
        self.robot = None
        self.is_initialized = False
        
    def _load_config(self, config_path):
        """Load configuration from JSON file."""
        config_file = Path(__file__).parent / config_path
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Config file not found: {config_file}")
            return {}
        except json.JSONDecodeError:
            print(f"Invalid JSON in config file: {config_file}")
            return {}
    
    def initialize_hardware(self):
        """Initialize connections to balance and robot."""
        try:
            # Initialize balance
            self.balance = MTXPRBalance(
                host=self.config.get('balance', {}).get('ip', '192.168.254.83'),
                password=self.config.get('balance', {}).get('password', 'Accelerate')
            )
            print("✓ Balance connected successfully")
            
            # Initialize robot
            robot_config = self.config.get('robot', {})
            self.robot = URController(
                ur_ip=robot_config.get('ip', '192.168.254.19'),
                gripper_port=robot_config.get('gripper_port', 63352)
            )
            print("✓ Robot connected successfully")
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            print(f"✗ Failed to initialize hardware: {e}")
            return False
    
    def open_balance_door(self):
        """Open the right door of the balance."""
        try:
            self.balance.open_door(MTXPRBalanceDoors.RIGHT_OUTER) 
            print("✓ Balance right door opened")
            time.sleep(1)  # Wait for door to fully open
            return True
        except Exception as e:
            print(f"✗ Failed to open balance door: {e}")
            return False
    
    def close_balance_door(self):
        """Close the left door of the balance."""
        try:
            self.balance.close_door(MTXPRBalanceDoors.RIGHT_OUTER)
            print("✓ Balance right door closed")
            time.sleep(1)  # Wait for door to fully close
            return True
        except Exception as e:
            print(f"✗ Failed to close balance door: {e}")
            return False
    
    def place_vial_in_balance(self):
        """Robot places vial inside the balance."""
        try:
            self.balance.open_door(MTXPRBalanceDoors.RIGHT_OUTER)
            self.robot.home_h()
            self.robot.home_h_2_vial_rack()
            self.robot.vial_rack_2_balance()  # Pick up vial
            self.robot.balance_2_home()
            self.balance.close_door(MTXPRBalanceDoors.RIGHT_OUTER)
            
            print("✓ Vial placed in balance")
            return True
            
        except Exception as e:
            print(f"✗ Failed to place vial: {e}")
            return False
    
    def place_dosing_head(self):
        """Robot places dosing head onto the balance."""
        try:
            self.robot.dosehead_2_balance()
            
            print("⚠ Dosing head placement not yet implemented - add waypoints to ur3_positions.json")
            return True
            
        except Exception as e:
            print(f"✗ Failed to place dosing head: {e}")
            return False
    def vial_2_ot(self):
        try:
            self.robot.balance_2_ot_2_home

            print("move vial to ot")
        except Exception as e:
            print(f"✗ Failed to place dosing head: {e}")
            return False


    def start_dosing(self):
        """Start the dosing process."""
        try:
            # Tare the balance
            self.balance.tare()
            print("✓ Balance tared")
            
            # Start auto dosing
            dosing_config = self.config.get('dosing', {})
            self.balance.auto_dose(
                substance_name=dosing_config.get('substance_name', 'NaCl'),
                target_dose_amount_mg=dosing_config.get('target_amount_mg', 0.5)
            )
            print("✓ Dosing started")
            
            # # Wait for dosing to complete
            # wait_time = dosing_config.get('wait_time_seconds', 2.0)
            # time.sleep(wait_time)
            
            # # Get final weight
            # weight_val, unit, is_stable = self.balance.get_weight(WeighingCaptureMode.IMMEDIATE)
            # print(f"✓ Final weight: {weight_val} {unit}, Stable: {is_stable}")
            
            return True
            
        except Exception as e:
            print(f"✗ Failed to start dosing: {e}")
            return False

    
    def run_full_workflow(self):
        """Run the complete dosing workflow."""
        print("Starting dosing workflow...")
        
        if not self.is_initialized:
            if not self.initialize_hardware():
                print("Failed to initialize hardware. Aborting workflow.")
                return False
        
        try:
            # Step 1: Open balance door
            if not self.open_balance_door():
                 return False
            
            # Step 2: Place vial in balance
            # if not self.place_vial_in_balance():
            #     return False
            
            # Step 3: Close balance door
            # if not self.close_balance_door():
            #     return False
            
            # Step 4: Place dosing head
            # if not self.place_dosing_head():
            #     return False
            
            # Step 5: Start dosing
            # if not self.start_dosing():
            #     return False
            
            # Step 6: Open balance door
            # if not self.open_balance_door():
            #     return False

            # # Step 6: move vial to ot
            # if not self.vial_2_ot():
            #     return False
            
            print("Workflow completed successfully!")
            return True
            
        except Exception as e:
            print(f"Workflow failed with error: {e}")
            return False
    



def main():
    """Main function to run the workflow."""
    workflow = DosingWorkflow()
    
    
    success = workflow.run_full_workflow()
    if success:
        print("Workflow completed successfully!")
    else:
        print("Workflow failed!")
    #finally:
        #workflow.cleanup()


if __name__ == "__main__":
    main() 