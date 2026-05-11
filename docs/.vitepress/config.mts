import markdownItKatex from 'markdown-it-katex';
import { withMermaid } from "vitepress-plugin-mermaid";
import lightbox from "vitepress-plugin-lightbox"


export default withMermaid({
    title: 'EIC AI Background',
    description: 'Background analysis pipelines and AI/ML datasets for the EIC ePIC detector',
    base: '/ai-epic-background/',

    head: [
        ['link', { rel: 'stylesheet', href: 'https://cdn.jsdelivr.net/npm/katex@0.16.0/dist/katex.min.css' }],
        ['meta', { name: 'viewport', content: 'width=device-width, initial-scale=1.0' }],
    ],

    themeConfig: {
        nav: [
            { text: 'Home', link: '/' },
            { text: 'CSV Convert', link: '/csv-convert' },
            { text: 'Full-Sim Pipeline', link: '/full-sim-pipeline' },
            { text: 'GitHub', link: 'https://github.com/eic/ai-epic-background' },
        ],

        sidebar: [
            {
                text: 'Getting Started',
                collapsed: false,
                items: [
                    { text: 'Overview', link: '/' },
                    { text: 'Data Format', link: '/data-format' },
                ]
            },
            {
                text: 'CSV Convert',
                collapsed: false,
                items: [
                    { text: 'Overview', link: '/csv-convert' },
                    { text: 'Running the Converter', link: '/csv-convert-running' },
                    { text: 'Snakemake & SLURM', link: '/csv-convert-snakemake' },
                ]
            },
            {
                text: 'Full-Sim Pipeline',
                collapsed: false,
                items: [
                    { text: 'Overview', link: '/full-sim-pipeline' },
                    { text: 'Job Creator', link: '/full-sim-pipeline-jobs' },
                    { text: 'Campaigns', link: '/full-sim-pipeline-campaigns' },
                ]
            },
            {
                text: 'AI / ML',
                collapsed: false,
                items: [
                    { text: 'Datasets', link: '/ai-datasets' },
                ]
            },
        ],

        footer: {
            message: 'Released under the MIT License.',
            copyright: 'Copyright © 2026 EIC AI Background Project'
        },

        socialLinks: [
            { icon: 'github', link: 'https://github.com/eic/ai-epic-background' }
        ],

        search: {
            provider: 'local'
        },

        outline: {
            level: [2, 3],
            label: 'On this page'
        },

        editLink: {
            pattern: 'https://github.com/eic/ai-epic-background/edit/main/docs/:path',
            text: 'Edit this page on GitHub'
        },

        appearance: true
    },

    markdown: {
        config: (md) => {
            md.use(markdownItKatex);
            md.use(lightbox, {});
        }
    },

    vite: {
        css: {
            preprocessorOptions: {
                scss: {
                    additionalData: `
            // Add any global SCSS variables here
          `
                }
            }
        }
    }
});
