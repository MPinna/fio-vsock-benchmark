import psutil
import libvirt

QEMU_USERNAME = 'qemu'
NUM_OF_CORES = psutil.cpu_count()

def get_core_sibling(core_id: int) -> int:
    return (core_id + NUM_OF_CORES//2) % NUM_OF_CORES

def get_qemu_threads() -> list[int]:

    qemu_threads = []

    for proc in psutil.process_iter(['pid', 'name', 'username']):
        try:
            username = proc.username()

            if username == QEMU_USERNAME:
                threads = proc.threads()

                for thread in threads:
                    qemu_threads.append(thread.id)
        except psutil.NoSuchProcess:
            continue

    return qemu_threads

def get_qemu_vhost_threads() -> list[int]:

    qemu_vhost_threads = []
    qemu_threads = get_qemu_threads()

    for q_thread in qemu_threads:
        q_thread_process = psutil.Process(pid=q_thread)
        if "vhost" in  q_thread_process.name():
            qemu_vhost_threads.append(q_thread)

    return qemu_vhost_threads

def get_qemu_vcpu_threads() -> list[int]:

    qemu_vcpu_threads = []
    qemu_threads = get_qemu_threads()

    for q_thread in qemu_threads:
        q_thread_process = psutil.Process(pid=q_thread)
        if "CPU" in  q_thread_process.name():
            qemu_vcpu_threads.append(q_thread)

    return qemu_vcpu_threads

def pin_domain_vcpu(domain: libvirt.virDomain, vCPU_index: int, affinity_list: list[int]):

    if vCPU_index not in range(len(domain.vcpuPinInfo())):
        # TODO: handle error in a better way
        print("Invalid vCPU index")
        return

    if any([idx >= NUM_OF_CORES or idx < 0 for idx in affinity_list]):
        # TODO: handle error in a better way
        print("Invalid affinity list")
        return
    
    # if affinity_list is empty, pin to all cores
    if len(affinity_list) == 0:
        cpu_mask = tuple([True]*NUM_OF_CORES)
        domain.pinVcpu(vCPU_index, cpu_mask)
        return
    
    cpu_mask = tuple([True if idx in affinity_list else False for idx in range(NUM_OF_CORES)])
    
    domain.pinVcpu(vCPU_index, cpu_mask)