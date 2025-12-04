import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from matterlab_opentrons import OpenTrons
from prefect import flow
from pathlib import Path
import time
import json
from pH_measure.pizerocam.src.image_req_client.ph_analyzer import pHAnalyzer
from dotenv import load_dotenv

load_dotenv()

@flow(log_prints=True)
def demo_flex(simulation: bool = True):
    otflex_password = os.environ.get("OPENTRONS_PASSWORD")
    if not otflex_password:
        raise ValueError("OPENTRONS_PASSWORD is not set in the environment. Please add it to your .env file without quotes or spaces.")
    ot = OpenTrons(host_alias="otflex", password=otflex_password, simulation=simulation)
    print(ot.invoke("print([slot for slot in protocol.deck])"))
    print("SSH connected.")
    print(ot.invoke("from opentrons import execute"))
    print(ot.invoke("protocol = execute.get_protocol_api('2.21')"))
    ot.home()

    # Load labware
    with open(Path(r"C:\Users\xmguo\project\solid_dosing\matterlab_opentrons\20mlvial_6_wellplate.json"), "r") as f:
        vial_config_6 = json.load(f)
    with open(Path(r"C:\Users\xmguo\project\solid_dosing\matterlab_opentrons\phunit.json"), "r") as f:
        ph_config = json.load(f)
    with open(Path(r"C:\Users\xmguo\project\solid_dosing\matterlab_opentrons\al24wellplate_24_wellplate_15000ul.json"), "r") as f:
        vial_config_24 = json.load(f)

    plates = [
        {"nickname": "plate_96_1", "loadname": "corning_96_wellplate_360ul_flat", "location": "C2", "ot_default": True, "config": {}},
        {"nickname": "vial_plate_6", "loadname": "20mlvial_6_wellplate", "location": "C1", "ot_default": False, "config": vial_config_6},
        {"nickname": "phunit", "loadname": "phunit", "location": "D1", "ot_default": False, "config": ph_config},
        {"nickname": "vial_plate_24", "loadname": "al24wellplate", "location": "B3",  "ot_default": False, "config": vial_config_24}
    ]

    tips = [
        {"nickname": "tip_1000_96_1", "loadname": "opentrons_flex_96_filtertiprack_1000ul", "location": "A2", "ot_default": True, "config": {}},
        {"nickname": "tip_50_96_1", "loadname": "opentrons_flex_96_filtertiprack_50ul", "location": "B2", "ot_default": True, "config": {}}
    ]

    for plate in plates:
        ot.load_labware(plate)
    for tip in tips:
        ot.load_labware(tip)

    ot.load_trash_bin()
    ot.load_instrument({"nickname": "p1000", "instrument_name": "flex_1channel_1000", "mount" : "left", "tip_racks": ["tip_1000_96_1"],"ot_default": True})

    # Wells and volume plan
    # well_list = ["A1","A2","A3","A4","A5","A6","A7"]
    # # well_list = ["D1","D2","D3","D4","D5","D6","D7"]
    # # well_list = ["C6","C7"]
    # mixtures = [
    #     (0, 300),
    #     (50, 250),
    #     (100, 200),
    #     (150, 150),
    #     (200, 100),
    #     (250, 50),
    #     (300, 0)
    # ]



    # # --------- 1. Dispense all acids with one tip ---------
    # #tip_acid = ot.get_location_from_labware("tip_1000_96_1")
    # tip_location = ot.get_location_from_labware(labware_nickname="tip_1000_96_1", position="A1", top=0)
    # ot.pick_up_tip(pip_name="p1000")
    # for i, (v_acid, _) in enumerate(mixtures):
    #     well = well_list[i]
    #     ot.get_location_from_labware("vial_plate_6", position="A1", top=-50)
    #     ot.move_to_pip(pip_name="p1000")
    #     ot.aspirate(pip_name="p1000", volume=v_acid)
    #     ot.get_location_from_labware("plate_96_1", position=well, top=1)
    #     ot.move_to_pip(pip_name="p1000")
    #     ot.dispense(pip_name="p1000", volume=v_acid)
    # ot.drop_tip(pip_name="p1000")

    #tip_location = ot.get_location_from_labware(labware_nickname="tip_1000_96_1", position="A1", top=0)
    
    well_list = ["A6","B6"]
    for well in well_list:
         ot.pick_up_tip(pip_name="p1000")
         ot.get_location_from_labware("vial_plate_6", position="A1", top=-55)
         ot.move_to_pip(pip_name="p1000")
         ot.aspirate(pip_name="p1000", volume=200)
         ot.get_location_from_labware("vial_plate_24", position=well, top=-30)
         ot.move_to_pip(pip_name="p1000")
         ot.dispense(pip_name="p1000", volume=200)
         ot.drop_tip(pip_name="p1000")


    # # --------- 2. Dispense all NaHCO3 with second tip ---------
    # #tip_base = ot.get_location_from_labware("tip_1000_96_1")
    # tip_location = ot.get_location_from_labware(labware_nickname="tip_1000_96_1", position="A2", top=0)
    # ot.pick_up_tip(pip_name="p1000")
    # for i, (_, v_base) in enumerate(mixtures):
    #     well = well_list[i]
    #     ot.get_location_from_labware("vial_plate", position="B1", top=-50)
    #     ot.move_to_pip(pip_name="p1000")
    #     ot.aspirate(pip_name="p1000", volume=v_base)
    #     ot.get_location_from_labware("plate_96_1", position=well, top=1)
    #     ot.move_to_pip(pip_name="p1000")
    #     ot.dispense(pip_name="p1000", volume=v_base)
    # ot.drop_tip(pip_name="p1000")


    #tip_positions = ["A2","A3","A4","A5"]  # assign one tip per well

    # for i, well in enumerate(well_list):
    #     #tip_pos = tip_positions[i]  # pick a unique tip
    #     #tip_location = ot.get_location_from_labware(labware_nickname="tip_1000_96_1", position=tip_pos, top=0)
    #     ot.pick_up_tip(pip_name="p1000")
    #     # Move to well for mixing
    #     ot.get_location_from_labware("vial_plate_24", position=well, top=-41)
    #     ot.move_to_pip(pip_name="p1000")
    #     # Mix: aspirate and dispense several times
    #     mix_volume = 500  # adjust as needed
    #     for _ in range(2):
    #         ot.aspirate(pip_name="p1000", volume=mix_volume)
    #         ot.dispense(pip_name="p1000", volume=mix_volume)
    #     # Aspirate 50 µL for pH measurement
    #     ot.aspirate(pip_name="p1000", volume=20)
        # Move to pH measurement unit
    #     ph_location = ot.get_location_from_labware(labware_nickname="phunit", position="A1", top=-6)
    #     ot.move_to_pip(pip_name="p1000")
    #     analyzer = pHAnalyzer()
    #     analyzer.dispense_strip()
    #     # Dispense into pH unit
    #     ot.dispense(pip_name="p1000", volume=20)
    #     # Measure pH
    #     time.sleep(1)  # wait for a moment to ensure the sample is ready
    #     ph_value = analyzer.read_ph()
    #     # Drop tip
    #     ot.drop_tip(pip_name="p1000")
    #     analyzer.dispense_strip()
    #     time.sleep(1)  # small delay between measurements
    #     analyzer.dispense_strip()

    # print("\nProtocol finished.")

    # ot.home()
    # ot.close_session()
    return results  # Return results for saving outside the flow

if __name__ == "__main__":
    results = demo_flex(False)  # Run protocol and collect results
    # Save results to CSV (plain Python, not in Prefect flow)
    import csv
    output_path = os.path.join(os.path.dirname(__file__), "ph_results.csv")
    if results:
        with open(output_path, "w", newline="") as csvfile:
            fieldnames = ["well", "v_acid", "v_base", "pH"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in results:
                writer.writerow(row)
        print(f"\nResults saved to {output_path}\n")
    else:
        print("No results to save.")
