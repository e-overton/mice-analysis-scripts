#!/usr/bin/env python

"""
Quick script for calculating the sections of the detector which
are not reading out (dead channels/fibres)
"""

# Imports
import os
import csv
import ROOT
import argparse
import libMausCpp  # pylint: disable = W0611

from SciFiTools import FindDeadChansHist, StationDeadProbability
from FrontEndLookup import FrontEndLookup

###############################################################################
# Argument parsing:
###############################################################################
# parser = argparse.ArgumentParser()
# parser.add_argument("output_path", help="the path to put the output",
#                     type=str)
# parser.add_argument("input_path", help="the path to find the input",
#                     type=str)
# parser.add_argument("mapping_file", help="the scifi mapping used",
#                     type=str)
# parser.add_argument("calibration_file", help="the scifi calibration used",
#                     type=str)
# parser.add_argument("run_start", help="the output name for the data output",
#                     type=int)
# parser.add_argument("run_end", help="the output name for the data output",
#                     type=int)
# 
# 
# args = parser.parse_args()
# print vars(args)

# Generate Lookup object
maus_scifi_calibration = "%s/files/calibration/"\
    "scifi_calibration_2015-06-18.txt" % os.environ.get("MAUS_ROOT_DIR")
maus_scifi_mapping = "%s/files/cabling/scifi_mapping_2015-09-11.txt"\
    % os.environ.get("MAUS_ROOT_DIR")

# Parameters
inpath = "/home/ed/MICE/testdata/"
infiles = ["%05d_recon.root" % i for i in range(7515, 7547)]
# infiles = ["07417_recon.root"]
outrootfile = "dead_07515.root"
outcsvfile = "dead_07515.csv"
max_spills = 0  # 0 Will run over all data
lookup = FrontEndLookup(maus_scifi_mapping, maus_scifi_calibration)

###############################################################################
# Main Script
###############################################################################

# Initilise memory elements:
print "Setting up memory elements"
ch_hists = {}
for tracker in [0,1]:
    for station in range(1,6):
        for plane in range (3):
            basename = "%i_%i_%i" % (tracker, station, plane)
            ch_hists["chist_"+basename] = ROOT.TH1D("chist_"+basename,
                                                    "chist_"+basename,
                                                    220, -0.5, 219.5)
# Load data for processing:
print "Setting up ROOT TChain"
chain = ROOT.TChain("Spill")

for infile in infiles:
    f = os.path.join(inpath, infile)
    print "Appending file: ", f
    chain.AddFile(f)

data = ROOT.MAUS.Data()  # pylint: disable = E1101
chain.SetBranchAddress("data", data)

# Begin the processing
print "Beginning Processing"
for i in range(chain.GetEntries()):
    print "Spill", i, "/", chain.GetEntries()
    if max_spills > 0 and i > max_spills:
        break
    chain.GetEntry(i)
    spill = data.GetSpill()
    if spill.GetDaqEventType() != "physics_event":
        continue

    for j, recon_event in enumerate(spill.GetReconEvents()):
        # print j, ":",

        # Look for all triplet spacepoints and store the channel hits
        # which made them. Dead fibres cannot contribute triplets.
        for sp in recon_event.GetSciFiEvent().spacepoints():
            if len(sp.get_channels()) == 3:
                tracker = sp.get_tracker()
                station = sp.get_station()

                # Add clusters which are over an npe cut:
                for cluster in sp.get_channels():
                    for digit in cluster.get_digits():
                        if digit.get_npe() > 3:
                            plane = digit.get_plane()
                            basename = "%i_%i_%i" % (tracker, station, plane)
                            ch_hists["chist_"+basename].Fill(digit.get_channel())

###############################################################################
# Process Hits
###############################################################################

# Loop over all hits and populate the dead channels list:
deadchans = {}
for tracker in range(2):
    for station in range(1, 6):
        basename = "%i_%i" % (tracker, station)
        deadchans[basename] = []
        for plane in range(3):
            hist = ch_hists["chist_"+basename+"_%i" % plane]
            dchs = FindDeadChansHist(hist)
            for c in dchs:
                c["plane"] = plane
                c["tracker"] = tracker
                c["station"] = station
            deadchans[basename].extend(dchs)

# Dump this into a csv file:
with open(outcsvfile, 'w') as csvfile:
    fieldnames = ['tracker', 'station', 'plane', 'trchannel',
                  'channelUID', 'board', 'bank', 'elchannel']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for tracker in range(2):
        for station in range(1, 6):
            for c in deadchans["%i_%i" % (tracker, station)]:
                try:
                    mapch = lookup.GetChannel(c["tracker"], c["station"],
                                              c["plane"], c["channel"])
                except LookupError:
                    pass
                else:
                    row = {}
                    for key, value in c.iteritems():
                        if row in fieldnames:
                            row[key] = value
                    for key, value in mapch.iteritems():
                        if key in fieldnames:
                            row[key] = value
                    writer.writerow(row)


# Print out the dead channels:
print "==================================================================="
print "Dead Channels found.."
print "---------------------------------------------------"
for tracker in range(2):
    for station in range(1, 6):
        print ""
        print "Tracker: %i, Station %i" % (tracker, station)
        print ""
        dchs = deadchans["%i_%i" % (tracker, station)]
        tripineff = 0.0
        tripineff_err = 0.0
        for c in dchs:
            try:
                mapch = lookup.GetChannel(tracker, station,
                                          c["plane"], c["channel"])
                uid = mapch["channelUID"]
            except LookupError:
                uid = -1
            if uid > 0:
                print "%i  %i  %i  %.3e %.3e" % (c["plane"], c["channel"],
                                            uid, c["probability"],c["prob_error"])
            tripineff += c["probability"]
            tripineff_err += c["prob_error"]
        print ""
        print "Number Dead Channels %i" % len(dchs)
        print "Missing Probability  %.6f +- %.6f" % StationDeadProbability(dchs)
        print "Triplet Inefficiency %.6f +- %.6f" % (tripineff, tripineff_err)
        print ""
        print "---------------------------------------------------"


# Save dead channel histograms:
c_upstr = ROOT.TCanvas("cu","Upstream Planes", 600, 900)
c_upstr.Divide(3,5)
for station in range(1, 6):
    for plane in range(3):
        c_upstr.cd(1+plane+(station-1)*3)
        basename = "%i_%i_%i" % (0, station, plane)
        ch_hists["chist_"+basename].Draw()

c_dnstr = ROOT.TCanvas("cd","Downstream Plances", 600, 900)
c_dnstr.Divide(3,5)
for station in range(1, 6):
    for plane in range(3):
        c_dnstr.cd(1+plane+(station-1)*3)
        basename = "%i_%i_%i" % (1, station, plane)
        ch_hists["chist_"+basename].Draw()


# Save all histograms:
tf = ROOT.TFile(outrootfile, "RECREATE")
for h in ch_hists:
    ch_hists[h].Write()
tf.Write()
tf.Close()

raw_input("Finished")
                