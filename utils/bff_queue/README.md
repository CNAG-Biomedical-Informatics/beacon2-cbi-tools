# bff-queue

`bff-queue` helps run many `bff-tools` jobs on a workstation or small server. It is useful when you want something more structured than a shell loop, but do not have an HPC scheduler.

It is built on [Minion](https://metacpan.org/dist/Minion) and commonly uses SQLite as the backend.

## When to use it

- you have many VCF or TSV files to process
- you want a simple local job queue
- you want a small web UI to inspect job state

If a plain shell solution is enough, GNU `parallel` is often the simplest option:

```bash
parallel "bin/bff-tools vcf -t 1 -i chr{}.vcf.gz > chr{}.log 2>&1" ::: {1..22} X Y
```

## Install

```bash
cpanm Minion Minion::Backend::SQLite
```

## Run

Start a worker:

```bash
cd utils/bff_queue
./bff-queue minion worker -j 8 -q beacon
```

Start the UI in another terminal:

```bash
./minion_ui.pl daemon
```

The UI is then available at <http://localhost:3000>.

For production deployment:

```bash
hypnotoad minion_ui.pl
```

## Submit a job

Go to the directory with your input files and submit a command to the queue:

```bash
/usr/share/beacon2-ri/beacon2-cbi-tools/utils/bff_queue/bff-queue minion job -q beacon -e beacon_task -a '["cd /home/mrueda/beacon ; /usr/share/beacon2-ri/beacon2-cbi-tools/bin/bff-tools vcf -i test_1000G.vcf.gz -p param.yaml -t 1 > beacon.log 2>&1"]'
```

Update the paths in that example for your own installation.

## Troubleshooting

If the local queue database gets into a bad state, remove `minion.db` from `utils/bff_queue` and start again.
