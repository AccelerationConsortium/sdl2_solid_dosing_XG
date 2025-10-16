from typing import Dict, Union
import os
from math import ceil
import socket
import time
import json
import numpy as np
from pathlib import Path
from robot.ur5_rtde_gripper import URArm
from resources.resource_handler import Handler
from utils import (
    logger, configure_global_exception_handler, component_manager
)


vial_stock_depth = -52 #distance in mm from prep to vial grip point
dose_stock_depth = 50 #distance in mm from prep to dose grip point


class URController:


    def __init__(self, ur3_ip="192.168.254.89", gripper_connect:bool = True, location_settings: Dict = None, location_file="ur3_1006_locations_converted.json"):
        self._gripper_item = None
        self._rob_loc = None
        self.gripper_dist = {
            "open": {"vial": 0.81, "dose": 0.65},
            "close": {"vial": 0.95, "dose": 0.70}
        }
        self._load_location_settings(location_settings if location_settings is not None else None)
        self._connect_rob(ur3_ip, gripper_connect)
        self._initialize_trays()


    def _log_debug(self, message: str):
        """Log debug message to component logger if available, otherwise to main logger."""
        comp_logger = component_manager.component_loggers.get("URController")
        if comp_logger:
            comp_logger.debug(message)
        else:
            # Create the component logger if it doesn't exist yet
            if "URController" not in component_manager.component_loggers:
                component_manager.component_loggers["URController"] = component_manager._create_component_logger("URController")
            comp_logger = component_manager.component_loggers.get("URController")
            if comp_logger:
                comp_logger.debug(message)
            else:
                logger.debug(message)
    
    def _log_error(self, message: str):
        """Log error message to component logger if available, otherwise to main logger."""
        comp_logger = component_manager.component_loggers.get("URController")
        if comp_logger:
            comp_logger.error(message)
        else:
            # Create the component logger if it doesn't exist yet
            if "URController" not in component_manager.component_loggers:
                component_manager.component_loggers["URController"] = component_manager._create_component_logger("URController")
            comp_logger = component_manager.component_loggers.get("URController")
            if comp_logger:
                comp_logger.error(message)
            else:
                logger.error(message)
    
    def _load_location_settings(self, settings: Dict = None) -> None:
        """Load robot position settings from JSON file or dict."""
        if settings is None:
            path_to_locations = os.path.join(os.path.dirname(__file__), 'ur3_1006_locations_converted.json')
            with open(path_to_locations, 'r') as f:
                settings = json.load(f)
        self.loc = settings["rob_locations"]
    
    def _connect_rob(self, rob_ip:str, gripper_connect:bool):
        self.rob = URArm(rob_ip, gripper_connect=gripper_connect)
    

    def gripper_pos(self, distance: float):
        self.rob.close_gripper(position=distance)
        self._gripper_pos = distance
        self._log_debug(f"Successfully set gripper position to {distance}")

    def activate_gripper(self):
        """Activate the gripper using the URArm's RobotiqGripper interface."""
        try:
            self.rob.gripper.set_registers({'ACT': 1})
            time.sleep(0.5)
            self._log_debug("Gripper activated.")
        except Exception as e:
            self._log_error(f"Gripper activation error: {e}")

    def _initialize_trays(self):
        """Initialize workspace tray layouts for current workflow."""
        self.resource_handler = Handler()
        self.vial_stock = self.resource_handler.make_tray(
            self.loc['vial_stock'], rows=6, columns=4, spacing=(20, 20), tray_name="vial_stock")

        self.dose_stock = self.resource_handler.make_tray(
            self.loc['dose_stock'], rows=5, columns=1, spacing=(45, 45), tray_name="dose_stock")
        
        self.dose_stock_back = self.resource_handler.make_tray(
            self.loc['dose_stock_back'], rows=5, columns=1, spacing=(45, 45), tray_name="dose_stock_back")

        self.vial_sample = self.resource_handler.make_tray(
            self.loc['prep_drop_ot'], rows=4, columns=6, spacing=(20, 20), tray_name="vial_sample")



    def print_lj(self):
        # # Debug RTDE connection status
        # rtde_connected = (self.rob.rtde_r is not None) and (self.rob.rtde_c is not None)
        # self._log_debug(f"RTDE connected: {rtde_connected}")
        current_joints = self.rob.get_joints()
        current_pose = self.rob.get_tcp_pose()
        # Log each line separately to ensure proper timestamps
        self._log_debug("Robot position: {")
        self._log_debug(f'"l": {[float(round(x, 2)) for x in current_pose]},')
        self._log_debug(f'"j": {[float(round(x, 2)) for x in current_joints]}')
        self._log_debug("}")
    

    def movej(self, pos, vel: float = 30, acc: float = None, asynchronous=False, verify_position=True):
        """Move robot joints to specified position with tracking and collision detection."""
        self._log_debug(f"movej: Moving to {pos} at velocity {vel} mm/s")
        
        if isinstance(pos, str):
            loc = self.loc.get(pos)
            if not loc or "j" not in loc or len(loc["j"]) != 6:
                self._log_error(f"Location '{pos}' not found or invalid joint data.")
                return False
            joints = loc["j"]
            self._log_debug(f"movej: Resolved position '{pos}' to joints: {joints}")
        else:
            joints = pos
            self._log_debug(f"movej: Using direct joint values: {joints}")
            
        # Execute movement
        self._log_debug(f"movej: Executing robot movement to joints: {joints}")
        self.rob.movej(joints, velocity=vel, acceleration=acc, async_move=asynchronous)
        
        self._rob_loc = pos if isinstance(pos, str) else None
        time.sleep(1)
        # self.print_lj()
        self._log_debug(f"movej: Successfully completed movement to {pos}")
        return True

    def movel(self, pos=None, x: float = 0, y: float = 0, z: float = 0, rx: float = 0, ry: float = 0, rz: float = 0, vel: float = 100, acc: float = None, asynchronous=False):
        """
        Move linearly to a pose using RTDEControlInterface.moveL.
        - If pos is a string, look up the location's 'l' pose in self.loc.
        - If pos is a list/tuple, use it directly.
        - If pos is a Location object, use its values as a 6-element list.
        - If pos is None, move relative to current TCP pose by (x, y, z, rx, ry, rz).
        """
        if isinstance(pos, str):
            self._log_debug(f"movel: Looking up position '{pos}'")
            loc = self.loc.get(pos, {})
            target_pose = loc.get("l")
            if not target_pose or len(target_pose) != 6:
                self._log_error(f"Location '{pos}' not found or invalid pose data.")
                return
        elif pos is None:
            self._log_debug(f"movel: Relative movement - offset: x={x}, y={y}, z={z}, rx={rx}, ry={ry}, rz={rz}")
            current_pose = self.rob.get_tcp_pose()
            target_pose = [
                current_pose[0] + x,
                current_pose[1] + y,
                current_pose[2] + z,
                current_pose[3] + rx,
                current_pose[4] + ry,
                current_pose[5] + rz
            ]
        elif hasattr(pos, 'position') and hasattr(pos, 'orientation'):
            # Accept Location object with position=[x,y,z] and orientation=[rx,ry,rz] format
            target_pose = pos.position + pos.orientation
            self._log_debug(f"movel: Using Location object pose: {target_pose}")
        elif hasattr(pos, 'x') and hasattr(pos, 'y') and hasattr(pos, 'z') and hasattr(pos, 'rx') and hasattr(pos, 'ry') and hasattr(pos, 'rz'):
            # Accept hein_robots.robotics.Location or compatible object
            target_pose = [pos.x, pos.y, pos.z, pos.rx, pos.ry, pos.rz]
            self._log_debug(f"movel: Using Location object pose: {target_pose}")
        else:
            if not isinstance(pos, (list, tuple)) or len(pos) != 6:
                error_msg = f"Invalid pose format: {type(pos).__name__}. Must be a 6-element list, tuple, or Location object."
                self._log_error(error_msg)
            target_pose = list(pos)
            self._log_debug(f"movel: Using direct pose values: {target_pose}")
        
        # Execute robot movement
       
        self._log_debug(f"movel: Executing linear movement at velocity {vel} mm/s")
        self.rob.movel(target_pose, velocity=vel, acceleration=acc, async_move=asynchronous)
        self._rob_loc = pos if pos is not None else None
        self.print_lj()
        self._log_debug(f"movel: Successfully completed linear movement")
            


    def home(self):
        self.movej("safe_rack")
        self._rob_loc = "safe_rack"
#Passed the test with tray update-2025/10/13
    def vial_2_balance(self, vial_loc:str):
        if self._rob_loc !="safe_rack":
            raise ValueError("start position should be 'safe_rack'")
        if self._gripper_item is not None:
            raise ValueError("move to vial rack gripper must be None")
        self.gripper_pos(self.gripper_dist["open"]["vial"])
        self.movel("vial_stock_prep")
        empty_vial = self.vial_stock[vial_loc]
        self.movel(empty_vial.location)
        self.movel(z = -55, vel = 30)
        self.gripper_pos(self.gripper_dist["close"]["vial"])
        self._gripper_item = "vial"
        self.movel(z = 55, vel=30)
        self.movel("vial_stock_prep")
        self.movej("safe_rack")
        self.movej("home_prep_bal")
        self.movej("safe_bal")
        self.movel("prep_viap_drop",vel=30)
        self.movel("drop_vial",vel=20)
        self.gripper_pos(self.gripper_dist["open"]["vial"])
        # print("[Debug] Opening gripper...")
        self._gripper_item = None
        self.movel("prep_viap_drop",vel=20)
        self.movel("safe_bal")
        self.movej("home_prep_bal")
        self.movej("safe_rack")

#Passed the test with tray update-2025/10/13. The position of dose head can be adjusted slightly. but it doesn't affect that much
    def dose_2_balance(self,dose_loc:str):
        if self._rob_loc !="safe_rack":
            raise ValueError("start position should be 'safe_rack'")
        self.gripper_pos(self.gripper_dist["open"]["dose"])

        self.movej("dos_rack_prep")
        dose = self.dose_stock[dose_loc]
        self.movel(dose.location, vel=50)
        self.movel(x = 50, vel = 50)
        self.gripper_pos(self.gripper_dist["close"]["dose"])
        self._gripper_item = "dose"
        self.movel(z=3,vel=20)
        self.movel(x=-50,vel=20)
        self.movel(z=60,vel=20)
        self.movel("dose_stock_back",vel=20)
        self.movej("out_bal_prep")
        self.movel("dos_bal_in_prep",vel=20)
        self.movel("dos_head_up",vel=20)
        self.movel("dos_head_in",vel=20)
        self.gripper_pos(self.gripper_dist["open"]["dose"])
        self.movel("dos_bal_in_prep",vel=20)
        self.movel("out_bal_prep")
        self.movej("safe_rack")
        self._rob_loc = "safe_rack"


    #TODO: test this function
    #TODO: add dose_back function
    def vial_2_OT(self):
        if self._rob_loc != "safe_rack":
            raise ValueError("start position should be 'safe_rack'")
        if self._gripper_item is not None:
            raise ValueError("move to vial rack gripper must be None")
        self.gripper_pos(self.gripper_dist["open"]["vial"])
        print("[Debug] Opening gripper...")
        self.movej("home_prep_bal")
        self.movej("safe_bal")
        self.movel("prep_viap_drop")
        self.movel("drop_vial")
        self.gripper_pos(self.gripper_dist["close"]["vial"])
        print("[Debug] Closing gripper...")
        self.movel("prep_viap_drop")
        self.movel("safe_bal")
        self.movej("safe_bal_2_ot")
        self.movej("safe_ot")
        self.movej("prep_drop_ot")
        self.movel("drop_vial_ot")
        self.gripper_pos(self.gripper_dist["open"]["vial"])
        print("[Debug] Opening gripper...")

        self.movel("prep_drop_ot")
        self.movej("safe_ot")
        self.movej("safe_bal_2_ot")
        self.movej("safe_bal")
        self.movej("home_prep_bal")
        self.movej("safe_rack")
        self._rob_loc = "safe_rack"


    # def dose_stock_back(self):

if __name__ == "__main__":
    controller = URController("192.168.254.89")
    controller.activate_gripper()