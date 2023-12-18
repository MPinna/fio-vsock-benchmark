# README
The python script automatically runs batches of fio jobs to test vsock bidirectional latency with different block sizes (`bs` parameter in the .fio job files).

Make sure the version of `fio` that you're using supports vsock (https://github.com/MPinna/fio)

All the .fio job files have to be on the host. The `receiver` fio job is started remotely with by the Python script by using the `--client` option.\
Since there is no way to specify the `bs` when using the `--client` option, one job file per each `bs` was created and that's what is used to start the receiver each time (`./jobs/fioserver_vsock_*.fio`).\
On the other hand, the local instance that stars the `sender` job can use both the jobfile and command-line parameters, so one single generic job file is enough (`./jobs/fioclient_vsock_generic.fio`).





## Usage

1. **Manually** start `fio` in server mode on the guest

```bash
./fio --server=,<listening port>
```

2. Make sure that the following constants are properly set in `fio-vsock-benchmark.py`:
    * DOMAIN_CID
    * DOMAIN_NAME
    * VM_IP
    * FIO_BIN_PATH_LOCAL

3. Launch the script

    ```bash
    ./fio-vsock-benchmark.py <fio_server_listening_port>
    ```

    where `<fio_server_listening_port>` is the port you used in step 1

    Most likely you will have to launch the script with `sudo` as it requires root privileges to handle CPU affinities etc.

    Output files will be saved by default in `./results`.

4. (optional) Run `plot_stats.py` to plot min, max, mean and stddev.