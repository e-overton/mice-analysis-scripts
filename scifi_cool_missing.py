#!/bin/env python
"""
Script to look for missing tracks in downstream detector
"""

# Imports
import os
import ROOT
import libMausCpp  # pylint: disable = W0611
from TOFTools import TOF12CoincidenceTime, TOF1SingleHit, TOF01Times, TOF01CoincidenceTime
from SciFiTools import UnsaturatedCluster
from PlotSciFiEvent import PlotSciFiEvent
from ROOTTools import CombinedNorm
import math

max_spills = 0  # 0 Will run over all data

#for MC
#inpath = "/home/ed/MICE/data/efficiency_investigation/mc"
#infiles = []
#for f in os.listdir(inpath):
#    if f[5:] == "_sim.root":
#        infiles.append(os.path.join(inpath, f))

infiles = ["/home/ed/MICE/data/cooling/08681_recon.root"] # bad 140mev data
#infiles = ["/home/ed/MICE/data/08672_recon.root"] # good 240mev data
#infiles = ['/home/ed/MICE/data/efficiency_investigation/high_sz_2_6_0.root']

# Load data for processing:
print "Setting up ROOT TChain"
chain = ROOT.TChain("Spill")

for f in infiles:
    print "Appending file: ", f
    chain.AddFile(f)
    
data = ROOT.MAUS.Data()  # pylint: disable = E1101
chain.SetBranchAddress("data", data)

TH1D_unusedsp_US = ROOT.TH1D("TH1D_unusedsp_US", "Unused upstream spacepoints",
                             15, -0.5, 14.5)
TH1D_unusedsp_DS = ROOT.TH1D("TH1D_unusedsp_DS", "Unused downstream spacepoints",
                             15, -0.5, 14.5)
TH1D_unusedsptk_US = ROOT.TH1D("TH1D_unusedsptk_US", "Unused upstream spacepoints with track",
                             15, -0.5, 14.5)
TH1D_unusedsptk_DS = ROOT.TH1D("TH1D_unusedsptk_DS", "Unused downstream spacepoints with track",
                             15, -0.5, 14.5)
TH1D_5misslly_DS = ROOT.TH1D("TH1D_5misslly_DS", "DS 5 missing light yield",
                             25, -0.5, 24.5)
TH1D_5misslly_US = ROOT.TH1D("TH1D_5misslly_US", "US 5 missing light yield",
                             25, -0.5, 24.5)

TH1D_tof01 = ROOT.TH1D("TH1D_tof01", "TOF01", 100, 0, 50)

TH1D_stationsum_us = ROOT.TH1D("TH1D_stationsum_us", "Sum of station numbers US in 5 unused",
                             30, -0.5, 29.5)

TH1D_stationsum_ds = ROOT.TH1D("TH1D_stationsum_ds", "Sum of station numbers DS in 5 unused",
                             30, -0.5, 29.5)


trip_duplet_us = [0,0]
trip_duplet_ds = [0,0]

# find awesome events
aswesome_events = []


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
        print "  ", j, ":",

        # Check TOF:
        TOF1_singlehit = TOF1SingleHit(recon_event.GetTOFEvent())
        TOF12_coincidence = TOF12CoincidenceTime(recon_event.GetTOFEvent())
        TOF01_cut = TOF01CoincidenceTime(recon_event.GetTOFEvent(), 29.5, 31)

        # Fill unused spacepoints:
        if TOF1_singlehit and TOF12_coincidence and TOF01_cut:
            us_unused = 0
            ds_unused = 0
            us_unusedtrip = 0
            ds_unusedtrip = 0
            us_station_sum = 0
            ds_station_sum = 0
            for sp in recon_event.GetSciFiEvent().spacepoints():
                if not sp.is_used():
                    if sp.get_tracker() == 0:
                        us_unused += 1
                        if len(sp.get_channels()) == 3:
                            us_unusedtrip += 1 
                    else:
                        ds_unused += 1
                        if len(sp.get_channels()) == 3:
                            ds_unusedtrip += 1 
            us_track = False
            ds_track = False
            for tk in recon_event.GetSciFiEvent().scifitracks():
                if tk.tracker() == 0:
                    us_track = True
                else:
                    ds_track = True

            for time in TOF01Times(recon_event.GetTOFEvent().GetTOFEventSpacePoint()):
                TH1D_tof01.Fill(time)

            if us_unused == 5 and not us_track:
                for sp in recon_event.GetSciFiEvent().spacepoints():
                    if sp.get_tracker() == 0:
                        us_station_sum += sp.get_station()
                        if len(sp.get_channels()) == 3:
                            trip_duplet_us[0] += 1
                        else:
                            for cl in sp.get_channels():
                                TH1D_5misslly_US.Fill(UnsaturatedCluster(cl))
                            trip_duplet_us[1] += 1
                TH1D_stationsum_us.Fill(us_station_sum)

            if ds_unused == 5 and not ds_track:
                for sp in recon_event.GetSciFiEvent().spacepoints():
                    if sp.get_tracker() == 1:
                        ds_station_sum += sp.get_station()
                        if len(sp.get_channels()) == 3:
                            trip_duplet_ds[0] += 1
                        else:
                            for cl in sp.get_channels():
                                TH1D_5misslly_DS.Fill(UnsaturatedCluster(cl))
                            trip_duplet_ds[1] += 1
                TH1D_stationsum_ds.Fill(ds_station_sum)

            #if (us_unused == 5 and ds_unused == 5) and (not us_track and not ds_track)\
            #    and us_unusedtrip == 5  and ds_unusedtrip == 5:
            if (ds_unused == 5 and ds_unusedtrip == 5 and not ds_track and ds_station_sum==15):
            
                print " AWE",
                aswesome_events.append(spill.GetSpillNumber()*1000+j)
                #event = PlotSciFiEvent()
                #event.fill(recon_event.GetSciFiEvent())
                #event.draw()
                #raw_input ("press enter to continue")



            if us_track:
                TH1D_unusedsptk_US.Fill(us_unused)
            else:
                TH1D_unusedsp_US.Fill(us_unused)
            if ds_track:
                TH1D_unusedsptk_DS.Fill(ds_unused)
            else:
                TH1D_unusedsp_DS.Fill(ds_unused)


        #Check TKU:
        #track_tku = False
        #track_tkd = False
        #for track in recon_event.GetSciFiEvent().scifitracks():
        #    if track.tracker() == 0:
        #        track_tku = track
        #    if track.tracker() == 1:
        #        track_tkd = track

        #if TOF1_singlehit and TOF12_coincidence and track_tku and not track_tkd:
        #    print " MISS", 

        #    event = PlotSciFiEvent()
        #    event.fill(recon_event.GetSciFiEvent())
        #    event.draw()
        #    raw_input ("press enter to continue")

        print ""


c = ROOT.TCanvas("c1", "c1", 800, 600)
c.Divide(2,1)
c.cd(1)
CombinedNorm([TH1D_unusedsptk_US, TH1D_unusedsp_US])
TH1D_unusedsptk_US.Draw()
TH1D_unusedsp_US.SetFillColor(ROOT.kRed)
TH1D_unusedsp_US.SetFillStyle(3004)
TH1D_unusedsp_US.Draw("same")

c.cd(2)
CombinedNorm([TH1D_unusedsptk_DS, TH1D_unusedsp_DS])
TH1D_unusedsptk_DS.Draw()
TH1D_unusedsp_DS.SetFillColor(ROOT.kRed)
TH1D_unusedsp_DS.SetFillStyle(3004)
TH1D_unusedsp_DS.Draw("same")

c2 = ROOT.TCanvas("ly", "ly", 800, 600)
c2.Divide(2,1)
c2.cd(1)
TH1D_5misslly_US.Draw()
c2.cd(2)
TH1D_5misslly_DS.Draw()

c3 = ROOT.TCanvas("stationsum", "stationsum", 800, 600)
c3.Divide(2,1)
c3.cd(1)
TH1D_stationsum_us.Draw()
c3.cd(2)
TH1D_stationsum_ds.Draw()

c4 = ROOT.TCanvas("c3", "c3", 800, 600)
c4.cd()
TH1D_tof01.Draw()


print trip_duplet_us
print trip_duplet_ds

with open('ds_bad.txt', 'w') as f:
    for a in aswesome_events:
        f.write('%i\n'%a)
        #print(a, file=f)


#print aswesome_events

raw_input ("press enter to continue")

