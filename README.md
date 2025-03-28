# Metacritic-Analysis

**Metacritic-Analysis** is a data pipeline designed to scrape, parse, transform, and analyze information from the Metacritic website. This pipeline retrieves data about movies and games, saves it in a MongoDB instance, processes the raw data into JSON and cleansed data Parquet files, and uploads it to an AWS S3 bucket in two layers: raw and cleansed. The entire workflow is managed using Dockerized environment, with dependency management via Poetry.

## Project Overview

- **Data Collection**: Fetches data from Metacritic’s browse pages for movies and games.
- **Data Storage**: Saves HTML data in MongoDB to optimize scraping performance and provide recoverability.
- **Data Parsing and Transformation**: Extracts and cleans relevant information, uses AWS S3, storing raw data as JSON, and applies cleaning transformations and storing it as Parquet.
- **Pipeline Management**: Containerization with Docker/Docker-Compose, and dependencies managed by Poetry.

## Architecture

1. **Crawler**: A Python-based tool that scrapes data from Metacritic using HTTPX requests and HTML parsing with Selectolax.
2. **MongoDB**: MongoDB instance to store raw HTML data.
3. **AWS S3**: Stores raw and cleansed data layers in JSON and Parquet formats.
4. **Poetry**: Manages Python dependencies, defined in `pyproject.toml`.
5. **Dockerized Environment**: The Docker runtime for the Application, MongoDB and Mongo Express.

## Directory Structure

```plaintext
.
├── LICENSE.txt                      # License information
├── docker-compose.yml               # Docker Compose for managing services
├── Dockerfile                       # Dockerfile for building the project image
├── .dockerignore                    # Docker ignore file to exclude from Docker image build
├── .gitignore                       # Git ignore file to exclude files from version control
├── poetry.lock                      # Poetry lock file for dependency management
├── pyproject.toml                   # Poetry configuration file
├── python_version                   # Specifies the Python version used in the project
├── README.md                        # Project documentation
├── template.env                     # Environment template for variables
├── .pre-commit-config.yaml          # Pre-commit configuration file for Git hooks
├── app/
│   ├── analysis.py                  # Data analysis script
│   └── queries.py                   # Queries for database or other data sources
├── src/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── agents.py                # User Agent handling for web requests
│   │   ├── agents.py                # User Agent handling for web requests
│   │   ├── contracts.py             # Data models and interfaces
│   │   ├── requester.py             # Request handling logic
│   │   ├── settings.py              # Core settings and configuration
│   │   └── tools/
│   │       ├── __init__.py
│   │       ├── mongodb.py           # MongoDB utility functions
│   │       └── s3.py                # S3 utility functions for storage
│   ├── entrypoint.py                # Main entry point for the pipeline
│   ├── __init__.py
│   └── pipeline/
│       ├── extraction/
│       │   ├── __init__.py
│       │   ├── parsers/
│       │   │   ├── games_parser.py  # Parser for games data
│       │   │   ├── movies_parser.py # Parser for movies data
│       │   │   └── utils.py         # Utility functions for parsers
│       │   └── spider.py            # Main spider for scraping data
│       ├── __init__.py
│       └── transformation/
│           ├── data_cleansing.py    # Functions for cleaning extracted data
│           └── __init__.py
├── tests/
│   └── test_todo.py                      # Placeholder for tests

```

## Prerequisites

- **Docker and Docker Compose**
- **Poetry**
- **AWS S3** Account and proper access permissions.

## Setup and Installation

### Step 1: Clone the Repository

```bash
git clone <repository-url>

cd Metacritic-Analysis
```

### Step 2: Install Dependencies with Poetry

Install project dependencies via Poetry, ensuring the `pyproject.toml` configuration is utilized.

```bash
poetry install

poetry shell
```

### Step 3: Configure Environment Variables

Create a `.env` file from the `template.env` provided, adding your AWS, MongoDB and Mongo Express credentials (Example):

```plaintext
AWS_ACCESS_KEY_ID=<your-access-key>
AWS_SECRET_ACCESS_KEY=<your-secret-key>

S3_BUCKET_NAME=<your-bucket-name>
S3_FOLDER_NAME=<your-folder-name>

...
```

### Step 4: Start MongoDB and Mongo Express with Docker Compose

Run MongoDB using Docker Compose. Mongo Express will be accessible on port `8001` for database inspection.

```bash
docker-compose up -d
```

## Usage

### Running the Pipeline

The script `spider.py`, will manage the data extraction, parsing, and transformation process:

1. **Data Extraction**: Crawls Metacritic’s browse pages and saves HTML data in MongoDB.
2. **Parsing and Transformation**: Parses HTML content, extracts fields like ratings, genres, and platforms, then transforms raw data for upload.
3. **Data Upload to S3**: Saves JSON data to the S3 raw layer, applies cleansing, and stores it as Parquet in the cleansed layer.

### Accessing the Data

Raw JSON and cleansed Parquet files are available in S3, providing an easily accessible format for downstream analysis.

## Configuration

- **`docker-compose.yml`**: Adjust settings for MongoDB and Mongo Express storage and ports.
- **`.env`**: Set environment-specific configurations for AWS, MongoDB and Mongo Express.

## Troubleshooting

1. **Python Environment**: Verify the correct Poetry virtual environment is being used.
2. **MongoDB Issues**: Confirm MongoDB and Mongo Express containers are running.
3. **AWS Permissions**: Check that S3 permissions allow for read/write access.

## License

This project is licensed under the MIT License. Please see `LICENSE` for more information.

---
