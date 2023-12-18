import os
import json
from statistics import mean
from collections import defaultdict
import matplotlib.pyplot as plt
import numpy as np

mins = defaultdict(list)
maxs = defaultdict(list)
means = defaultdict (list)
stddevs = defaultdict(list)

total_avgs = dict()

# set to the directory that contains the .json output files
RESULTS_DIR = "../results/"

def main():
    p = os
    json_files = [f for f in os.listdir(RESULTS_DIR) if f.endswith(".json")]

    block_sizes = []

    for json_file in json_files:
        filename = RESULTS_DIR + json_file
        with open(filename) as f:
            try:
                json_content = json.load(f)
            except json.JSONDecodeError as e:
                continue
        bs = int(json_content["global options"]["bs"])
        if bs not in block_sizes:
            block_sizes.append(bs)
        j_min = json_content["jobs"][0]["write"]["lat_ns"]["min"]
        j_max = json_content["jobs"][0]["write"]["lat_ns"]["max"]
        j_mean = json_content["jobs"][0]["write"]["lat_ns"]["mean"]
        j_stddev = json_content["jobs"][0]["write"]["lat_ns"]["stddev"]

        mins[bs].append(j_min)
        maxs[bs].append(j_max)
        means[bs].append(j_mean)
        stddevs[bs].append(j_stddev)
    
    block_sizes = sorted(block_sizes)

    for bs in block_sizes:
        print(f"bs = {bs}:")


        print(f"\tmin: {mean(mins[bs])} \n\tmax: {mean(maxs[bs])}\n\tmean: {mean(means[bs])}\n\tstddev: {mean(stddevs[bs])}")

    ### Plotting ###
    bar_width = 0.25    
    fig = plt.figure(figsize=(12, 8))
    
    plt.subplot(2,2,1)
    plt.semilogx(block_sizes, [mean(mins[bs]) for bs in block_sizes], 'o-')
    plt.xlabel('Block size (B)')
    plt.ylabel('Avg min latency (ns)')
    plt.xticks(block_sizes)
    
    

    plt.subplot(2,2,2)
    plt.semilogx(block_sizes, [mean(maxs[bs]) for bs in block_sizes], 'o-')
    plt.xlabel('Block size (B)')
    plt.ylabel('Avg max latency (ns)')
    plt.xticks(block_sizes)

    plt.subplot(2,2,3)
    plt.semilogx(block_sizes, [mean(means[bs]) for bs in block_sizes], 'o-')
    plt.xlabel('Block size (B)')
    plt.ylabel('Avg mean latency (ns)')
    plt.xticks(block_sizes)

    plt.subplot(2,2,4)
    plt.semilogx(block_sizes, [mean(stddevs[bs]) for bs in block_sizes], 'o-')
    plt.xlabel('Block size (B)')
    plt.ylabel('Avg latency stddev (ns)')
    plt.xticks(block_sizes)


    plt.legend()
    plt.show() 

    

if __name__ == "__main__":
    main()