Below is an updated README.md that reflects the project structure, package manager, and new project name: **Metacritic-Analysis**.

---

# Metacritic-Analysis

**Metacritic-Analysis** is a data pipeline designed to scrape, parse, transform, and analyze information from the Metacritic website. This pipeline retrieves data about movies and games, saves it locally in a MongoDB instance to reduce latency, processes the raw data into JSON files, and uploads it to an AWS S3 bucket in two layers: raw and cleansed. The entire workflow is managed using Astronomer’s CLI within a Dockerized environment, with dependency management via Poetry.

## Project Overview

- **Data Collection**: Fetches data from Metacritic’s browse pages for movies and games.
- **Data Storage**: Saves HTML data locally in MongoDB to optimize scraping performance and provide recoverability.
- **Data Parsing and Transformation**: Extracts and cleans relevant information, stores raw data as JSON in S3, and applies cleansing transformations.
- **Pipeline Management**: Orchestrated by Airflow, with Astronomer CLI handling the runtime environment, and dependencies managed by Poetry.

## Architecture

1. **Crawler**: A Python-based HTML parser that scrapes data from Metacritic.
2. **MongoDB**: Local MongoDB instance to store raw HTML data.
3. **AWS S3**: Stores raw and cleansed data layers in JSON format.
4. **Airflow DAGs**: Manages the data flow and orchestrates the pipeline.
5. **Poetry**: Manages Python dependencies, defined in `pyproject.toml`.
6. **Dockerized Environment**: The Docker runtime for Airflow and MongoDB.

## Directory Structure

```plaintext
.
├── airflow_settings.yaml           # Airflow configuration
├── dags                            # Contains Airflow DAGs
│   └── pipeline_dag.py             # Main DAG file
├── docker-compose.yml              # Docker Compose for services
├── Dockerfile                      # Astronomer Dockerfile for runtime
├── include                         # Additional files for Airflow
├── plugins                         # Custom plugins for Airflow
├── poetry.lock                     # Poetry lock file
├── pyproject.toml                  # Poetry configuration file
├── README.md                       # Project documentation
├── src                             # Source files
│   ├── core                        # Core modules and configurations
│   │   ├── agents.py
│   │   ├── contracts.py            # Data models and interfaces
│   │   ├── requester.py            # Request handling
│   │   ├── settings.py             # Core settings
│   │   └── tools                   # Utilities for MongoDB and S3
│   │       └── s3.py
│   ├── entrypoint.py               # Main entrypoint for pipeline
│   ├── pipeline                    # Pipeline modules
│   │   ├── extraction              # Extraction and parsing of data
│   │   │   └── parsers
│   │   │       ├── games_parser.py
│   │   │       ├── movies_parser.py
│   │   └── transformation          # Data cleansing functions
│   │       └── data_cleansing.py
└── template.env                    # Environment template for variables
```

## Prerequisites

- **Docker and Docker Compose**
- **Astronomer CLI**
- **Poetry**
- **AWS S3** account and proper access permissions

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
```

### Step 3: Configure Environment Variables

Create a `.env` file from the `template.env` provided, adding your AWS and MongoDB credentials:

```plaintext
AWS_ACCESS_KEY_ID=<your-access-key>
AWS_SECRET_ACCESS_KEY=<your-secret-key>

S3_BUCKET_NAME=<your-bucket-name>
S3_FOLDER_NAME=<your-folder-name>
```

### Step 4: Start MongoDB and Mongo Express with Docker Compose

Run MongoDB locally using Docker Compose. Mongo Express will be accessible on port `8001` for database inspection.

```bash
docker-compose up -d
```

### Step 5: Build and Run the Astronomer Runtime

Run the Airflow DAGs using Astronomer CLI and the provided `Dockerfile`.

```bash
astro dev start
```

## Usage

### Running the Pipeline

The Airflow DAG, `pipeline_dag.py`, will manage the data extraction, parsing, and transformation process:

1. **Data Extraction**: Crawls Metacritic’s browse pages and saves HTML data in MongoDB.
2. **Parsing and Transformation**: Parses HTML content, extracts fields like ratings, genres, and platforms, then transforms raw data for upload.
3. **Data Upload to S3**: Saves JSON data to the S3 raw layer, applies cleansing, and stores it in the cleansed layer.

### Accessing the Data

Raw and cleansed JSON files are available in S3, providing an easily accessible format for downstream analysis.

## Configuration

- **`docker-compose.yml`**: Adjust settings for MongoDB storage and ports.
- **`pipeline_dag.py`**: Customize the DAG schedule or add additional data processing steps.
- **`.env`**: Set environment-specific configurations for AWS and MongoDB.

## Troubleshooting

1. **MongoDB Issues**: Confirm MongoDB and Mongo Express containers are running.
2. **AWS Permissions**: Check that S3 permissions allow for read/write access.
3. **Astronomer CLI Configuration**: Verify Astronomer CLI is properly set up and Docker is running.

## License

This project is licensed under the MIT License. Please see `LICENSE` for more information.

---
