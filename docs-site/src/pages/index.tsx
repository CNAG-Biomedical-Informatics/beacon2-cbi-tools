import clsx from 'clsx';
import Heading from '@theme/Heading';
import Layout from '@theme/Layout';
import Link from '@docusaurus/Link';
import styles from './index.module.css';

const features = [
  {
    title: 'Run Bundled Test Data',
    description:
      'Run the quick start first to validate metadata, convert bundled genomic input, and see expected outputs.',
    link: '/docs/getting-started/quick-start',
    cta: 'Open Quick Start',
  },
  {
    title: 'Choose the Right Command',
    description:
      'Start from what you already have: XLSX metadata, VCF, TSV, existing BFF files, or MongoDB.',
    link: '/docs/getting-started/what-should-i-run',
    cta: 'Decide What to Run',
  },
  {
    title: 'Understand Outputs',
    description:
      'Learn where logs, BFF JSON collections, browser files, and MongoDB loading outputs are written.',
    link: '/docs/reference/outputs',
    cta: 'View Outputs',
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
    cta: 'Read Workflow',
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
    <header className={clsx('hero hero--primary')}>
      <div className="container">
        <div className="beacon-docs-hero-brand">
          <img className="beacon-docs-hero-logo" src="img/logo.png" alt="Beacon v2 CBI Tools" />
          <Heading as="h1" className="hero__title beacon-docs-hero-title">
            Beacon v2 CBI Tools
          </Heading>
        </div>
        <p className="hero__subtitle">
          Documentation for preparing Beacon v2 deployments with Beacon Friendly Format data.
        </p>
        <div>
          <Link className="button button--primary button--lg" to="/docs/overview">
            Read the Docs
          </Link>
          <Link className="button button--secondary button--lg beacon-hero-secondary" to="/docs/getting-started/what-should-i-run">
            What should I run?
          </Link>
        </div>
      </div>
    </header>
  );
}

function FeatureCards() {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {features.map((feature) => (
            <div className="col col--4" key={feature.title}>
              <article className="beacon-feature-card">
                <Heading as="h3">{feature.title}</Heading>
                <p>{feature.description}</p>
                <Link className="button button--outline button--primary" to={feature.link}>
                  {feature.cta}
                </Link>
              </article>
            </div>
          ))}
        </div>
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
      <HomepageHeader />
      <main>
        <FeatureCards />
      </main>
    </Layout>
  );
}
