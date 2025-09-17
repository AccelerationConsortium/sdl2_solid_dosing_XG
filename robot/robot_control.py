from rtde_control import RTDEControlInterface as rtc
from rtde_receive import RTDEReceiveInterface as rtr
import socket
import time
import json
import numpy as np

class URController:
    def reconnect_rtde(self, max_retries=3, delay=1.0):
        """
        Attempt to reconnect RTDE interfaces. Returns True if successful, False otherwise.
        """
        for attempt in range(max_retries):
            try:
                print(f"[Reconnect] Attempt {attempt+1} to reconnect RTDE...")
                self.rtde_c = rtc(self.gripper_ip)
                self.rtde_r = rtr(self.gripper_ip)
                # Test connection
                _ = self.rtde_r.getActualQ()
                print("[Reconnect] RTDE reconnected successfully.")
                return True
            except Exception as e:
                print(f"[Reconnect] Failed: {e}")
                time.sleep(delay)
        print("[Reconnect] Could not reconnect RTDE after retries.")
        return False
    
    def __init__(self, ur_ip="192.168.254.89", gripper_port=63352, location_file="ur3_0828_locations.json"):
        self.rtde_c = rtc(ur_ip)
        self.rtde_r = rtr(ur_ip)
        self.gripper_ip = ur_ip
        self.gripper_port = gripper_port
        self.gripper_dist = {
            "open":{"vial": 210, "dose": 165},
            "close":{"vial": 244, "dose": 178}
        }
        self._rob_loc = None
        self._gripper_item = None
        # Load locations from JSON file
        try:
            with open(location_file, 'r') as f:
                data = json.load(f)
                self.locations = data.get("rob_locations", {})
            print(f"Loaded {len(self.locations)} locations from {location_file}")
        except Exception as e:
            print(f"Error loading locations: {e}")
            self.locations = {}
    # def movel_to_location(self, loc_name, speed=0.5, acceleration=0.5, asynchronous=False):
    #     """
    #     Move linearly to a location using the 'l' (Cartesian pose) from JSON.
    #     """
    #     pose = self.locations.get(loc_name, {}).get("l")
    #     if not pose or len(pose) != 6:
    #         print(f"Location '{loc_name}' not found or invalid pose data.")
    #         return False
    #     print(f"Moving linearly to location '{loc_name}': {pose}")
    #     self.movel(pose=pose, speed=speed, acceleration=acceleration, asynchronous=asynchronous)
    #     return True

    def get_joints(self):
        joints = self.rtde_r.getActualQ()
        print("Current joints:", joints)
        return joints

    def movej(self, joints, speed=0.6, acceleration=0.6, asynchronous=False):
        if isinstance(joints, str):
            loc = self.locations.get(joints)
            if not loc or "j" not in loc or len(loc["j"]) != 6:
                print(f"Location '{joints}' not found or invalid joint data.")
                return
            joints = loc["j"]
        print("Moving joints to:", joints)
        try:
            self.rtde_c.moveJ(joints, speed=speed, acceleration=acceleration, asynchronous=asynchronous)
            print("Moved joints to:", joints)
        except Exception as e:
            print(f"[movej] RTDE error: {e}")
            if self.reconnect_rtde():
                try:
                    self.rtde_c.moveJ(joints, speed=speed, acceleration=acceleration, asynchronous=asynchronous)
                    print("Moved joints to:", joints)
                except Exception as e2:
                    print(f"[movej] Retry failed: {e2}")
            else:
                print("[movej] Could not reconnect to RTDE.")

    def movel(self, pose=None, x=0, y=0, z=0, rx=0, ry=0, rz=0, speed=0.6, acceleration=0.6, asynchronous=False):
        """
        Move linearly to a pose using RTDEControlInterface.moveL.
        - If pose is a string, look up the location's 'l' pose in self.locations.
        - If pose is a list/tuple, use it directly.
        - If pose is None, move relative to current TCP pose by (x, y, z, rx, ry, rz).
        """
        if isinstance(pose, str):
            loc = self.locations.get(pose, {})
            target_pose = loc.get("l")
            if not target_pose or len(target_pose) != 6:
                print(f"Location '{pose}' not found or invalid pose data.")
                return
        elif pose is None:
            current_pose = self.rtde_r.getActualTCPPose()
            target_pose = [
                current_pose[0] + x,
                current_pose[1] + y,
                current_pose[2] + z,
                current_pose[3] + rx,
                current_pose[4] + ry,
                current_pose[5] + rz
            ]
        else:
            if not isinstance(pose, (list, tuple)) or len(pose) != 6:
                print("Invalid pose. Must be a 6-element list or tuple.")
                return
            target_pose = list(pose)
        print(f"Moving linearly to: {target_pose}")
        try:
            self.rtde_c.moveL(target_pose, speed=speed, acceleration=acceleration, asynchronous=asynchronous)
            print("Linear move executed.")
        except Exception as e:
            print(f"[movel] RTDE error: {e}")
            if self.reconnect_rtde():
                try:
                    self.rtde_c.moveL(target_pose, speed=speed, acceleration=acceleration, asynchronous=asynchronous)
                    print("Linear move executed.")
                except Exception as e2:
                    print(f"[movel] Retry failed: {e2}")
            else:
                print("[movel] Could not reconnect to RTDE.")

    def print_lj(self):
        """
        Print current TCP pose (l) and joint positions (j) in the same format as the JSON file.
        """
        current_joints = self.rtde_r.getActualQ()
        current_pose = self.rtde_r.getActualTCPPose()
        print('{')
        print('  "l": [', ', '.join(f'{v:.5f}' for v in current_pose), '],')
        print('  "j": [', ', '.join(f'{v:.5f}' for v in current_joints), ']')
        print('}')

    def jog_joint(self, joint_index, delta, speed=0.5, acceleration=0.5):
        joints = self.get_joints()
        joints[joint_index] += delta
        self.movej(joints, speed, acceleration)
        joints[joint_index] -= delta
        self.movej(joints, speed, acceleration)

    def send_gripper_command(self, command):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(10)
                s.connect((self.gripper_ip, self.gripper_port))
                s.sendall(command.encode('utf-8') + b'\n')
                data = s.recv(1024)
                print(f"Sent: {command}")
                print("Response:", data.decode(errors="ignore"))
        except Exception as e:
            print("Gripper error:", e)

    def activate_gripper(self):
        self.send_gripper_command("SET ACT 1")
        time.sleep(0.5)

    def gripper_position(self, pos):
        pos = max(0, min(255, pos))
        self.send_gripper_command(f"SET POS {pos} GTO01")
        time.sleep(0.5)

    def home(self):
        self.movej("safe_rack")
        self._rob_loc = "safe_rack"

# Passed the test
    def vial_2_balance(self):
        if self._rob_loc !="safe_rack":
            raise ValueError("start position should be 'safe_rack'")
        if self._gripper_item is not None:
            raise ValueError("move to vial rack gripper must be None")
        self.gripper_position(self.gripper_dist["open"]["vial"])
        print("[Debug] Opening gripper...")
        self.movej("prep_vial")
        self.movel("A1vial_grip")
        self.gripper_position(self.gripper_dist["close"]["vial"])
        print("[Debug] Closing gripper...")
        self._gripper_item = "vial"
        self.movel("prep_vial")
        self.movej("safe_rack")
        self.movej("home_prep_bal")
        self.movej("safe_bal")
        self.movel("prep_viap_drop")
        self.movel("drop_vial")
        self.gripper_position(self.gripper_dist["open"]["vial"])
        print("[Debug] Opening gripper...")
        self._gripper_item = None
        self.movel("prep_viap_drop")
        self.movel("safe_bal")
        self.movej("home_prep_bal")
        self.movej("safe_rack")

#Passed the test
    def dose_2_balance(self):
        if self._rob_loc !="safe_rack":
            raise ValueError("start position should be 'safe_rack'")
        self.gripper_position(self.gripper_dist["open"]["dose"])
        self.movel("dos_rack_prep")
        self.movel("grip_dose")
        self.gripper_position(self.gripper_dist["close"]["dose"])
        self.movel("grip_dos_up")
        self.movel("dos_out_rack")
        self.movej("dos_rack_safe")
        self.movej("out_bal_prep")
        #self.movej("dos_bal_prep")
        self.movel("dos_bal_in_prep")
        #self.movel(x=0.0405)
        self.movel("dos_head_up")
        #self._rob_loc = "dos_head_up_h"        #self.movej("dos_head_up_h")
        #self.movel(z=-0.003)
        #self._rob_loc = "dos_head_in_h" 
        self.movel("dos_head_in")
        self.gripper_position(self.gripper_dist["open"]["dose"])
        self.movel("dos_bal_in_prep")
        # self.movej("dos_bal_prep")
        self.movel("out_bal_prep")
        #self.movej("dos_rack_safe")
        self.movej("safe_rack")
        self._rob_loc = "safe_rack"

    def vial_2_OT(self):
        if self._rob_loc != "safe_rack":
            raise ValueError("start position should be 'safe_rack'")
        if self._gripper_item is not None:
            raise ValueError("move to vial rack gripper must be None")
        self.gripper_position(self.gripper_dist["open"]["vial"])
        print("[Debug] Opening gripper...")
        self.movej("home_prep_bal")
        self.movej("safe_bal")
        self.movel("prep_viap_drop")
        self.movel("drop_vial")
        self.gripper_position(self.gripper_dist["close"]["vial"])
        print("[Debug] Closing gripper...")
        self.movel("prep_viap_drop")
        self.movel("safe_bal")
        self.movej("safe_bal_2_ot")
        self.movej("safe_ot")
        self.movej("prep_drop_ot")
        self.movel("drop_vial_ot")
        self.gripper_position(self.gripper_dist["open"]["vial"])
        print("[Debug] Opening gripper...")

        self.movel("prep_drop_ot")
        self.movej("safe_ot")
        self.movej("safe_bal_2_ot")
        self.movej("safe_bal")
        self.movej("home_prep_bal")
        self.movej("safe_rack")
        self._rob_loc = "safe_rack"

if __name__ == "__main__":
    controller = URRTDEController("192.168.254.89")
    controller.activate_gripper()
    controller.gripper_position(210)
    controller.jog_joint(-1, 1.0)