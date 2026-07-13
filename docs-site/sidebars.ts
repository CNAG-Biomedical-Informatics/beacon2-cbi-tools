import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  docsSidebar: [
    'overview',
    {
      type: 'category',
      label: 'Get Started',
      items: [
        'getting-started/installation',
        {
          type: 'category',
          label: 'Installation Paths',
          items: [
            'getting-started/docker',
            'getting-started/apptainer',
            'getting-started/from-source',
          ],
        },
        'getting-started/annotation-data',
        'getting-started/quick-start',
      ],
    },
    {
      type: 'category',
      label: 'Beaconize Data',
      items: [
        {
          type: 'doc',
          id: 'workflows/data-beaconization',
          label: 'End-to-End Tutorial',
        },
        {
          type: 'doc',
          id: 'examples/hg38',
          label: 'GRCh38 / hg38 Example',
        },
        {
          type: 'link',
          label: 'GRCh37 / hs37 Fixtures',
          href: 'https://github.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools/tree/main/testdata',
        },
        {
          type: 'link',
          label: 'CINECA Synthetic Cohort',
          href: 'https://github.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools/tree/main/CINECA_synthetic_cohort_EUROPE_UK1',
        },
        'reference/supported-data',
      ],
    },
    {
      type: 'category',
      label: 'Reference',
      items: [
        'reference/cli',
        'reference/configuration',
        'reference/outputs',
        'reference/mongodb',
        'reference/validation-and-reproducibility',
      ],
    },
    {
      type: 'category',
      label: 'Help',
      items: ['troubleshooting/faq'],
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
