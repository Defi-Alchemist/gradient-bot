# 🚀 Gradient Network Multi-Account Automation

A sophisticated automation framework for managing multiple Gradient Network Sentry Nodes simultaneously. This tool streamlines the deployment and monitoring of browser-based edge compute nodes on the Solana blockchain, enabling efficient participation in the decentralized physical infrastructure (DePIN) ecosystem.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Architecture](#architecture)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## 🌐 Overview

Gradient Network represents a cutting-edge decentralized edge computing platform built on Solana, where participants operate lightweight browser-based nodes to earn rewards through computational resource sharing. The network focuses on AI inference, content delivery, and serverless functions, backed by prominent investors including Multicoin Capital, Pantera Capital, and Sequoia Capital.

This automation framework addresses the challenge of managing multiple Gradient Network accounts efficiently, providing enterprise-grade deployment capabilities with comprehensive monitoring and automatic recovery mechanisms.

## ✨ Features

### 🔄 Multi-Account Management
- **Concurrent Deployment**: Deploy multiple accounts simultaneously with intelligent staggered intervals
- **Individual Proxy Assignment**: Each account operates through its dedicated proxy for enhanced security
- **Resource Optimization**: Memory-optimized Chrome instances for maximum scalability
- **Account Isolation**: Complete separation between accounts to prevent cross-contamination

### 🛡️ Robust Automation
- **Intelligent Retry Logic**: Automatic recovery from connection failures and UI interaction issues
- **Health Monitoring**: Real-time status tracking with visual indicators
- **Error Handling**: Comprehensive error management with detailed logging
- **UI Interaction Resilience**: Advanced click retry mechanisms for unstable web elements

### 📊 Monitoring & Analytics
- **Real-time Health Status**: Live monitoring of node connectivity and uptime
- **Visual Progress Tracking**: Enhanced progress bars and status indicators
- **Comprehensive Logging**: Detailed logs for debugging and performance analysis
- **Account Performance Metrics**: Individual account statistics and health reports

### 🔧 Advanced Configuration
- **Proxy Integration**: Full support for authenticated HTTP proxies
- **Browser Optimization**: Memory-efficient Chrome configurations
- **Headless Operation**: Background execution without GUI overhead
- **Customizable Parameters**: Flexible configuration options for various deployment scenarios

## 📋 Prerequisites

### System Requirements
- **Memory**: Minimum 8GB RAM (16GB+ recommended for 20+ accounts)
- **Storage**: 2GB available disk space
- **Network**: Stable internet connection with proxy support

### Software Dependencies
- **Python**: Version 3.8 or higher
- **Chrome Browser**: Latest stable version

### Account Requirements
- Valid Gradient Network accounts with credentials
- HTTP proxy servers (one per account)
- Chrome extension: Gradient Sentry Node

## 🚀 Installation

### 1. Clone Repository
```bash
git clone https://github.com/Defi-Alchemist/gradient-bot
cd gradient-network-automation
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

## ⚙️ Configuration

### 1. Account Configuration (`data.txt`)
Create a file containing your Gradient Network credentials:
```
email1@example.com:password1
email2@example.com:password2
email3@example.com:password3
```

### 2. Proxy Configuration (`proxy.txt`)
Configure HTTP proxies (one per account, matching line numbers):
```
http://username1:password1@proxy1.example.com:8080
http://username2:password2@proxy2.example.com:8080
http://username3:password3@proxy3.example.com:8080
```

## 🎯 Usage

### Basic Execution
```bash
python main.py
```

### Deployment Flow
```
Account 1: Immediate deployment
Account 2: Deploys after 30 seconds
Account 3: Deploys after 60 seconds
...
Account N: Deploys after (N-1) × 30 seconds
```

## 🏗️ Architecture

### Core Components

#### `ChromeProxyAutomation`
- **Purpose**: Individual account management
- **Responsibilities**: Browser control, extension setup, health monitoring
- **Features**: Retry logic, error handling, resource cleanup

#### `MultiAccountManager`
- **Purpose**: Orchestrates multiple account deployments
- **Responsibilities**: Resource allocation, concurrent execution, monitoring coordination
- **Features**: Thread management, resource validation, cleanup coordination

### Process Flow
```mermaid
graph TD
    A[Start] --> B[Parse Configurations]
    B --> C[Validate Resources]
    C --> D[Create Account Instances]
    D --> E[Deploy with Staggered Intervals]
    E --> F[Monitor Health Status]
    F --> G{Connection Issues?}
    G -->|Yes| H[Initiate Retry]
    G -->|No| I[Continue Monitoring]
    H --> J[Cleanup Resources]
    J --> K[Restart Account]
    K --> F
    I --> F
```

## 📊 Monitoring

### Health Status Indicators
- 🟢 **Good**: Node is connected and operational
- 🔴 **Disconnected**: Node requires attention or retry
- ⚠️ **Warning**: Minor issues detected
- ℹ️ **Info**: General status updates

### Real-time Metrics
- **Account Status**: Individual node connectivity
- **Uptime Tracking**: Connection duration monitoring
- **Retry Statistics**: Failure and recovery counts
- **Resource Usage**: Memory and CPU utilization

### Log Analysis
Comprehensive logging includes:
- Deployment progress and status
- Error details with stack traces
- Performance metrics and timing
- Health check results and trends

## 🤝 Contributing

We welcome contributions to improve the automation framework. Please follow these guidelines:

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Implement changes with comprehensive testing
4. Submit pull request with detailed description

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This automation tool is designed for educational and research purposes. Users are responsible for:
- Compliance with Gradient Network terms of service
- Proper proxy usage and legal considerations
- Account security and credential management
- Resource usage and system performance monitoring

The developers assume no responsibility for account suspensions, financial losses, or system damage resulting from the use of this software.

## 🔗 Related Resources

- [Gradient Network Official](https://app.gradient.network/)
- [Solana Blockchain](https://solana.com/)
- [DePIN Ecosystem](https://messari.io/report/the-depin-sector-map)

---

**Built with ❤️ for the decentralized future**
