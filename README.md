# Helmholtz AI Workshop Series

https://nickdelgrosso.github.io/HelmholtzAI-TrainingSeries2025/

A collaborative training program on scientific software development practices for early-career professionals working on machine learning consulting projects.

## Overview

This repository contains materials for an 8-session workshop series designed for Helmholtz AI consultants and similar professionals working on short-term (3-12 month) data science and ML projects. The series focuses on software development practices that make research projects easier to collaborate on, maintain, and scale.

## Project Structure

```
hhai-repo/
├── notebooks/          # Jupyter notebooks with workshop materials
│   ├── 01_git/        # Git and version control session
│   └── index.ipynb    # Series overview and schedule
├── site/              # Hugo static site for publishing materials
│   └── content/       # Generated markdown content
├── scripts/           # Automation scripts
│   ├── notebooks_to_site.py  # Convert notebooks to Hugo markdown
│   └── watch.py       # Auto-convert on file changes
└── pixi.toml          # Environment and dependency management
```

## Getting Started

### Prerequisites

This project uses [Pixi](https://pixi.sh/) for environment management. Install Pixi following the instructions at https://pixi.sh/

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd hhai-repo

# Install dependencies (Pixi will handle everything)
pixi install
```

## Usage

### Convert Notebooks to Site Content

Convert Jupyter notebooks to Hugo-compatible markdown:

```bash
pixi run convert
```

### Watch for Changes

Automatically convert notebooks when they're modified:

```bash
pixi run watch
```

### Serve the Site Locally

Start a local web server to preview the site:

```bash
pixi run serve
```

The site will be available at http://localhost:1313

## Workshop Structure

Each workshop session includes:

1. **Pre-workshop materials** - Readings, tutorials, and exercises with Q&A via GitHub Discussions
2. **Live workshop** - Interactive group problem-solving with toy examples and real-world breakouts
3. **Follow-up consulting** - One-on-one or small group support for applying practices to real projects
4. **Team reflection** - Planning and steering for upcoming sessions

## Technologies

- **Hugo** - Static site generator using the LotusDocs theme
- **Pixi** - Cross-platform package and environment manager
- **Python** - Notebook processing and automation
- **Jupyter** - Interactive notebook materials

## Contributing

Workshop materials are developed iteratively. Participants can contribute questions, examples, and feedback through GitHub Discussions and Issues.

## License

This project uses a dual license approach:

- **Teaching Materials** (notebooks, documentation, workshop content) - [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/)
- **Code** (scripts, automation tools) - [MIT License](LICENSE-CODE)

You are free to use, share, and adapt the materials with attribution. See individual LICENSE files for full terms.

## Contact

Nicholas A. Del Grosso <delgrosso.nick@gmail.com>
