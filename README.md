# IT Management and Audits — Project Portfolio

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](#license)
[![Projects: 15](https://img.shields.io/badge/Projects-15-brightgreen.svg)](#projects)
[![Status: Active](https://img.shields.io/badge/Status-Active-success.svg)](#)

A comprehensive collection of 15 hands-on projects covering IT management, governance, security auditing, and financial technology. Each project is a standalone toolkit with source code, documentation, and tests — designed as practical, portfolio-ready demonstrations of enterprise IT concepts.

---

## Projects

| # | Project | Description | Tech Stack |
|---|---------|-------------|------------|
| 1 | [Cloud Infrastructure Lab](./cloud-infra-lab/) | Hands-on cloud provisioning lab with Terraform IaC | Terraform, AWS, Node.js, Nginx |
| 2 | [IT Governance Framework Mapper](./governance-framework-mapper/) | Map IT processes to COBIT 2019 and ITIL v4 frameworks | Python, Click, Rich, Jinja2 |
| 3 | [Network Traffic Analyzer](./network-traffic-analyzer/) | Capture, parse, and analyze network traffic for anomalies | Python, Scapy, Matplotlib |
| 4 | [Web Application Security Scanner](./webapp-security-scanner/) | Vulnerability scanner with a deliberately vulnerable target app | Python, Flask, OWASP Top 10 |
| 5 | [Agile Sprint Simulator](./agile-sprint-simulator/) | Interactive sprint simulation with burndown charts and Kanban | Python, Click, Rich, Matplotlib |
| 6 | [Financial Data Manager](./financial-data-manager/) | SQL-based financial data management with data quality checks | Python, SQLite, Faker |
| 7 | [Financial Data Visualizer](./financial-data-visualizer/) | Financial analytics with 10+ chart types and interactive dashboards | Python, Matplotlib, Plotly, Seaborn |
| 8 | [BI Dashboard Builder](./bi-dashboard-builder/) | Self-service business intelligence dashboard generator | Python, Flask, Plotly, Pandas |
| 9 | [Mobile UX Prototyping Toolkit](./mobile-ux-toolkit/) | Mobile banking wireframes and design system | HTML5, CSS3, JavaScript |
| 10 | [API Integration Testing Suite](./api-testing-suite/) | Mock payment API with automated test suite and Postman collection | Python, Flask, Pytest, OpenAPI |
| 11 | [IT Audit Toolkit](./it-audit-toolkit/) | Audit management system with checklists, risk scoring, and reports | Python, Click, Rich, Jinja2 |
| 12 | [Smart Contract Development Kit](./smart-contract-devkit/) | Solidity smart contracts with Hardhat tests and deployment scripts | Solidity, Hardhat, Ethers.js |
| 13 | [Crypto Wallet Explorer](./crypto-wallet-explorer/) | Ethereum wallet generation and transaction exploration toolkit | Python, Web3.py, eth-account |
| 14 | [Incident Response Playbook](./incident-response-playbook/) | IR simulation engine with 5 scenarios and detailed playbooks | Python, Click, Rich, Jinja2 |
| 15 | [Security Assessment Platform](./security-assessment-platform/) | End-to-end security assessment with scanning, compliance, and reporting | Python, Flask, PyYAML, Chart.js |

---

## Getting Started

### Prerequisites

- **Python 3.8+** — Required for projects 2-8, 10-14
- **Node.js 18+** — Required for projects 1, 12
- **Git** — Version control

### Running a Project

Each project is self-contained with its own README, dependencies, and instructions.

```bash
# Example: Running the IT Governance Framework Mapper
cd governance-framework-mapper
python -m venv venv
source venv/bin/activate    # Linux/macOS
venv\Scripts\activate       # Windows
pip install -r requirements.txt
python src/cli.py --help
```

```bash
# Example: Running the Smart Contract DevKit
cd smart-contract-devkit
npm install
npx hardhat compile
npx hardhat test
```

---

## Project Categories

### Infrastructure & Cloud
- **Cloud Infrastructure Lab** — AWS provisioning, VPC networking, Terraform IaC

### Governance & Compliance
- **IT Governance Framework Mapper** — COBIT 2019 / ITIL v4 process mapping
- **IT Audit Toolkit** — Audit checklists, risk assessment, compliance reporting

### Security
- **Network Traffic Analyzer** — Packet analysis and anomaly detection
- **Web Application Security Scanner** — OWASP vulnerability scanning
- **Incident Response Playbook** — IR simulation and response procedures
- **Security Assessment Platform** — Comprehensive security assessment suite

### Financial Technology
- **Financial Data Manager** — Database management with data quality framework
- **Financial Data Visualizer** — Analytics charts and dashboards
- **BI Dashboard Builder** — Self-service BI dashboard generator

### Blockchain
- **Smart Contract Development Kit** — Solidity contracts with testing
- **Crypto Wallet Explorer** — Wallet mechanics and transaction exploration

### Software Engineering
- **Agile Sprint Simulator** — Sprint planning and execution simulation
- **API Integration Testing Suite** — REST API testing methodology
- **Mobile UX Prototyping Toolkit** — Mobile banking UX design system

---

## Repository Structure

```
it-management-and-audits/
├── README.md                          # This file
├── .gitignore                         # Master gitignore
├── cloud-infra-lab/                   # Project 1
├── governance-framework-mapper/       # Project 2
├── network-traffic-analyzer/          # Project 3
├── webapp-security-scanner/           # Project 4
├── agile-sprint-simulator/            # Project 5
├── financial-data-manager/            # Project 6
├── financial-data-visualizer/         # Project 7
├── bi-dashboard-builder/              # Project 8
├── mobile-ux-toolkit/                 # Project 9
├── api-testing-suite/                 # Project 10
├── it-audit-toolkit/                  # Project 11
├── smart-contract-devkit/             # Project 12
├── crypto-wallet-explorer/            # Project 13
├── incident-response-playbook/        # Project 14
└── security-assessment-platform/      # Project 15
```

Each project contains:
- `README.md` — Project overview, setup, and usage instructions
- `src/` or source code directory — Fully functional implementation
- `tests/` — Unit tests
- `docs/` — Detailed documentation and guides
- `requirements.txt` or `package.json` — Dependencies
- `LICENSE` — MIT License

---

## License

All projects in this repository are licensed under the [MIT License](https://opensource.org/licenses/MIT).

---

## Contributing

Contributions are welcome! Please open an issue first to discuss proposed changes.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/improvement`)
3. Commit your changes (`git commit -m "Add improvement"`)
4. Push to the branch (`git push origin feature/improvement`)
5. Open a Pull Request
