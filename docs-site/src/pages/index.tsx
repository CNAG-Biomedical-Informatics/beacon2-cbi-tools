import Link from '@docusaurus/Link';
import useBaseUrl from '@docusaurus/useBaseUrl';
import Layout from '@theme/Layout';
import styles from './index.module.css';

const guideLinks = [
  {
    label: 'Get started',
    title: 'Install and run',
    text: 'Choose Docker, Apptainer, or a source installation and produce your first BFF collections.',
    to: '/docs/getting-started/quick-start',
  },
  {
    label: 'Workflow',
    title: 'Beaconize a dataset',
    text: 'Take metadata and variants through validation, annotation, conversion, and review.',
    to: '/docs/workflows/data-beaconization',
  },
  {
    label: 'Annotation',
    title: 'Prepare reference data',
    text: 'Configure the FASTA, SnpEff, dbNSFP, ClinVar, and COSMIC resources used for raw input.',
    to: '/docs/getting-started/annotation-data',
  },
  {
    label: 'Quality control',
    title: 'Establish trust',
    text: 'Review schema guarantees, biological limits, provenance, and release acceptance checks.',
    to: '/docs/reference/validation-and-reproducibility',
  },
];

export default function Home() {
  const browserVisual = useBaseUrl('/img/bff-variant-detail-inspector.png');

  return (
    <Layout
      title="Beacon v2 CBI Tools"
      description="Validate and convert metadata and genomic files to Beacon v2 Beacon Friendly Format">
      <main className={styles.page}>
        <section className={styles.hero}>
          <div className={styles.heroInner}>
            <div className={styles.copy}>
              <p className={styles.kicker}>CNAG Biomedical Informatics</p>
              <h1>Beacon v2 CBI Tools</h1>
              <p className={styles.value}>Turn metadata and genomic files into Beacon Friendly Format.</p>
              <p className={styles.lede}>
                Use the <code>bff-tools</code> CLI to validate Beacon metadata,
                annotate and convert VCF or SNP-array input, and inspect portable
                BFF collections before connecting them to a Beacon implementation.
              </p>
              <div className={styles.actions}>
                <Link className="button button--primary button--lg" to="/docs/getting-started/quick-start">
                  Quick start
                </Link>
                <Link className="button button--secondary button--lg" to="/docs/workflows/data-beaconization">
                  Tutorial
                </Link>
              </div>
            </div>

            <div className={styles.runPreview} aria-label="Example optional beaconization parameter file">
              <div className={styles.previewTitle}>Optional run profile</div>
              <pre><code><span>genome:</span> hg38{`\n`}<span>datasetid:</span> cohort-1{`\n`}<span>projectdir:</span> cohort-bff{`\n`}<span>annotate:</span> true{`\n`}<span>bff2html:</span> true</code></pre>
              <div className={styles.statuses}>
                <div><span>Metadata</span><strong>validated</strong></div>
                <div><span>Variants</span><strong>annotated</strong></div>
                <div><span>Output</span><strong>BFF ready</strong></div>
              </div>
            </div>
          </div>
        </section>

        <section className={styles.output} aria-label="BFF output review">
          <div className={styles.outputInner}>
            <div className={styles.outputHeading}>
              <div>
                <span>Standalone review</span>
                <h2>Inspect the generated genomic variations</h2>
              </div>
              <Link to="/docs/examples/hg38">Run the GRCh38 example</Link>
            </div>
            <img
              className={styles.outputImage}
              src={browserVisual}
              alt="BFF Tools Browser showing an annotated CINECA variant with colored clinical, molecular-effect, type, and filter labels"
            />
            <div className={styles.mobileFlow}>
              <div><span>Input</span><strong>XLSX, JSON, VCF, or SNP-array data</strong></div>
              <div><span>Process</span><strong>Validate, annotate, and convert</strong></div>
              <div><span>Output</span><strong>Portable BFF collections and report</strong></div>
            </div>
            <p>Generated from the annotated CINECA chr22 parity data included with the repository.</p>
          </div>
        </section>

        <section className={styles.sections} aria-label="Documentation sections">
          <div className={styles.grid}>
            {guideLinks.map((guide) => (
              <Link className={styles.card} to={guide.to} key={guide.title}>
                <span>{guide.label}</span>
                <h2>{guide.title}</h2>
                <p>{guide.text}</p>
              </Link>
            ))}
          </div>
        </section>
      </main>
    </Layout>
  );
}
