#! /usr/bin/env python3
import os
import sys
import subprocess
from pprint import pprint
from time import sleep
import libvirt
import psutil

from pinning import *

QEMU_CONN_STRING = "qemu:///system"

SSH_PRIV_KEY_PATH = "~/.ssh/id_rsa"

FIO_JOBS_DIR = "./jobs/"
FIO_SENDER_JOB = FIO_JOBS_DIR + "fioclient_vsock_generic.fio"

RUNS_PER_CONFIG = 30

OUTPUT_DIR = "./results/"


# change the following constants accordingly
DOMAIN_CID = 3
DOMAIN_NAME  = "f38-vm-build-v2"
VM_IP = "192.168.124.252"
FIO_BIN_PATH_LOCAL = ""


def launch_fio_receiver_remote(listening_server_port: int, bs: int):
    # TODO: check that jobfile exists
    receiver_jobfile = FIO_JOBS_DIR + f"fioserver_vsock_{bs}.fio"
    subprocess.Popen([f"{FIO_BIN_PATH_LOCAL}", f"--client={VM_IP},{listening_server_port}", f"{receiver_jobfile}"], stdout=subprocess.DEVNULL)

def launch_fio_sender_local(bs: int, output_path: str):
    ret = subprocess.run([f"{FIO_BIN_PATH_LOCAL}", f"--bs={bs}", f"{FIO_SENDER_JOB}", "--output-format=json", f"--output={output_path}"])
    print(f"\tOutput saved to: {output_path}")

def launch_fio_batch(fio_server_port: int, bs: int, n_runs: int = RUNS_PER_CONFIG):
    for run in range(n_runs):
        filename = f"fio_bs{bs}_{run}.json"
        output_path = OUTPUT_DIR + filename

        print(f"Run n. {run+1}/{n_runs}")
        
        print(f"\tStarting receiver on guest with bs={bs}...")
        launch_fio_receiver_remote(fio_server_port, bs)
        
        sleep(1)
        print(f"\tStarting sender on host with bs={bs}...")
        launch_fio_sender_local(bs, output_path)


if __name__ == "__main__":

    if(len(sys.argv) != 2):
        print("Usage: ./fio-vsock-benchmark.py <fio_server_listening_port>")
        exit(1)

    fio_server_port = int(sys.argv[1])

    print("Jobs will be launched using the following parameters:")
    print(f"\tDOMAIN CID = {DOMAIN_CID}")
    print(f"\tDOMAIN NAME = {DOMAIN_NAME}")
    print(f"\tVM IP = {VM_IP}")
    print(f"\tLOCAL FIO BIN PATH = {FIO_BIN_PATH_LOCAL}")
    print()

    user_choice = input("Continue? (y/n)")
    if user_choice.lower() not in ["y", "yes"]:
        print("Aborting...")
        exit(1)

    # connect to QEMU and find domain
    conn = libvirt.open(QEMU_CONN_STRING)
    if not conn:
        raise SystemExit(f"Failed to open connection to {QEMU_CONN_STRING}")
    else:
        print(f"Established connection to {QEMU_CONN_STRING}")
    
    
    dom = None
    for virDomain in conn.listAllDomains():
        if virDomain.name() == DOMAIN_NAME:
            dom = virDomain
            break

    print(f"Domain name: {dom.name()}")
    
    print("Domain vCPU pin info:")
    pprint(dom.vcpuPinInfo())
    num_of_vcpus = len(dom.vcpuPinInfo())


    vhost_threads_pids = get_qemu_vhost_threads()
    vhost_threads = [psutil.Process(pid) for pid in vhost_threads_pids]
    print("vhost threads PIDS:")
    print(vhost_threads_pids)
    num_of_vhost_threads = len(vhost_threads)

    print("Pinning vhost thread(s)...")
    for i, vht in enumerate(vhost_threads):
        print(f"Pinning vhost thread {vhost_threads_pids[i]} to CPU {i}")
        vht.cpu_affinity([i])

    for i in range(num_of_vcpus):
        print(f"Pinning vCPU {i} to CPU {i + num_of_vhost_threads}")
        pin_domain_vcpu(dom, i, [i + num_of_vhost_threads])

    pprint(dom.vcpuPinInfo())


    ### FIO ###

    # create output directory if it doesn't exist
    if not os.path.exists(OUTPUT_DIR):
        print(f"Creating directory {OUTPUT_DIR}")
        os.makedirs(OUTPUT_DIR)

    # block size from 1 to 4096
    block_sizes = [2**i for i in range(13)]

    print("Launching fio batches")
    print(f"Num of runs per config: {RUNS_PER_CONFIG}")
    print(f"Num of configs: {len(block_sizes)}")
    print(f"Estimated duration of each run: {5 + 1 + 1}\n") # 5 seconds per job, 1 second before traffic starts, 1 second to setup receiver
    print(f"Estimated runtime: {RUNS_PER_CONFIG*len(block_sizes)*7} seconds\n\n")
    for bs in block_sizes:    
        launch_fio_batch(fio_server_port, bs, RUNS_PER_CONFIG)
        
    # PINNING CLEANUP
    print("Pinning cleanup")

    # TODO handle num of vhost threads
    print("Resetting affinity list for vhost threads")
    vhost_threads[0].cpu_affinity([])
    for vht in vhost_threads:
        vht.cpu_affinity([])

    print("Resetting affinity list for vCPU threads")

    for i in range(num_of_vcpus):
        pin_domain_vcpu(dom, i, [])

    pprint(dom.vcpuPinInfo())
    exit()