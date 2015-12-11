#!/usr/bin/env python

"""
Quick script for finding the efficiency of the detector.
"""
# Imports
import os
import ROOT
import libMausCpp  # pylint: disable = W0611
from TOFTools import TOF12CoincidenceTime
from SpacepointTools import unsaturatedCluster
from ROOTTools import TemplateFitter, IntegrateExpErr
import math

# Parameters
inpath = "/home/ed/MICE/testdata/"
#infiles = ["%05d_recon.root" % i for i in range(7515, 7547)]
infiles = ["7367/7367_recon.root", "7369/7369_recon.root",
           "7370/7370_recon.root", "7372/7372_recon.root",
           "7373/7373_recon.root", "7375/7375_recon.root",
           "7376/7376_recon.root", "7377/7377_recon.root"]
max_spills = 0

outrootfile = "7367_efficiency.root"

###############################################################################
# Main Script
###############################################################################

# Initilise memory elements:
print "Setting up memory elements"
counts = {}
counts["TOF12_Coinc"] = 0
th1ds = {}
for tracker in [0, 1]:
    for station in range(1, 6):
        basename = "Trk_%i_%i_" % (tracker, station)
        counts[basename + "triplet"] = 0
        counts[basename + "duplet"] = 0
        th1ds[basename + "triplet"] = ROOT.TH1D(basename+"triplet",
                                                basename+"triplet",
                                                30, -0.5, 29.5)
        th1ds[basename + "duplet"] = ROOT.TH1D(basename+"duplet",
                                               basename+"duplet",
                                               30, -0.5, 29.5)

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
        print j, ":",

        if TOF12CoincidenceTime(recon_event.GetTOFEvent()):
            print " TOF12",
            counts["TOF12_Coinc"] += 1

            # First look for triplets in each station
            tripletfound = [0] * 10
            for sp in recon_event.GetSciFiEvent().spacepoints():
                if len(sp.get_channels()) == 3:
                    basename = "Trk_%i_%i_" % (sp.get_tracker(), sp.get_station())
                    tripletfound[sp.get_tracker()*5+sp.get_station()-1] = 1
                    counts[basename + "triplet"] += 1
                    for cluster in sp.get_channels():
                        th1ds[basename + "triplet"].Fill\
                            (unsaturatedCluster(cluster))
            # Identify stations without triplets and store duplet
            # info
            for sp in recon_event.GetSciFiEvent().spacepoints():
                if len(sp.get_channels()) == 2:
                    if tripletfound[sp.get_tracker()*5+sp.get_station()-1] == 0:
                        basename = "Trk_%i_%i_" % (sp.get_tracker(), sp.get_station())
                        tripletfound[sp.get_tracker()*5+sp.get_station()-1] = 1
                        counts[basename + "duplet"] += 1
                        for cluster in sp.get_channels():
                            th1ds[basename + "duplet"].Fill\
                                (unsaturatedCluster(cluster))
        print ""

###############################################################################
# Post Processing
###############################################################################
eff = {}
for tracker in [0, 1]:
    for station in range(1, 6):
        print ""
        print " ============================================="
        print " = Now Processing: Tracker %i, Station %i ====" % (tracker, station)
        print ""
        basename = "Trk_%i_%i_" % (tracker, station)

        # Look at the efficiency we found triplets:
        c_triplet = float(counts[basename + "triplet"])
        eff[basename + "triplet"] = c_triplet/counts["TOF12_Coinc"]
        eff[basename + "triplet_err"] = math.sqrt(c_triplet)/counts["TOF12_Coinc"]
        print "Triplet Efficiency: %f, Error: %f" % \
            (eff[basename + "triplet"], eff[basename + "triplet_err"])

        # To understand the duplet stuff, we need to fir the light yields to
        # estimate the SNR from the duplets.
        bkg = ROOT.TF1("bkg", "expo", 2, 25)
        tempfunc = TemplateFitter(th1ds[basename + "triplet"], bkg)
        th1ds[basename + "triplet"].Draw()
        fit = ROOT.TF1("f", tempfunc, 2, 25, 4)
        fit.SetParameter(0, 0.05)
        fit.SetParameter(1, 100000)
        fit.FixParameter(2, 0)
        fit.SetParameter(3, -0.3)
        th1ds[basename + "triplet"].Draw("SAME")
        th1ds[basename + "duplet"].Fit(fit, "R", "SAME", 2, 25)

        intg, intg_err = IntegrateExpErr(fit.GetParameter(3), fit.GetParError(3), 2, 10)
        n_noise = intg*fit.GetParameter(1)
        n_noise_err = n_noise*math.sqrt (math.pow(intg_err/intg, 2) + 
                                         math.pow(fit.GetParError(1)/fit.GetParameter(1),2))

        print "Duplets from Noise %f, Error: %f" % (n_noise, n_noise_err)

        # Now subtract the estimated noise events:
        n_duplets = counts[basename + "duplet"] - n_noise
        n_duplets = 0.0 if n_duplets < 0 else n_duplets
        n_duplets_err = math.sqrt(n_duplets) + n_noise_err

        eff[basename + "duplet"] = float(n_duplets)/counts["TOF12_Coinc"]
        eff[basename + "duplet_err"] = n_duplets_err/counts["TOF12_Coinc"]
        print "Triplet Efficiency: %f, Error: %f" % \
            (eff[basename + "duplet"], eff[basename + "duplet_err"])

        # Cobined effieicny:
        eff[basename] = eff[basename + "triplet"] +  eff[basename + "duplet"]
        eff[basename+"err"] = eff[basename + "triplet_err"] + eff[basename + "duplet_err"]

        print "Combined Efficiency: %f, Error: %f" % \
            (eff[basename], eff[basename+"err"])

###############################################################################
# Finally make plots:
###############################################################################
th1ds["eff"] = ROOT.TH1D("eff", "Efficiency; Station[-ve=upstream]; Efficiency", 11, -5.5, 5.5)
for tracker in [0, 1]:
    for station in range(1, 6):
        basename = "Trk_%i_%i_" % (tracker, station)
        s = (-station) if tracker == 0 else (station)
        bin = th1ds["eff"].FindBin(s)
        th1ds["eff"].SetBinContent(bin,eff[basename])
        th1ds["eff"].SetBinError(bin,eff[basename+"err"])

th1ds["eff"].Draw()

# Save all histograms:
tf = ROOT.TFile(outrootfile, "RECREATE")
for h in th1ds:
    th1ds[h].Write()
tf.Write()
tf.Close()

raw_input ("Finale")
