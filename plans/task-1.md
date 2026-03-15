# Task 1: Call an LLM from Code — Implementation Plan

**Author:** Marsel (mmmrsssl)  
**Date:** 2026-03-16  
**Task:** [Task] Call an LLM from Code

## 1. LLM Provider and Model Selection

### Provider: Qwen Code API (self-hosted on VM)

- **Reason for choice:**
  - Provides 1000 free requests per day
  - Works from Russia without credit card
  - Already deployed and tested on my VM at `http://10.93.26.31:42005/v1`
  - Successfully verified with curl command
  - Recommended in the task instructions

### Model: `qwen3-coder-plus`

- **Why this model:**
  - Recommended as default in `.env.agent.example`
  - Strong tool-calling capabilities (will be needed in Tasks 2-3)
  - Good balance of performance and speed
  - Successfully tested with sample query

## 2. Agent Architecture

### 2.1. Overview

The agent will be a simple Python CLI program (`agent.py`) that:

1. Reads configuration from `.env.agent.secret`
2. Takes a question as command-line argument
3. Sends it to LLM via OpenAI-compatible API
4. Outputs structured JSON response

### 2.2. Program Flow

```mermaid
flowchart TD
    A[Start] --> B[Load .env.agent.secret]
    B --> C{Question provided?}
    C -->|No| D[Print error to stderr, exit 1]
    C -->|Yes| E[Prepare API request]
    E --> F[Send POST to LLM API]
    F --> G{Response OK?}
    G -->|No| H[Print error to stderr, exit 1]
    G -->|Yes| I[Parse JSON response]
    I --> J[Extract answer text]
    J --> K[Build output JSON]
    K --> L[Print JSON to stdout]
    L --> M[Exit 0]
