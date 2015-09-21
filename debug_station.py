#!/usr/bin/env python

"""
Study a single station to understand what is happening to that
"""

import os
import subprocess

# basic PyROOT definitions
import ROOT 
import xboa.common

# definitions of MAUS data structure for PyROOT
import libMausCpp #pylint: disable = W0611
import itertools

import StationStudy


def main():

    print "Generating some data"
    #my_file_name = "/home/ed/MICE/testdata/maus_7333.root"
    my_file_name = "/home/ed/MICE/testdata/maus_output_new-mapping-calibration_run7333.root"

    output_dir = 

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
        if i > 5000:
            break
            
        print "Spill", i
        
        tree.GetEntry(i)
        spill = data.GetSpill()

        if spill.GetDaqEventType() == "physics_event":

            for j, recon_event in enumerate(spill.GetReconEvents()):
                
                for station in stations:
                    station.FillRecon(recon_event)
    
    for station in stations:
        station.MakeDrawCanvas()
        station.MakeResultsDict()
 
    raw_input("Done, press enter to exit")

if __name__=="__main__":
        main()
