export type DocLink = { label: string; href: string };
export type DocGroup = { group: string; links: DocLink[] };

export const DOCS_GITHUB_URL = "https://github.com/Pavilion-devs/halo";
export const DOCS_DEMO_URL = "https://youtu.be/nW7aeeBrIZQ";

export const DOCS_NAV: DocGroup[] = [
  {
    group: "Overview",
    links: [
      { label: "Introduction", href: "/docs" },
      { label: "Run it locally", href: "/docs/run-locally" }
    ]
  },
  {
    group: "How it works",
    links: [
      { label: "Architecture", href: "/docs/architecture" },
      { label: "Jaguar integration", href: "/docs/jaguar" },
      { label: "Resilience & modes", href: "/docs/resilience" },
      { label: "Guardrails & safety", href: "/docs/guardrails" }
    ]
  },
  {
    group: "Platform & deployment",
    links: [
      { label: "TrueFoundry + Bedrock", href: "/docs/truefoundry" },
      { label: "Deployment", href: "/docs/deployment" },
      { label: "API reference", href: "/docs/api" }
    ]
  }
];

export const DOCS_FLAT: DocLink[] = DOCS_NAV.flatMap((g) => g.links);
