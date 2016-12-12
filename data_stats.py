#/bin/env python

print "Run info generator..."

from cdb import Beamline, CoolingChannel       #  get beamline information for some run
from datetime import datetime
import time
import pprint
import sys

import ROOT

# Start/end dates to collate data over:
start_date = datetime.strptime("2016-12-04", "%Y-%m-%d")
end_date = datetime.strptime("2016-12-07", "%Y-%m-%d")

# Function to help collate infomation later:
def add_key(dict, key, value):
    if not key in dict:
        dict[key] = value
    else:
        dict[key] += value

###############################################################################
# Load CDB elements
###############################################################################
print " Loading Beamline...",
try:
    beamline = Beamline()
except:
    print "  ERROR"
    sys.exit()
else:
    print "  OK"

print " Loading Cooling Channel...",
try:
    channel = CoolingChannel()
except:
    print "  ERROR"
    sys.exit()
else:
    print "  OK"

###############################################################################
# Setup processing
###############################################################################

# CDB spill counter
date0_unix = time.mktime(start_date.timetuple())
date1_unix = time.mktime(end_date.timetuple())
th1d_spills_hr = ROOT.TH1D("th1d_spills_hr", "Spills/hr",
                           int((date1_unix-date0_unix)/900), date0_unix - 450.0,
                           date1_unix + 450.0)

# Tag tally infomation
tag_tally = {}

print "****************************************************"
runs = beamline.get_beamlines_for_dates(start_date, end_date)
for run_number in runs.keys():
    print "Found run: %i"%run_number
    # Generate Dips/hr infomation:
    this_beamline = runs[run_number]
    run_start_time = this_beamline['start_time']
    run_end_time = this_beamline['end_time']
    start_unix = time.mktime(run_start_time.timetuple())
    end_unix = time.mktime(run_end_time.timetuple())

    run_time = float((run_end_time - run_start_time).seconds)
    target_dips = this_beamline['end_pulse']-this_beamline['start_pulse']
    dip_rate = target_dips/run_time
    # Find overlapping runs and bins, then fill the bins with dips
    for xbin in range(1, th1d_spills_hr.GetNbinsX()+1):
        bin_min = th1d_spills_hr.GetBinLowEdge(xbin)
        bin_max = th1d_spills_hr.GetBinLowEdge(xbin+1)

        overlap = min(bin_max, end_unix) - max(bin_min, start_unix)
        if overlap > 0:
            th1d_spills_hr.SetBinContent(xbin, th1d_spills_hr.GetBinContent(xbin) + overlap*dip_rate*4)

    # Collate run infomation if run time is long enough:
    if run_time > 900:
        # Append beamline tag infomation
        tag_id = this_beamline["optics"]
        print "Tag: %s"%tag_id
        if tag_id not in tag_tally:
            tag_tally[tag_id] = {}

        # Sum infomation together
        for k in ['Particle Triggers', 'Requested Triggers', 'ToF0 Triggers',
                  'ToF1 Triggers', 'ToF2 Triggers']:
            add_key(tag_tally[tag_id], k, this_beamline['scalars'][k])
        add_key(tag_tally[tag_id], "target_dips", target_dips)
        add_key(tag_tally[tag_id], "run_time", run_end_time - run_start_time)

        # Log each run assosoiated with a particular tag:
        if "runs" not in tag_tally[tag_id]:
            tag_tally[tag_id]["runs"] = []
        tag_tally[tag_id]["runs"].append(run_number)

    print "****************************************************"

print ""
print "###  Tag summary ########################################"
print "%20s %10s %10s %10s %10s  %s" % ("Tag", "Time(H:M)", "Dips",
                                "P.Trig(k)", "TOF2(k)", "  Runs")

for tag in tag_tally:
    tag_info = tag_tally[tag]
    txt_time = "%3i:%2i" % (tag_info["run_time"].seconds/3600,
                            (tag_info["run_time"].seconds/60) % 60)
    txt_runs = ','.join(map(str, tag_info["runs"]))

    print "%20s %10s %10i %10i %10i %s" % (tag, txt_time, tag_info["target_dips"],
                                    tag_info["Particle Triggers"]/1000,
                                    tag_info["ToF2 Triggers"]/1000,
                                    txt_runs)


    
#pprint.pprint(tag_tally)
th1d_spills_hr.Draw()
th1d_spills_hr.GetXaxis().SetTimeDisplay(1)
th1d_spills_hr.SetFillColor(ROOT.kBlue)
th1d_spills_hr.SetLineColor(ROOT.kBlue)

raw_input("Done")
    
    