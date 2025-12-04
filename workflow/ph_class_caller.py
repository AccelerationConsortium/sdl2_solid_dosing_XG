import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from pH_measure.pizerocam.src.image_req_client.ph_analyzer import pHAnalyzer

# Quick read
analyzer = pHAnalyzer()
#ph = analyzer.read_ph()
analyzer.read_ph()
analyzer.dispense_strip()


'''
# Full workflow
with pHAnalyzer() as analyzer:
    analyzer.dispense_strip()
    ph = analyzer.read_ph()
    print(f"pH: {ph}")
'''