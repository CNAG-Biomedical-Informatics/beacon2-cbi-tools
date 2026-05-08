import clsx from 'clsx';
import Heading from '@theme/Heading';
import Layout from '@theme/Layout';
import Link from '@docusaurus/Link';
import styles from './index.module.css';

const features = [
  {
    title: 'Start With Test Data',
    description:
      'Run the quick start first to validate metadata, convert bundled genomic input, and see expected outputs.',
  },
  {
    title: 'Choose Your Runtime',
    description:
      'Use Docker, Apptainer, or a direct host installation while keeping large reference data outside the runtime.',
  },
  {
    title: 'Move to Real Data',
    description:
      'Use the data beaconization workflow to adapt reference genomes, metadata, genomic conversion, and MongoDB loading.',
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
