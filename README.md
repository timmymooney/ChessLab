# ChessLab ♟

**Personal chess performance analytics and coaching powered by Chess.com game data.**

ChessLab is an end-to-end Python project for analysing a player's Chess.com games, turning raw game data into study reccomendations.

The long-term goal is to allow a user to enter their Chess.com username, select a date range and game types, and receive a detailed analysis of their chess performance, including opening, middlegame and endgame performance, recurring mistakes, strengths, weaknesses, and personalised study recommendations.

---

### Current Roadmap

* [X] Set up Python project
* [   ] Connect to the Chess.com API
* [   ] Retrieve player's game archives
* [   ] Download games within a selected date range
* [   ] Parse PGN data and store games in a structured format
* [   ] Analyse games with Stockfish
* [   ] Classify opening, middlegame and endgame positions
* [   ] Identify mistakes and recurring patterns
* [   ] Build player performance profiles
* [   ] Generate personalised study recommendations
* [   ] Generate natural-language analysis reports
* [   ] Build interactive Streamlit (or similar) application
* [   ] Generate personalised training positions
* [   ] Deploy application

---

## Project Goals

While this is also intended as a portfolio project, ChessLab is intended to explore the intersection of:

* Chess
* Python
* Data science
* Machine learning
* Natural-language processing
* API integration
* Data engineering
* Interactive web applications

---

## Planned Architecture

The intended pipeline/workflow is:

```text
Chess.com API
      │
 PGN ingestion
      │
 Game parsing
      │
 Structured game data
      │
 Stockfish analysis
      │
 Feature extraction
      │
      ├───────────────┐ 
 Opening          Middlegame
 analysis         analysis
      │               │
      └───────┬───────┘
     Endgame analysis
              │
     Player profiling
              │
    Strengths & weaknesses
              │
    Study recommendations
              │
    NLP report generation
              │
    Interactive web app
```

---

## Planned Tech Stack

|                  |                  |
| ---------------- | ---------------- |
| Language         | Python           |
| Chess data       | Chess.com PubAPI |
| Chess parsing    | python-chess     |
| Chess engine     | Stockfish        |
| Data analysis    | pandas           |
| Database         | SQLite           |
| Machine learning | scikit-learn     |
| Visualisation    | Plotly           |
| Web application  | Streamlit        |
| Testing          | pytest           |
| Version control  | Git / GitHub     |

NOTE: The stack specifics may change as the project develops.

---

## Project Structure

The initial repo is intentionally small.

```text
ChessLab/
│
├── README.md
├── pyproject.toml
├── .gitignore
├── .env.example
│
└── src/
    └── chesslab/
        ├── __init__.py
        │
        └── api/
            ├── __init__.py
            └── chesscom.py
```

NOTE: The project will grow larger as new functionality is added.

---

## Project Set-Up 

### 1. Clone the repository

```bash
git clone https://github.com/timmymooney/ChessLab.git
cd ChessLab
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate environment (macOS/Linux):

```bash
source .venv/bin/activate
```

### 3. Install the project

```bash
pip install -e ".[dev]"
```

### 4. Run unit tests

```bash
pytest
```

---

## Environment

ChessLab is currently designed around Chess.com's public API and does not require an API key for its initial functionality.

A `.env.example` file is included as a template for future configuration, avoiding any upload of credentials.

---

## Planned Features

### Game Analysis

ChessLab will eventually analyse things like:

* Win/loss/draw records
* Rating progression
* Opening choices
* Move accuracy
* Blunders
* Mistakes
* Inaccuracies
* Game length and time control
* Game phases

### Personalised Recommendations

Based on the above analyses, ChessLab will generate suggestions such as:

* Tactical motifs to practise
* Openings to study
* Endgame concepts to review
* Types of positions to practise
* Recurring mistakes to address

### Natural-Language Reports

The final application will turn the underlying quantitative analysis into a readable report explaining:

> **What am I doing well?**

> **Where am I losing performance?**

> **What patterns appear across my games?**

> **What should I study next?**

---

## Data & API

ChessLab uses publicly available game information provided through Chess.com's public API.

The project is intended for educational, analytical and portfolio purposes. API usage will respect Chess.com's published API documentation and usage requirements.

---

## License

This project is currently under development. For now, the standard MIT License is used but may later be finalised as the project matures.

---

## ChessLab's Vision

> **Turn your chess games into a personalised training plan.**

ChessLab aims to move beyond simply telling a player which moves were inaccurate and instead identify the recurring patterns behind their mistakes, and should help them decide what to study next 📚