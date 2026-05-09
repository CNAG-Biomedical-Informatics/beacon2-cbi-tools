import Layout from '@theme/Layout';
import Link from '@docusaurus/Link';
import styles from './index.module.css';

const features = [
  {
    title: 'Run Commands',
    description:
      'Use copy-paste recipes for metadata validation, VCF conversion, SNP-array input, MongoDB loading, and inspection.',
    link: '/docs/workflows/recipes',
    cta: 'Open Recipes',
  },
  {
    title: 'Check Supported Data',
    description:
      'Confirm which inputs, outputs, commands, and current limits apply before processing a real cohort.',
    link: '/docs/reference/supported-data',
    cta: 'View Matrix',
  },
  {
    title: 'Review Reproducibility',
    description:
      'Understand what schema validation checks, what it cannot prove, and what to keep for reproducibility.',
    link: '/docs/reference/validation-and-reproducibility',
    cta: 'Read Guidance',
  },
  {
    title: 'Install the Toolkit',
    description:
      'Pick Docker, Apptainer, or a non-containerized install depending on your workstation, server, or HPC environment.',
    link: '/docs/getting-started/installation',
    cta: 'Choose Install Path',
  },
  {
    title: 'Prepare Real Data',
    description:
      'Follow the end-to-end workflow for metadata validation, genomic conversion, and MongoDB loading.',
    link: '/docs/workflows/data-beaconization',
    cta: 'Start Tutorial',
  },
  {
    title: 'Troubleshoot a Run',
    description:
      'Use the FAQ when reference genomes, annotation resources, validation warnings, or MongoDB loading fail.',
    link: '/docs/troubleshooting/faq',
    cta: 'Open FAQ',
  },
];

function HomepageHeader() {
  return (
    <header className={styles.hero}>
      <div className={styles.heroGrid}>
        <div className={styles.copy}>
          <p className={styles.kicker}>Beacon v2 CBI Tools</p>
          <h1>Build Beacon v2-ready datasets from metadata and genomic files.</h1>
          <p className={styles.lede}>
            Validate Beacon metadata, convert VCF or SNP-array input into
            Beacon Friendly Format, and load the resulting collections into
            MongoDB for Beacon deployments.
          </p>
          <div className={styles.actions}>
            <Link className="button button--primary button--lg" to="/docs/workflows/data-beaconization">
              Start Tutorial
            </Link>
            <Link className="button button--primary button--lg" to="/docs/workflows/recipes">
              Command Recipes
            </Link>
            <Link className="button button--secondary button--lg" to="/docs/getting-started/what-should-i-run">
              What should I run?
            </Link>
          </div>
        </div>

        <div className={styles.flow} aria-label="Beacon v2 CBI Tools workflow">
          <div>
            <span>Input</span>
            <strong>XLSX metadata</strong>
            <strong>BFF JSON</strong>
            <strong>VCF / SNP-array TSV</strong>
          </div>
          <div>
            <span>Run</span>
            <strong>validate</strong>
            <strong>vcf / tsv</strong>
            <strong>load / full</strong>
          </div>
          <div>
            <span>Output</span>
            <strong>BFF collections</strong>
            <strong>genomicVariations</strong>
            <strong>MongoDB / browser files</strong>
          </div>
        </div>
      </div>
    </header>
  );
}

function FeatureCards() {
  return (
    <section className={styles.features}>
      <div className={styles.cardGrid}>
        {features.map((feature) => (
          <Link className={styles.card} to={feature.link} key={feature.title}>
            <span>{feature.cta}</span>
            <h2>{feature.title}</h2>
            <p>{feature.description}</p>
          </Link>
        ))}
      </div>
    </section>
  );
}

export default function Home() {
  return (
    <Layout
      title="Beacon v2 CBI Tools"
      description="Documentation for Beacon v2 CBI Tools"
    >
      <main className={styles.page}>
        <HomepageHeader />
        <FeatureCards />
      </main>
    </Layout>
  );
}
