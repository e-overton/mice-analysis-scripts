#!/usr/bin/env python

"""
Eds analysis to study the tracker...
"""

# Py-stuff
import os

# PyRoot
import ROOT

# definitions of MAUS data structure for PyROOT
import libMausCpp  # pylint: disable = W0611

# Some modules for this task.
from StationStudy import StationStudy
import FrontEndLookup
from ClusterLightYield import ClusterLightYield
import TOFTools


def main(maus_datafile, lookup=None, output_tfile=None,
         output_plot_path=None):
    """The main "process me" function.

    A function to process the MAUS data and generate plots to be stored in.

    :param maus_data: The MAUS data to process.
    :param lookup: FrontEndLookup object for light yield.
    :param output_tfile: The TFile to write plots into.
    :param output_plots: The Folder to store plots into.
    """

    # Setup ###############################################################

    # Load the MAUS_File:
    if isinstance(maus_datafile, basestring):
        maus_datafile = [maus_datafile]

    print "Setting up ROOT TChain"
    chain = ROOT.TChain("Spill")
    for f in maus_datafile:
        print "Appending file: ", f
        chain.AddFile(f)

    print "Setting up data"
    tree = chain
    data = ROOT.MAUS.Data()  # pylint: disable = E1101
    tree.SetBranchAddress("data", data)

    # Setting up output:
    if not (output_tfile is None):
        print "Setting up output file", output_tfile
        out_root_file = ROOT.TFile(output_tfile, "RECREATE")

    # Objects to store data into:
    print "Setting up data objects"
    stations = [StationStudy(0, s)for s in range(1, 6)] +\
               [StationStudy(1, s)for s in range(1, 6)]

    if lookup is None:
        light_yields = []
    else:
        light_yields = [ClusterLightYield(lookup, "US"),
                        ClusterLightYield(lookup, "DS")]

    max_spills = 100000

    # Process MAUS data #####################################################
    print "Beginning Processing"
    for i in range(tree.GetEntries()):

        if i > max_spills:
            break

        print "Spill", i, "/", tree.GetEntries()

        tree.GetEntry(i)
        spill = data.GetSpill()

        # Skip non-physics events:
        if spill.GetDaqEventType() != "physics_event":
            continue

        # Process recon event:
        for j, recon_event in enumerate(spill.GetReconEvents()):

            # Time in spill cuts:
            spill_time = TOFTools.TimeInSpill(spill, j)
            #  if spill_time < 8.5:
            #    continue

            # Fill the station analysis objects
            for station in stations:
                    station.FillRecon(recon_event)

            # Fill the light yield objects
            for tk, ly in enumerate(light_yields):
                for pr in [recon_event.GetSciFiEvent().straightprtracks(),
                           recon_event.GetSciFiEvent().helicalprtracks()]:
                    for track in pr:
                        if tk == track.get_tracker():
                            for sp in track.get_spacepoints():
                                for cluster in sp.get_channels():
                                    ly.FillCluster(cluster)

    # Postprocess the data ##################################################

    # Duplet noise rate per station
    h_du_noise = ROOT.TH1D("dunoise", "dunoise;Station(-ve is upstream);"
                           "Duplet Noise Rate (%)", 11, -5.5, 5.5)

    # Efficiency from stuff.
    h_effic = ROOT.TH1D("efficiency", "efficiency;Station(-ve is upstream);"
                        "Efficiency (%)", 11, -5.5, 5.5)

    for d in [s.MakeResultsDict() for s in stations]:

        # Determine the bin, b to set the contents of.
        if d["tracker"] == 0:
            b = h_du_noise.FindBin(-d["station"])
        else:
            b = h_du_noise.FindBin(d["station"])

        h_du_noise.SetBinContent(b, d["duplet_noise"]*100.0)
        h_effic.SetBinContent(b, d["sp_eff"]*100.0)

    # Generste canvases and store to disk ###################################
    forceDraw = True

    if (output_plot_path is not None) or forceDraw:

        # Station Plots
        for s in stations:
            s.MakeDrawCanvas()
            if output_plot_path is not None:
                filename = "StationPlot_%s_%s.pdf" % (s.trkname, s.station)
                s.c.SaveAs(os.path.join(output_plot_path, filename))

        # Station performance plots
        c_dunoise = ROOT.TCanvas("DupletNoise", "DupletNoise", 800, 600)
        c_dunoise.cd()
        h_du_noise.Draw()
        if output_plot_path is not None:
            c_dunoise.SaveAs(os.path.join(output_plot_path, "DupletNoise.pdf"))

        c_effic = ROOT.TCanvas("Efficiency", "Efficiency", 800, 600)
        c_effic.cd()
        h_effic.Draw()
        h_effic.GetYaxis().SetRangeUser(70, 100)
        if output_plot_path is not None:
            c_effic.SaveAs(os.path.join(output_plot_path, "Efficiency.pdf"))

        # Light Yield Plots
        for ly in light_yields:
            ly.MakeDrawCanvas()
            if output_plot_path is not None:
                filename = "LightYieldPlot_%s.pdf" % ly.name
                ly.c.SaveAs(os.path.join(output_plot_path, filename))

    raw_input("test")

    # Try to store root file:
    try:
        out_root_file.Write()
        out_root_file.Close()
        print "Written root file"
    except NameError:
        pass

    # raw_input ("test2")

if __name__ == "__main__":

    print "Loading Calibration/Mapping lookups"

    # The SciFi calibration
    maus_scifi_calibration = "%s/files/calibration/"\
        "scifi_calibration_2015-06-18.txt" % os.environ.get("MAUS_ROOT_DIR")

    # The SciFi Mapping
    maus_scifi_mapping = "%s/files/cabling/scifi_mapping_2015-06-18.txt"\
        % os.environ.get("MAUS_ROOT_DIR")

    # The SciFi Mapping
    maus_scifi_badch = "%s/files/calibration/"\
        "scifi_bad_channels_2015-06-18.txt" % os.environ.get("MAUS_ROOT_DIR")

    lookup = FrontEndLookup.FrontEndLookup(maus_scifi_mapping,
                                           maus_scifi_calibration,
                                           maus_scifi_badch)
    # lookup = None # comment this line for lightyields.

    filepath = "/home/ed/MICE/testdata/"
    #files = ["7367/7367_recon.root", "7369/7369_recon.root",
    #         "7370/7370_recon.root", "7372/7372_recon.root",
    #         "7373/7373_recon.root", "7375/7375_recon.root",
    #         "7376/7376_recon.root", "7377/7377_recon.root"]
    files = ["07513_recon.root"]
    filespath = [os.path.join(filepath, f) for f in files]

    fname = "07411_recon.root"
    main(os.path.join(filepath, fname), lookup, "out7513.root", "output/7513")
