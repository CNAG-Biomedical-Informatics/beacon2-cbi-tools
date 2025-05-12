# NAME

`bff-tools`: A unified command-line toolkit for working with Beacon v2 Models data. It allows users to **annotate** and **convert** VCF/TSV files into the `genomicVariations` entity using the Beacon-Friendly Format (BFF), **validate** metadata files (XLSX or JSON) against Beacon v2 schema definitions and **load** BFF-formatted data into a **MongoDB** instance.

This tool is part of the `beacon2-cbi-tools` repository and is designed to support Beacon v2 data ingestion pipelines, metadata validation workflows, and federated data sharing initiatives.

# SYNOPSIS

bff-tools &lt;mode> \[-arguments\] \[-options\]

    Mode:
    * vcf
         -i | --input <file.vcf>        Requires a VCF.gz file (gz or not gz)
                                        (May also use a parameters file)

    * tsv
         -i | --input <file.tsv>        Requires a SNP microarray TSV filea (e.g., from 23andme) 
                                        (May also use a parameters file)

    * load
                                        (Requires a parameters file specifying BFF files)

    * full (vcf + load)
               or
           (tsv + load)
         -i | --input <file>            Requires a VCF or TSV file
                                        (May also use a parameters file)

       Options [vcf|tsv|load|full]
         -c | --config <file>           Requires a configuration file
         -p | --param <file>            Requires a parameters file (optional)
         -projectdir-override <path>    Custom project directory path (overrides config)
         -t | --threads <number>        Number of threads (optional, mainly for VCF)

    * validate
       Options [validate]
         -i | --input <file(s)>         One or more XLSX/JSON metadata files
         -s | --schema-dir <directory>  Directory containing JSON schemas
         -o | --out-dir <directory>     Output directory for validated data
         -gv                            Set this option if you want to process <genomicVariations> entity
         -ignore-validation             Writes JSON collection regardless of results from validation against JSON schemas (AYOR!)

        Experimental:
         -gv-vcf                        Set this option to read <genomicVariations.json> from <beacon vcf> (with one document per line)


       Generic Options:
         -h                             Brief help message
         -man                           Full documentation
         -v                             Display version information
         -debug <level>                 Print debugging information (1 to 5)
         -verbose                       Enable verbosity
         -nc | --no-color               Do not print colors to STDOUT
         -ne | --no-emoji               Do not print emojis to STDOUT

# DESCRIPTION

### `bff-tools`

`bff-tools` is a command-line toolkit with five operational modes for working with Beacon v2 data:

# HOW TO RUN `bff-tools`

This script supports four **modes**: `vcf`, `tsv`, `load`, `full`, and `validate`.

**\* Mode `vcf`**

Annotates a gzipped (or uncompressed) VCF file and serializes it into the Beacon-Friendly Format (BFF) as `genomicVariationsVcf.json.gz`.

**\* Mode `tsv`**

Annotates a gzipped (or uncompressed) SNP microarray text file and serializes it into the Beacon-Friendly Format (BFF) as `genomicVariationsVcf.json.gz`.

**\* Mode `load`**

Loads BFF-formatted JSON files - including metadata and genomic variations - into a MongoDB instance.

**\* Mode `full`**

Combines `vcf` and `load`: it processes a VCF file and ingests the resulting data into MongoDB.

**\* Mode `validate`**

Validates metadata files (XLSX or JSON) against the Beacon v2 schema definitions and serializes them into BFF JSON collections.  
Note: This mode uses a separate internal script and does not require a parameters or configuration file.

To perform these tasks, you may need:

- A VCF file or a TSV file for modes: `vcf` and `full`.
- A parameters file (optional)

    YAML file with job-specific values and metadata file references. Recommended for structured processing.

- BFF JSON files (required for modes: `load` and `full`)

    See [Beacon-Friendly Format (BFF)](#what-is-the-beacon-friendly-format-bff) for a detailed explanation.

- Metadata files (XLSX or JSON) (for mode: `validate`)

    You can start with the provided Excel template and use `--gv` or `--ignore-validation` flags if needed.

- Threads (only for `vcf`, `tsv` and `full` modes)

    You can set the number of threads using `-t`. However, since SnpEff doesn't parallelize efficiently, it's best to use `-t 1` and distribute the work (e.g., by chromosome) using GNU `parallel` or the included [queue system](https://github.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools/tree/main/utils/bff_queue)).

`bff-tools` will create an independent project directory `projectdir` and store all needed information needed there. Thus, many concurrent calculations are supported.
Note that `bff-tools` will treat your data as _read-only_ (i.e., will not modify your original files).

**Annex: Parameters file** (YAML)

Example for `vcf` mode:

    --
    genome: hs37 # default hg19
    annotate: true # default true
    bff2html: true # default false

Example for `tsv` mode:

    --
    genome: b37 # default hg19
    annotate: true # default true
    bff2html: true # default false

Example for `load` mode:

    --
    bff:
      metadatadir: .
      analyses: analyses.json
      biosamples: biosamples.json
      cohorts: cohorts.json
      datasets: datasets.json
      individuals: individuals.json
      runs: runs.json
      # Note that genomicVariationsVcf is not affected by <metadatadir>
      genomicVariationsVcf: beacon_XXXX/vcf/genomicVariationsVcf.json.gz
    projectdir: my_project

Example for `full` mode:

    --
    genome: hs37 # default hg19
    annotate: true # default true
    bff:
      metadatadir: .
      analyses: analyses.json
      runs: runs.json
    projectdir: my_project

Please find below a detailed description of all parameters (alphabetical order):

- **annotate**

    When the **annotate** parameters is set to `true` (default), the tool will perform annotation on the provided VCF file. This process involves running snpEff to enrich the VCF with annotation data by leveraging databases such as dbNFSP, ClinVar, and COSMIC. In this mode, the tool will generate and populate the ANN fields based on the analysis.

    If the **annotate** parameters is set to `false`, the tool assumes that the VCF file has already been annotated (i.e., it already contains the ANN fields). In this case, it will skip the annotation step and directly parse the existing ANN fields. If you choose this route, please make sure to modify the file `lib/internal/complete/config.yaml` consisting of database versions with your own values.

    One way to use `annotate: false` is to perform `bff2html` without having to re-annotate the VCF with SnpEff.

- **bff**

    Location for the Beacon Friendly Format JSON files.

- **bff2html**

    Set bff2html to `true` to create HTML for the BFF Genomic Variations Browser.

- **center**

    Experimental feature. Not used for now.

- **datasetid**

    An unique identifier for the dataset present in the input VCF. Default value is 'id\_1'

- **genome**

    Your reference genome.

    Accepted values: hg19, hg38, hs37, and b37 (b37 will be interpreted as hs37).

    If you used GATKs GRCh37 set it to hg19.

    Not supported: NCBI36/hg18, NCBI35/hg17, NCBI34/hg16, hg15 and older.

- **organism**

    Experimental feature. Not used for now.

- **projectdir**

    The prefix for dir name (e.g., 'cancer\_sample\_001'). Note that it can also contain a path (e.g., /workdir/cancer\_sample\_001).
    The script will automatically add an unique identifier to each job.

- **technology**

    Experimental feature. Not used for now.

**Examples:**

    $ bin/bff-tools vcf -i input.vcf.gz 

    $ bin/bff-tools vcf -i input.vcf.gz -p param.yaml -projectdir-override beacon_exome_id_123456789

    $ bin/bff-tools load -p param_file  # MongoDB load only

    $ bin/bff-tools full -t 1 --i input.vcf.gz -p param_file  > log 2>&1

    $ bin/bff-tools full -t 1 --i input.vcf.gz -p param_file -c config_file > log 2>&1

    $ bin/bff-tools validate -i my_data.xlsx -o outdir

    $ nohup $path_to_beacon/bin/bff-tools full -i input.vcf.gz -verbose

    $ parallel "bin/bff-tools vcf -t 1 -i chr{}.vcf.gz  > chr{}.log 2>&1" ::: {1..22} X Y

_NB_: If you don't want colors in the output use the flag `--no-color`. If you did not use the flag and want to get rid off the colors in your printed log file use this command to parse ANSI colors:

    perl -pe 's/\x1b\[[0-9;]*[mG]//g'

**Note:** The script creates `log` files for all the processes. For instance, when running in `vcf` mode you can check via `tail -f` command:

    $ tail -f <your_job_id/vcf/run_vcf2bff.log

## WHAT IS THE BEACON FRIENDLY FORMAT (BFF)

The Beacon Friendly Format is a data exchange format consisting up to  7 JSON files (JSON arrays) that match the 7 schemas from [Beacon v2 Models](https://docs.genomebeacons.org/schemas-md/analyses_defaultSchema/).

Six files correspond to Metadata (`analyses.json,biosamples.json,cohorts.json,datasets.json,individuals.json,runs.json`) and one corresponds to variations (`genomicVariations.json`).

Normally, `bff-tools` script is used to create `genomicVariations` JSON file. The other 6 files are created with [this utility](https://github.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools/tree/main/utils/bff_validator) (part of the distribution). See instructions [here](https://github.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools/tree/main/utils/bff_validator/README.md).

Once we have all seven files, then we can proceed to load the data into MongoDB.

# COMMON ERRORS: SYMPTOMS AND TREATMENT

    * Perl: 
            * Execution errors:
              - Error with YAML::XS
                Solution: Make sure the YAML (config.yaml or parameters file) is well formatted (e.g., space after param:' ').

    * Bash: 
            (Possible errors that can happen when the embeded Bash scripts are executed)
            * bcftools errors: bcftools is nit-picky about VCF fields and nomenclature of contigs/chromosomes in reference genome
                   => Failed to execute: beacon_161855926405757/run_vcf2bff.sh
                      Please check this file beacon_161855926405757/run_vcf2bff.log
              - Error: 
                     # Running bcftools
                     [E::faidx_adjust_position] The sequence "22" was not found
                Solution: Make sure you have set the correct genome (e.g., hg19, hg38 or hs37) in parameters_file.
                          In this case bcftools was expecting to find 22 in the <*.fa.gz> file from reference genome, but found 'chr22' instead.
                    Tips:
                         - hg{19,38} use 'chr' in chromosome naming (e.g., chr1)
                         - hs37 does not use 'chr' in chromosome naming (e.g., 1)
          
               - Error
                    # Running bcftools
                    INFO field IDREP only contains 1 field, expecting 2
                 Solution: Please Fix VCF info field manually (or get rid of problematic fields with bcftools)
                           e.g., bcftools annotate -x INFO/IDREP input.vcf.gz | gzip > output.vcf.gz
                                 bcftools annotate -x INFO/MLEAC,INFO/MLEAF,FMT/AD,FMT/PL input.vcf.gz  | gzip > output.vcf.gz
               
                     
      NB: The bash scripts can be executed "manually" in the beacon_XXX dir. You must provide the 
          input vcf as an argument. This is a good option for debugging. 

## KNOWN ISSUES

    * Some Linux distributions do not include perldoc and thus Perl's library Pod::Usage will complain.
      Please, install it (sudo apt install perl-doc) if needed.

# CITATION

The author requests that any published work that utilizes **B2RI** includes a cite to the the following reference:

Rueda, M, Ariosa R. "Beacon v2 Reference Implementation: a toolkit to enable federated sharing of genomic and phenotypic data". _Bioinformatics_, btac568, https://doi.org/10.1093/bioinformatics/btac568

# AUTHOR

Written by Manuel Rueda, PhD. Info about CNAG can be found at [https://www.cnag.eu](https://www.cnag.eu)

Credits: 

    * Sabela De La Torre (SDLT) created a Bash script for Beacon v1 to parse vcf files L<https://github.com/ga4gh-beacon/beacon-elixir>.
    * Toshiaki Katayamai re-implemented the Beacon v1 script in Ruby.
    * Later Dietmar Fernandez-Orth (DFO) modified the Ruby for Beacon v2 L<https://github.com/ktym/vcftobeacon and added post-processing with R, from which I borrowed ideas to implement vcf2bff.pl.
    * DFO for usability suggestions and for creating bcftools/snpEff commands.
    * Roberto Ariosa for help with MongoDB implementation.
    * Mauricio Moldes helped with the containerization.

# COPYRIGHT and LICENSE

This PERL file is copyrighted. See the LICENSE file included in this distribution.
