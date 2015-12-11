#!/usr/bin/env python
"""
Some test scripts for testing things..
"""

import ROOT
import os
import libMausCpp  # @UnusedImport
import pickle

from MasterProcessor import MasterProcessor
from ChannelAnalysis import ChannelAnalysisDigtProcessor
from SpacepointAnalysis import SpacepointMultiplicityProcessor
from FrontEndLookup import FrontEndLookup
from TOFTools import TOF12CoincidenceTime
from EMRTools import EMRMuon

filepath = "/home/ed/MICE/testdata/"
# fname = "07410_recon.root"
# maus_datafile = [os.path.join(filepath, fname)]


# files = ["7367/7367_recon.root", "7369/7369_recon.root",
#         "7370/7370_recon.root", "7372/7372_recon.root",
#         "7373/7373_recon.root", "7375/7375_recon.root",
#         "7376/7376_recon.root", "7377/7377_recon.root"]

# files = ["07387_recon.root"]
# files = ["07475_recon.root"]
# files = ["07417_recon.root"]

files = ["%05d_recon.root" % i for i in range(7515, 7547)]
print files

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
chain = ROOT.TChain("Spill")  # @UndefinedVariable
for f in maus_datafile:
    print "Appending file: ", f
    chain.AddFile(f)

print "Setting up data"
tree = chain
data = ROOT.MAUS.Data()  # pylint: disable = E1101 @UndefinedVariable
tree.SetBranchAddress("data", data)

max_spills = 100000

# otuputter = ROOT.TFile("test.root","RECREATE")

dpro = ChannelAnalysisDigtProcessor(lookup)
tku_sp = SpacepointMultiplicityProcessor(0)
tkd_sp = SpacepointMultiplicityProcessor(1)
master = MasterProcessor(digit_processors=[dpro],
                         spacepoint_processors=[tku_sp, tkd_sp])

# Process MAUS data ###########################################################
print "Beginning Processing"
for i in range(tree.GetEntries()):

    if i > max_spills:
        break

    print "Spill", i, "/", tree.GetEntries(), "############################### ",

    tree.GetEntry(i)
    spill = data.GetSpill()
    print spill.GetSpillNumber()

    # Skip non-physics events:
    if spill.GetDaqEventType() != "physics_event":
        continue

    # Process recon event:
    for j, recon_event in enumerate(spill.GetReconEvents()):

        print j, ":",

        if TOF12CoincidenceTime(recon_event.GetTOFEvent()):
            print " TOF12",
            #if EMRMuon(recon_event.GetEMREvent()):
            #    print " EMR-MU",
            #print j, ", "
            master(recon_event.GetSciFiEvent())

        print ""


pickle.dump(tku_sp, file('tku_sp2.pickle', 'w'))
pickle.dump(tkd_sp, file('tkd_sp2.pickle', 'w'))
pickle.dump(dpro, file('dpro2.pickle', 'w'))


# otuputter.Write()
# otuputter.Close()
