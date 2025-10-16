import sys
import os
os.environ["PREFECT_API_URL"] = "None"
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from prefect import flow
import time
from matterlab_opentrons import OpenTrons

@flow(log_prints=True)
def demo_flex(simulation: bool = True):
    ot = OpenTrons(host_alias="otflex", password="accelerate", simulation=simulation)
    print("SSH connected.")
    # OpenTrons.home(ot)  
    print(ot.invoke("from opentrons import execute"))
    print(ot.invoke("protocol = execute.get_protocol_api('2.21')"))
    OpenTrons.home(ot)
    plates = [
        {"nickname": "plate_96_1", "loadname": "corning_96_wellplate_360ul_flat", "location": "B3", "ot_default": True, "config": {}}
    ]
    tips = [
        {"nickname": "tip_1000_96_1", "loadname": "opentrons_flex_96_filtertiprack_1000ul", "location": "A2", "ot_default": True, "config": {}},
        {"nickname": "tiprack_1", "loadname": "opentrons_flex_96_filtertiprack_1000ul", "location": "D2", "ot_default": True, "config": {}}
    ]
    for plate in plates:
        OpenTrons.load_labware(ot, plate)
    for tip in tips:
        OpenTrons.load_labware(ot, tip)

    OpenTrons.load_instrument(ot, {"nickname": "p1000", "instrument_name": "flex_1channel_1000", "mount": "left", "ot_default": True})

    # 去 D2 取 tip
    OpenTrons.get_location_from_labware(ot, labware_nickname="tiprack_1", position="A1", top=0)
    OpenTrons.pick_up_tip(ot, pip_name="p1000")
    # 丢弃 tip 到垃圾桶
    OpenTrons.drop_tip(ot, pip_name="p1000")
    OpenTrons.close_session(ot)

if __name__ == "__main__":
    demo_flex(False)
