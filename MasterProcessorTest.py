#!/usr/bin/env python
"""
Some test scripts for testing things..
"""

import ROOT
import os
import libMausCpp
import pickle

from MasterProcessor import MasterProcessor
from ChannelAnalysis import ChannelAnalysisDigtProcessor
from FrontEndLookup import FrontEndLookup

filepath = "/home/ed/MICE/testdata/"
fname = "07410_recon.root"
maus_datafile = [os.path.join(filepath, fname)]

files = ["7367/7367_recon.root", "7369/7369_recon.root",
         "7370/7370_recon.root", "7372/7372_recon.root",
         "7373/7373_recon.root", "7375/7375_recon.root",
         "7376/7376_recon.root", "7377/7377_recon.root"]

maus_datafile = [os.path.join(filepath, f) for f in files]

# The SciFi calibration
maus_scifi_calibration = "%s/files/calibration/"\
    "scifi_calibration_2015-06-18.txt" % os.environ.get("MAUS_ROOT_DIR")

# The SciFi Mapping
maus_scifi_mapping = "%s/files/cabling/scifi_mapping_2015-06-18.txt"\
    % os.environ.get("MAUS_ROOT_DIR")

# The SciFi Mapping
# maus_scifi_badch = "%s/files/calibration/"\
#    "scifi_bad_channels_2015-06-18.txt" % os.environ.get("MAUS_ROOT_DIR")
maus_scifi_badch = "temp_bad_channels.txt"

lookup = FrontEndLookup(maus_scifi_mapping, maus_scifi_calibration,
                        maus_scifi_badch)

print "Setting up ROOT TChain"
chain = ROOT.TChain("Spill")
for f in maus_datafile:
    print "Appending file: ", f
    chain.AddFile(f)

print "Setting up data"
tree = chain
data = ROOT.MAUS.Data()  # pylint: disable = E1101
tree.SetBranchAddress("data", data)

max_spills = 100000

# otuputter = ROOT.TFile("test.root","RECREATE")

dpro = ChannelAnalysisDigtProcessor(lookup)
master = MasterProcessor(digit_processors=[dpro])

# Process MAUS data ###########################################################
print "Beginning Processing"
for i in range(tree.GetEntries()):

    if i > max_spills:
        break

    print "Spill", i, "/", tree.GetEntries(), "###############################"

    tree.GetEntry(i)
    spill = data.GetSpill()

    # Skip non-physics events:
    if spill.GetDaqEventType() != "physics_event":
        continue

    # Process recon event:
    for j, recon_event in enumerate(spill.GetReconEvents()):

        master(recon_event.GetSciFiEvent())


pickle.dump(dpro, file('dpro.pickle', 'w'))


# otuputter.Write()
# otuputter.Close()
