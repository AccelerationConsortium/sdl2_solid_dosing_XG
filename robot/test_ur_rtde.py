from rtde_control import RTDEControlInterface as rtc
from rtde_receive import RTDEReceiveInterface as rtr
import time
import numpy as np

def test_movej():
    rtde_c = rtc("192.168.254.89")
    rtde_r = rtr("192.168.254.89")

    joints = rtde_r.getActualQ()
    print("Current joints:", joints)
    joints[-1] += 1
    print("Moving joints to:", joints)
    rtde_c.moveJ(joints, speed=0.5, acceleration=0.5, asynchronous=False)
    # joints: rads, speed: rads/s, acceleration: rads/s^2
    print("Moved joints to:", joints)
    joints[-1] -= 1
    print("Returning joints to:", joints)
    rtde_c.moveJ(joints, speed=0.5, acceleration=0.5,  asynchronous=False)
    print("Returned joints to:", joints)

if __name__ == "__main__":
    test_movej()