import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  docsSidebar: [
    'overview',
    {
      type: 'category',
      label: 'Getting Started',
      items: [
        'getting-started/installation',
        'getting-started/quick-start',
        'getting-started/docker',
        'getting-started/apptainer',
        'getting-started/non-containerized',
      ],
    },
    {
      type: 'category',
      label: 'Workflows',
      items: [
        'workflows/data-beaconization',
      ],
    },
    {
      type: 'category',
      label: 'Examples',
      items: [
        'examples/hg38',
        {
          type: 'link',
          label: 'GRCh37 / hg19',
          href: 'https://github.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools/tree/main/testdata',
        },
        {
          type: 'link',
          label: 'CINECA cohort',
          href: 'https://github.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools/tree/main/CINECA_synthetic_cohort_EUROPE_UK1',
        },
      ],
    },
    {
      type: 'category',
      label: 'Reference',
      items: [
        'reference/cli',
        'reference/configuration',
        'reference/utilities',
      ],
    },
    {
      type: 'category',
      label: 'Troubleshooting',
      items: [
        'troubleshooting/faq',
      ],
    },
    {
      type: 'category',
      label: 'About',
      items: [
        'about/project',
        'about/citation',
        'about/disclaimer',
      ],
    },
  ],
};

export default sidebars;
