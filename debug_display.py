#!/usr/bin/env python

"""
Example to load a ROOT file and make a histogram showing the beam profile at
TOF1
"""

import os
import subprocess

# basic PyROOT definitions
import ROOT 
import xboa.common

# definitions of MAUS data structure for PyROOT
import libMausCpp #pylint: disable = W0611
import itertools

def main():
    """
    Generates some data and then attempts to load it and make a simple histogram
    """
    print "Generating some data"
    #my_file_name = "/home/ed/MICE/testdata/maus2_07333.root"
    my_file_name = "/home/ed/MICE/testdata/maus_output_new-mapping-calibration_run7333.root"

    print "Loading ROOT file", my_file_name
    root_file = ROOT.TFile(my_file_name, "READ") # pylint: disable = E1101

    print "Setting up data tree"
    data = ROOT.MAUS.Data() # pylint: disable = E1101
    tree = root_file.Get("Spill")
    tree.SetBranchAddress("data", data)

    print "Getting some data"
    n_clusters_tku_hist = ROOT.TH2D("clusters hist", "all tracks in TKU;station number;number of clusters per space point", 5, 0.5, 5.5, 2, 1.5, 3.5)
    n_clusters_tku_hist.SetStats(False)
    n_clusters_tku_good_hist = ROOT.TH2D("good hist", "5 point tracks in TKU;station number;number of clusters per space point", 5, 0.5, 5.5, 2, 1.5, 3.5)
    n_clusters_tku_good_hist.SetStats(False)

    n_clusters_tkd_hist = ROOT.TH2D("clusters hist", "all tracks in TKD;station number;number of clusters per space point", 5, 0.5, 5.5, 2, 1.5, 3.5)
    n_clusters_tkd_hist.SetStats(False)
    n_clusters_tkd_good_hist = ROOT.TH2D("good hist", "5 point tracks in TKD;station number;number of clusters per space point", 5, 0.5, 5.5, 2, 1.5, 3.5)
    n_clusters_tkd_good_hist.SetStats(False)

    # Ed's Fun additional super bonus plots:
    peds_both_hist =  ROOT.TH2D("peds_both", "pedestals Both; channel no; ADC", 8192, -0.5, 8191.5, 256, -0.5, 255.5)
    peds_both_hist.SetStats(False)
    
    clusters_single_hist = ROOT.TH2D("clusters_singles", "clusters single Both; planeid [(tracker-1)*15 + (station-1)*3 + plane]; count/trigger", 30, -0.5, 29.5, 4, -0.5, 3.5)
    clusters_single_hist.SetStats(False) 
    clusters_double_hist = ROOT.TH2D("clusters_double", "clusters double Both; planeid [(tracker-1)*15 + (station-1)*3 + plane]; count/trigger", 30, -0.5, 29.5, 4, -0.5, 3.5)
    clusters_double_hist.SetStats(False)

    sp_duplets_hist = ROOT.TH2D("sp_duplets", "Duplets; stationid [(tracker-1)*5 + station-1]; count/trigger", 10, -0.5, 9.5, 4, -0.5, 3.5)
    sp_duplets_hist.SetStats(False)
    sp_triplet_hist = ROOT.TH2D("sp_triplets", "Triplets; stationid [(tracker-1)*5 + station-1]; count/trigger", 10, -0.5, 9.5, 4, -0.5, 3.5)
    sp_triplet_hist.SetStats(False)

    anayzed_triggers = 0

    for i in range(tree.GetEntries()):
        if i > 5000:
           continue
        print "Spill", i
        tree.GetEntry(i)
        spill = data.GetSpill()
        if spill.GetDaqEventType() == "physics_event":


            # =================================================================================================
            # Store the raw daq data to a histogram for plotting
            # =================================================================================================
            daq_event = spill.GetDAQData()
            for j, tracker_daq in enumerate(daq_event.GetTracker0DaqArray()):
                for k, vlsb in enumerate(tracker_daq.GetVLSBArray()):
                    peds_both_hist.Fill(128*vlsb.GetBankID() + vlsb.GetChannel(), vlsb.GetADC())

            for j, tracker_daq in enumerate(daq_event.GetTracker1DaqArray()):
                for k, vlsb in enumerate(tracker_daq.GetVLSBArray()):
                    peds_both_hist.Fill(128*vlsb.GetBankID() + vlsb.GetChannel(), vlsb.GetADC())

            
            for j, recon_event in enumerate(spill.GetReconEvents()):

                # =================================================================================================
                # Check that there is at least a coincidence hit in TOF1(H,V) and TOF2(H,V)
                # =================================================================================================
                # Note, I really have no idea which plane is horizontal and vertical, I just
                # want to see a hit in each (1,2)

                # TOF2 Checks:
                tof2_hhit, tof2_vhit = 0,0
                tof2_hit = False
                for tof2_slab_hit in recon_event.GetTOFEvent().GetTOFEventSlabHit().GetTOF2SlabHitArray():
                    if tof2_slab_hit.GetPlane() == 1:
                        tof2_hhit += 1
                    else:
                        tof2_vhit += 1

                tof2_hit = (tof2_hhit > 0) and (tof2_vhit >0)

                # TOF1 Checks
                tof1_hhit, tof1_vhit = 0,0
                tof1_hit = False
                for tof1_slab_hit in recon_event.GetTOFEvent().GetTOFEventSlabHit().GetTOF1SlabHitArray():
                    if tof1_slab_hit.GetPlane() == 1:
                        tof1_hhit += 1
                    else:
                        tof1_vhit += 1

                tof1_hit = (tof1_hhit > 0) and (tof1_vhit >0)
                data_ok = tof1_hit and tof2_hit

                print ("      TOF1: H: %i, V: %i  --  TOF2 H: %i, v: %i -- %s "%(tof1_hhit, tof1_vhit,tof2_hhit, tof2_vhit, "OK" if data_ok else "NT"))

                # Skip processing here, if not data is collected.
                if not data_ok:
                    continue

                print "    event", j   

                anayzed_triggers += 1

                # =================================================================================================
                # Check Cluster Finding Sanity:
                # =================================================================================================
                
                # Count number of entries in each spill: 
                cluster_singles, cluster_doubles = [0]*30, [0]*30
                for cluster in recon_event.GetSciFiEvent().clusters():
                    plane_id = 15*cluster.get_tracker() + 3*(cluster.get_station()-1) + cluster.get_plane()
                    if  cluster.get_digits().GetEntries() == 1:
                        cluster_singles[plane_id] += 1
                    else:
                        cluster_doubles[plane_id] += 1
                # After counting, fill:
                for plane_id in range(30):
                    clusters_single_hist.Fill(plane_id, cluster_singles[plane_id])
                    clusters_double_hist.Fill(plane_id, cluster_doubles[plane_id])
                
        
                # =================================================================================================
                # Spacepoint Finding Sanity:
                # =================================================================================================
                duplets, triplets = [0]*10, [0]*10

                for spacepoint in recon_event.GetSciFiEvent().spacepoints():
                    station_id = 5*spacepoint.get_tracker() + spacepoint.get_station()-1
                    #print spacepoint.get_type()
                    if spacepoint.get_type() == "triplet":
                        triplets[station_id] += 1
                        print "T"
                    else:
                        duplets[station_id] += 1
                
                #print ([duplets, triplets])
                for station_id in range(10):
                    sp_duplets_hist.Fill(station_id, duplets[station_id])
                    sp_triplet_hist.Fill(station_id, triplets[station_id])

            
                #print "    event", j
                # if j != 6:
                #    continue
                sci_fi_event = recon_event.GetSciFiEvent()
                x_list, y_list, z_list = [], [], []
                for space_point in sci_fi_event.spacepoints():
                    if space_point.get_tracker() == 0:
                        n_clusters_tku_hist.Fill(space_point.get_station(), space_point.get_channels_pointers().size())
                    if space_point.get_tracker() == 1:
                        n_clusters_tkd_hist.Fill(space_point.get_station(), space_point.get_channels_pointers().size())
                        x_list.append(space_point.get_position().x())
                        y_list.append(space_point.get_position().y())
                        z_list.append(space_point.get_position().z())
                if len(x_list) != 5 or len(y_list) != 5:
                    #print "Skipped"
                    continue
                for space_point in sci_fi_event.spacepoints():
                    if space_point.get_tracker() == 1:
                        n_clusters_tkd_good_hist.Fill(space_point.get_station(),
                                                  space_point.get_channels_pointers().size())

    print "Analysed %i triggers"%anayzed_triggers

    n_clusters_tku_canvas = xboa.common.make_root_canvas("n_clusters_tku")
    n_clusters_tku_canvas.cd()
    n_clusters_tku_hist.Draw("COLZ")
    n_clusters_tku_canvas.Update()
    n_clusters_tku_canvas.Print("n_clusters_tku.png")

                
    n_clusters_tkd_canvas = xboa.common.make_root_canvas("n_clusters")
    n_clusters_tkd_canvas.cd()
    n_clusters_tkd_hist.Draw("COLZ")
    n_clusters_tkd_canvas.Update()
    n_clusters_tkd_canvas.Print("n_clusters_tkd.png")
    n_clusters_tkd_good_canvas = xboa.common.make_root_canvas("n_clusters_5point")
    n_clusters_tkd_good_canvas.cd()
    n_clusters_tkd_good_hist.Draw("COLZ")
    n_clusters_tkd_good_canvas.Update()
    n_clusters_tkd_good_canvas.Print("n_clusters_5point_tkd.png")


    peds_both_canvas = xboa.common.make_root_canvas("peds_both_canvas")
    peds_both_canvas.cd()
    peds_both_hist.Draw("COL")
    peds_both_canvas.Print("peds.png")

    ROOT.gStyle.SetPaintTextFormat("1.2f")

    clusters_single_canvas = xboa.common.make_root_canvas("clusters_single_canvas")
    clusters_single_canvas.cd()
    clusters_single_hist.Scale(1.0/anayzed_triggers)
    clusters_single_hist.Draw("COLZ TEXT90")
    clusters_single_canvas.Print("cluster_single.png")

    clusters_double_canvas = xboa.common.make_root_canvas("clusters_double_canvas")
    clusters_double_canvas.cd()
    clusters_double_hist.Scale(1.0/anayzed_triggers)
    clusters_double_hist.Draw("COLZ TEXT90")
    clusters_double_canvas.Print("cluster_double.png")

    duplets_canvas = xboa.common.make_root_canvas("duplets_canvas")
    duplets_canvas.cd()
    sp_duplets_hist.Scale(1.0/anayzed_triggers)
    sp_duplets_hist.Draw("COLZ TEXT")
    duplets_canvas.Print("duplet_spacepoints.png")
    
    triplets_canvas = xboa.common.make_root_canvas("triplets_canvas")
    triplets_canvas.cd()
    sp_triplet_hist.Scale(1.0/anayzed_triggers)
    sp_triplet_hist.Draw("COLZ TEXT")
    triplets_canvas.Print("triplet_spacepints.png")

    

    raw_input()

if __name__ == "__main__":
    main()

