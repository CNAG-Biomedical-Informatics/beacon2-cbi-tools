# Frequently Asked Questions

## Installation

??? faq "I am getting a SnpEff error inside the Docker container"

    If you see an error like this:

    ```text
    ERROR while connecting to https://snpeff.blob.core.windows.net/databases/v5_0/snpEff_v5_0_hg19.zip
    java.lang.RuntimeException: java.net.UnknownHostException: snpeff.blob.core.windows.net
    ```

    first make sure you completed all installation steps, including the external data download and the `snpEff.config` update.

    See:

    - [Docker installation](../download-and-installation/docker-based.md)
    - [Apptainer installation](../download-and-installation/apptainer-based.md)
    - [Non-containerized installation](../download-and-installation/non-containerized.md)

## Coordinates and Input Data

??? faq "Are Beacon v2 `genomicVariations.variation.location.interval.{start,end}` coordinates 0-based or 1-based?"

    They are [0-based](http://docs.genomebeacons.org/formats-standards/#genome-coordinates).

??? faq "I have an error when attempting to use `bff-tools vcf`. What should I check first?"

    In most cases, the issue is one of these:

    - the reference genome in your parameter file does not match the contigs in the VCF
    - the VCF has malformed headers or INFO fields
    - the required external data or annotation setup is incomplete

    Common genome values are `hg19`, `hg38`, `hs37`, and `b37`. Make sure the VCF contigs match the FASTA and annotation resources used by your installation.

    If the VCF has problematic INFO fields, one possible workaround is:

    ```bash
    bcftools annotate -x INFO/IDREP input.vcf.gz | gzip > output.vcf.gz
    ```

??? faq "Can I use single-sample and multi-sample VCFs?"

    Yes. Both are supported.

    MongoDB loading is incremental, so you do not need to merge all samples into a single multi-sample VCF before ingestion.

??? faq "Can I use gVCF files?"

    Not directly. First convert the gVCF to a standard VCF containing variant positions with ALT alleles.

    Example:

    ```bash
    bcftools convert --gvcf2vcf --fasta ref.fa input.g.vcf
    ```

??? faq "Can I use SNP microarray data such as 23andMe exports?"

    Yes. Use `bff-tools tsv` with SNP-array style TSV or TXT input.

    Example:

    ```bash
    bin/bff-tools tsv -i testdata/tsv/input.txt.gz -p testdata/tsv/param.yaml
    ```

    If `bff2html: true` is enabled in the parameter file, the output can also be prepared for later browsing in `bff-browser`.

??? faq "Why does `bff-tools vcf` re-annotate VCFs? Can I use my own annotations?"

    The default workflow re-annotates VCFs to ensure a consistent set of annotation fields for downstream BFF generation.

    If your input VCF already contains the required annotation fields, you can disable annotation with:

    ```yaml
    annotate: false
    ```

    This should only be done if you understand the expected annotation content and your input already matches it.

    If you want to add complementary genomic information outside the VCF workflow, you can also provide `genomicVariations` metadata through the workbook or JSON validation path.

## Metadata and Validation

??? faq "Is there an alternative to the Excel file for metadata or phenotypic data?"

    Yes. You can validate JSON collections directly with `bff-tools validate`, and the standalone `bff-validator` utility can also be used on its own.

    If your source data lives in other models such as REDCap, OMOP CDM, Phenopackets v2, or CSV exports, you may also want to look at [Convert-Pheno](https://github.com/CNAG-Biomedical-Informatics/convert-pheno).

??? faq "What should I do about validation warnings such as `oneOf` mismatches?"

    `bff-tools validate` uses the Beacon schemas bundled with your installed toolkit version.

    Some warnings can reflect ambiguity in the current schema definitions rather than a real data problem. If needed, use:

    ```bash
    --ignore-validation
    ```

    for debugging, inspect the generated JSON output, and then decide whether the warning reflects a real issue in the source metadata.

## Ingestion and Performance

??? faq "Do you load all variants present in the VCF?"

    Yes. The loader does not discard variants based on fields such as `FILTER` or `QUAL`. Those values are preserved in the generated data and can still be used later.

??? faq "How can I speed up data ingestion?"

    Metadata ingestion is usually fast. VCF processing is the step that most often becomes expensive.

    Useful strategies include:

    - split large VCFs by chromosome or region
    - run multiple jobs in parallel
    - use `bff-queue` or other batching approaches on workstations

    Example:

    ```bash
    bcftools view input.vcf.gz --regions chr1
    ```

??? faq "Can I use parallel jobs when loading into MongoDB?"

    Yes, but heavy parallel loading may reduce performance slightly depending on your MongoDB setup and storage performance.

??? faq "When performing incremental uploads, do I need to rebuild indexes?"

    No. Indexes are created on the first load and are updated automatically as new data is inserted.

    Re-running the indexing step does not create duplicate indexes. In that sense, the operation is idempotent.

## Data Access and Licensing

??? faq "Where do I get the full WGS VCF for the CINECA synthetic cohort EUROPE UK1?"

    The full WGS data is available through the [EGA dataset page](https://ega-archive.org/datasets/EGAD00001006673). For project-specific context, see the CINECA synthetic cohort materials in this repository.

??? faq "Is `beacon2-cbi-tools` free and open source?"

    Yes.

    The toolkit is released under the GNU GPL v3.0, and the included CINECA synthetic dataset materials are distributed separately under their own terms.

## Project and Usage

??? faq "Should I update to the latest version?"

    In general, yes. Newer versions typically include fixes, schema alignment updates, and documentation improvements.

    Before updating production deployments, review the release notes or test the new version in your own environment first.

??? faq "Do you send any personal information to external servers?"

    No. Files are processed locally by the toolkit itself.

    You are still responsible for how you store, mount, transfer, or back up your own data.

??? faq "How do I cite `beacon2-cbi-tools`?"

    Cite the Beacon v2 Reference Implementation paper:

    !!! note "Citation"
        Rueda, M, Ariosa R. "Beacon v2 Reference Implementation: a toolkit to enable federated sharing of genomic and phenotypic data". _Bioinformatics_, btac568, [DOI](https://doi.org/10.1093/bioinformatics/btac568).
