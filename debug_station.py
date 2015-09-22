#!/usr/bin/env python

"""
Study a single station to understand what is happening to that
"""

import os
import subprocess

# basic PyROOT definitions
import ROOT 

# definitions of MAUS data structure for PyROOT
import libMausCpp #pylint: disable = W0611
import itertools

import StationStudy
import FrontEndLookup
import ClusterLightYield
import TOFTools


def main():

    print "Loading Calibration/Mapping lookups"
    
    # The SciFi calibration
    maus_scifi_calibration='%s/files/calibration/scifi_calibration_20150912.txt'\
        % os.environ.get("MAUS_ROOT_DIR")
    
    # The SciFi Mapping
    maus_scifi_mapping='%s/files/cabling/scifi_mapping_2015-06-18.txt'\
        % os.environ.get("MAUS_ROOT_DIR")
    
    lookup = FrontEndLookup.FrontEndLookup(maus_scifi_mapping, maus_scifi_calibration)
    LightYield = ClusterLightYield.ClusterLightYield(lookup)

    print "Generating some data"
    #my_file_name = "/home/ed/MICE/testdata/maus_7333.root"
    my_file_name = "/home/ed/MICE/testdata/maus_output_new-mapping-calibration_run7333.root"

    output_dir = "07333/"

    print "Loading ROOT file", my_file_name
    root_file = ROOT.TFile(my_file_name, "READ") # pylint: disable = E1101
        
    print "Setting up data tree"
    data = ROOT.MAUS.Data() # pylint: disable = E1101
    tree = root_file.Get("Spill")
    tree.SetBranchAddress("data", data)
	
    stations = [StationStudy.StationStudy(0,s)for s in range (1,6)] +\
               [StationStudy.StationStudy(1,s)for s in range (1,6)]
    
    print "Beginning Processing"
    for i in range(tree.GetEntries()):
        if i > 500:
            break
            
        print "Spill", i
        
        tree.GetEntry(i)
        spill = data.GetSpill()

        if spill.GetDaqEventType() == "physics_event":

            for j, recon_event in enumerate(spill.GetReconEvents()):

                spilltime =  TOFTools.TimeInSpill(spill,j)

                #for cluster in recon_event.GetSciFiEvent().clusters():
                #for track in  recon_event.GetSciFiEvent().straightprtracks():
                #    for sp in track.get_spacepoints():
                #        for cluster in sp.get_channels():
                #            LightYield.FillCluster(cluster)
                
                #if spilltime < 9.0:
                for station in stations:
                    station.FillRecon(recon_event)

    print "Beginning PostProcessing & Plotting."
    
    #LightYield.MakeDrawCanvas()
    

    for station in stations:
        station.MakeDrawCanvas()
        print ""
        print station.MakeResultsDict()
        print ""
        
    raw_input("Done, press enter to exit")

if __name__=="__main__":
        main()
