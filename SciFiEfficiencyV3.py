#!/usr/bin/env python

"""
Quick script for finding the efficiency of the detector.
"""
# Imports
import os
import ROOT
import libMausCpp  # pylint: disable = W0611
from TOFTools import TOF12CoincidenceTime, TOF1SingleHit, TimeInSpill
from SciFiTools import UnsaturatedCluster, StationSpacePointEfficiency
from ROOTTools import TemplateFitter, IntegrateExpErr
import math

max_spills = 0000  # 0 Will run over all data

#inpath="/home/ed/MICE/data/maus_v2_running"
#outrootfile="output/eff_oct.root"
#infiles = []
#for f in os.listdir(inpath):
#    if f[5:] == "_recon.root":
#        infiles.append(os.path.join(inpath,f))
        
#infiles = ["/home/ed/MICE/data/08502_recon.root"]
infiles = ["/home/ed/MICE/data/cooling/08681_recon.root"]

tof1_hpixels = [2,3,4]
tof1_vpixels = [2,3,4]
tof2_hpixels = [4,5,6]
tof2_vpixels = [4,5,6]

spe_us = [StationSpacePointEfficiency\
          (0, i, "us_%i"%i) for i in range(1,6)]
spe_ds = [StationSpacePointEfficiency\
          (1, i, "ds_%i"%i) for i in range(1,6)]

# Load data for processing:
print "Setting up ROOT TChain"
chain = ROOT.TChain("Spill")

for f in infiles:
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

        if TOF12CoincidenceTime(recon_event.GetTOFEvent(),0,100) and\
            TOF1SingleHit(recon_event.GetTOFEvent()):

            # Check TOF1 Pixels:
            t1sp = recon_event.GetTOFEvent().GetTOFEventSpacePoint().\
            GetTOF1SpacePointArray()[0]

            if not (t1sp.GetHorizSlab() in tof1_hpixels) or\
               not (t1sp.GetVertSlab () in tof1_vpixels):

                continue

            # Check TOF2 Pixels:
            t2sp = recon_event.GetTOFEvent().GetTOFEventSpacePoint().\
            GetTOF2SpacePointArray()[0]

            if not (t2sp.GetHorizSlab() in tof2_hpixels) or\
               not (t2sp.GetVertSlab () in tof2_vpixels):

                continue
                pass

            # Downstream SPE:
            # Apply constraints from upstream tracker:
            #ustrack_ok = False
            #dstrack_ok = False
            #for track in recon_event.GetSciFiEvent().straightprtracks():
            #    # Project to opposite apeture:
            #    z_loc = -3800 -1100
            #    x = track.get_x0() + z_loc*track.get_mx()
            #    y = track.get_y0() + z_loc*track.get_my()
            #    if track.get_tracker() == 0:
            #        if math.sqrt(x*x+y*y) < 100:
            #            ustrack_ok = True
            #    else:
            #        if math.sqrt(x*x+y*y) < 100:
            #            dstrack_ok = True
            #for track in recon_event.GetSciFiEvent().helicalprtracks():
            #    sp_in_r = True
            #    for sp in track.

            ustrack_ok = True
            dstrack_ok = True

            if dstrack_ok == True:
                for s in spe_us:
                    s.fill(recon_event)

            if ustrack_ok == True:
                for s in spe_ds:
                    s.fill(recon_event)
# Generate plot:
for e in spe_us:
    e.compute()
for e in spe_ds:
    e.compute()


eff = ROOT.TH1D("eff", "Efficiency; Station[-ve=upstream]; Efficiency", 11, -5.5, 5.5)
for e in spe_us:
    s = -e.station
    bin = eff.FindBin(s)
    eff.SetBinContent(bin,e.eff)
    eff.SetBinError(bin,e.eff_err)

for e in spe_ds:
    s = e.station
    bin = eff.FindBin(s)
    eff.SetBinContent(bin,e.eff)
    eff.SetBinError(bin,e.eff_err)

eff.SetLineColor(ROOT.kBlack)
eff.Draw()


tf = ROOT.TFile(outrootfile, "RECREATE")
eff.Write()
for s in spe_us:
    tobjs = s.getTObjects()
    for t in tobjs:
        tobjs[t].Write()

for s in spe_ds:
    tobjs = s.getTObjects()
    for t in tobjs:
        tobjs[t].Write()
tf.Write()
tf.Close()
