from typing import NamedTuple, List
import os
import csv
import sys
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from matterlab_opentrons import OpenTrons
from pH_measure.pizerocam.src.image_req_client.ph_analyzer import pHAnalyzer
import time
import json
from pathlib import Path

load_dotenv()

# Define the experiment type
class PhExperiment(NamedTuple):
    well: str
    acid_volume: float
    base_volume: float

# Setup OpenTrons
class PhProtocol:
    def __init__(self, simulation: bool = True):
        self.otflex_setup(simulation)
        self.load_labware_and_instruments()

    def otflex_setup(self, simulation: bool = True):
        otflex_password = os.environ.get("OPENTRONS_PASSWORD")
        if not otflex_password:
            raise ValueError("OPENTRONS_PASSWORD is not set in the environment. Please add it to your .env file without quotes or spaces.")
        self.ot = OpenTrons(host_alias="otflex", password=otflex_password, simulation=simulation)
        print(self.ot.invoke("print([slot for slot in protocol.deck])"))
        print("SSH connected.")
        print(self.ot.invoke("from opentrons import execute"))
        print(self.ot.invoke("protocol = execute.get_protocol_api('2.21')"))
        self.ot.home()    


    def load_labware_and_instruments(self):
        # Load custom labware
        vial_config_6 = json.load(open(Path(r"C:\Users\xmguo\project\solid_dosing\matterlab_opentrons\20mlvial_6_wellplate.json")))
        ph_config = json.load(open(Path(r"C:\Users\xmguo\project\solid_dosing\matterlab_opentrons\phunit.json")))
        vial_config_24 = json.load(open(Path(r"C:\Users\xmguo\project\solid_dosing\matterlab_opentrons\al24wellplate_24_wellplate_15000ul.json")))

        plates = [
            {"nickname": "plate_96_1", "loadname": "corning_96_wellplate_360ul_flat", "location": "C2", "ot_default": True, "config": {}},
            {"nickname": "vial_plate_6", "loadname": "20mlvial_6_wellplate", "location": "C1", "ot_default": False, "config": vial_config_6},
            {"nickname": "phunit", "loadname": "phunit", "location": "D1", "ot_default": False, "config": ph_config},
            {"nickname": "vial_plate_24", "loadname": "al24wellplate", "location": "B3", "ot_default": False, "config": vial_config_24}
        ]

        tips = [
            {"nickname": "tip_1000_96_1", "loadname": "opentrons_flex_96_filtertiprack_1000ul", "location": "A2", "ot_default": True, "config": {}},
            {"nickname": "tip_50_96_1", "loadname": "opentrons_flex_96_filtertiprack_50ul", "location": "B2", "ot_default": True, "config": {}}
        ]

        for plate in plates:
            self.ot.load_labware(plate)
        for tip in tips:
            self.ot.load_labware(tip)

        self.ot.load_trash_bin()
        self.ot.load_instrument({"nickname": "p1000", "instrument_name": "flex_1channel_1000", "mount": "left", "tip_racks": ["tip_1000_96_1"], "ot_default": True})


    # Run a batch
    def run_batch(self, batch: List[PhExperiment]):
        ot = self.ot

        wells = [exp.well for exp in batch]

        # -------------------------
        # Acid with ONE tip
        # -------------------------
        ot.pick_up_tip(pip_name="p1000")

        for exp in batch:
            # Aspirate acid
            ot.get_location_from_labware("vial_plate_6", position="A1", top=-40)
            ot.move_to_pip(pip_name="p1000")
            ot.aspirate(pip_name="p1000", volume=exp.acid_volume)

            # Dispense into target well
            ot.get_location_from_labware("plate_96_1", position=exp.well, top=0)
            ot.move_to_pip(pip_name="p1000")
            ot.dispense(pip_name="p1000", volume=exp.acid_volume)

        ot.drop_tip(pip_name="p1000")


        # -------------------------
        # Base with ONE tip
        # -------------------------
        ot.pick_up_tip(pip_name="p1000")

        for exp in batch:
            # Aspirate base
            ot.get_location_from_labware("vial_plate_6", position="B1", top=-40)
            ot.move_to_pip(pip_name="p1000")
            ot.aspirate(pip_name="p1000", volume=exp.base_volume)

            # Dispense into target well
            ot.get_location_from_labware("plate_96_1", position=exp.well, top=0)
            ot.move_to_pip(pip_name="p1000")
            ot.dispense(pip_name="p1000", volume=exp.base_volume)

        ot.drop_tip(pip_name="p1000")


        # -------------------------
        # Mix + pH test (NEW TIP per well)
        # -------------------------
        results = {}

        # for exp in batch:
        #     print(f"--- Mixing and measuring pH for {exp.well} ---")

        #     ot.pick_up_tip(pip_name="p1000")

        #     # Mix 3×
        #     for _ in range(3):
        #         ot.get_location_from_labware("plate_96_1", position=exp.well, top=-6)
        #         ot.move_to_pip(pip_name="p1000")
        #         ot.aspirate(pip_name="p1000", volume=100)
        #         ot.dispense(pip_name="p1000", volume=100)

        #     # Aspirate for pH test
        #     ot.get_location_from_labware("plate_96_1", position=exp.well, top=-6)
        #     ot.move_to_pip(pip_name="p1000")
        #     ot.aspirate(pip_name="p1000", volume=25)

        #     # Move to pH unit
        #     ph_location = ot.get_location_from_labware("phunit", position="A1", top=-6)
        #     ot.move_to_pip(pip_name="p1000")

        #     # Prepare strip
        #     analyzer = pHAnalyzer()
        #     analyzer.dispense_strip()

        #     # Dispense into pH strip
        #     ot.dispense(pip_name="p1000", volume=20)

        #     time.sleep(1)
        #     ph_value = analyzer.read_ph()

        #     # Cleanup
        #     ot.drop_tip(pip_name="p1000")
        #     analyzer.dispense_strip()
        #     time.sleep(1)
        #     analyzer.dispense_strip()

        #     results[exp.well] = ph_value

        return results


# Example usage
if __name__ == "__main__":
    # Example experiments
    batch = [
        PhExperiment(well="A1", acid_volume=150, base_volume=150)
        # PhExperiment(well="B1", acid_volume=175, base_volume=250),
        # PhExperiment(well="C1", acid_volume=300, base_volume=60)
    ]

    protocol = PhProtocol(simulation=True)
    results = protocol.run_batch(batch)
    print("Batch results:", results)
