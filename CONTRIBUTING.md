# Contributing to JIAZ

Thank you for your interest in contributing to **`jiaz`**! We welcome your ideas, bug reports, and code contributions.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Ways to Contribute](#ways-to-contribute)
- [How to Raise an Issue](#how-to-raise-an-issue)
- [How to Submit a Pull Request](#how-to-submit-a-pull-request)
- [Development Setup](#development-setup)
- [Code Review Process](#code-review-process)
- [Community Standards](#community-standards)

---

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md) to ensure a welcoming and respectful environment for all contributors.

---

## Ways to Contribute

- **Bug Reports:** Found a bug? Please [open an issue](https://github.com/sankur-codes/jiaz/issues).
- **Feature Requests:** Suggest new features by [opening an issue](https://github.com/sankur-codes/jiaz/issues).
- **Documentation:** Improve existing docs or add new ones.
- **Code:** Tackle open issues or propose enhancements.

---

## How to Raise an Issue

1. Search [existing issues](https://github.com/sankur-codes/jiaz/issues) to avoid duplicates.
2. If none match, click "New Issue" and fill out the issue template:
   - **Type:** If its a bug or a feature request or enhancement.
   - **Description:** Explain the problem or feature request.
   - **Steps to Reproduce:** If reporting a bug, provide step-by-step instructions.
   - **Expected Behaviour:** What is to be the desired output ?
   - **Actual Behaviour:** What is the current output ?
   - **Additional Information:** Any supporting context.

---

## How to Submit a Pull Request

1. **Fork** the repo and **clone** it locally:
   ```sh
   git clone https://github.com/<your-username>/jiaz.git
   cd jiaz
   ```
2. **Create a new branch** for your work:
   ```sh
   git checkout -b feature/your-branch
   ```
3. **Make your changes**:
   - Follow project style and conventions.
   - Add or update tests as needed.
   - Update documentation if applicable.
   - Run lints and tests to make sure all passes
4. **Commit** with clear messages:
   ```sh
   git commit -m "Add feature X"
   ```
5. **Push** your branch:
   ```sh
   git push origin feature/your-feature
   ```
6. **Open a Pull Request** on GitHub:
   - Fill out the PR template, referencing any related issues.
   - Ensure all CI checks pass.

---

## Development Setup

- See [README.md](README.md) for install and build instructions.
- Run tests with:
  ```sh
  make test
  ```

---

## Code Review Process

- All PRs require review and approval from maintainers.
- Address feedback and requested changes promptly.
- PRs may be merged once approved and CI passes.

---

## Community Standards

- Be respectful and collaborative.
- See our [Code of Conduct](CODE_OF_CONDUCT.md).

---

Thank you for helping make `jiaz` awesome!