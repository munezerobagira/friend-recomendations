# Friend Recommendation System

Welcome to the Friend Recommendation System repository. This project includes two main components:

- **ETL (Extract, Transform, Load)**: A system designed to load over 160MB of data.
- **RESTful API**: An API for users to query and receive recommended friends.

## Features

- **ETL System**: Efficiently processes and loads large datasets.
- **RESTful API**: Allows users to interact with the system to get friend recommendations based on interactions, hashtags, and keywords.

## Setup

### Prerequisites

- Docker and Docker Compose installed on your machine.

### Steps to Run the System

1. **Clone the Repository**

   ```bash
   git clone https://github.com/munezerobagira/friend-recommendation-system.git
   cd friend-recommendation-system
   ```

2. **Create Environment Variables**

   Use the `.env.example` file as a template to create your own `.env` file.

   ```bash
   cp .env.example .env
   ```

   Then, fill in the necessary environment variables:

   ```env
   DATABASE_URL=postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@db:5432/$POSTGRES_DB
   POSTGRES_USER=*******
   POSTGRES_PASSWORD=*******
   POSTGRES_DB=******
   NGINX_PORT=**
   ```

3. **Build and Start the Docker Containers**

   Use Docker Compose to build and start the services. This will set up both the API and the Nginx server.

   ```bash
   docker-compose up --build
   ```

4. **Run the ETL Script**

   Execute the ETL script to process and load the data.

   ```bash
   docker compose exec api python src/etl.py
   ```

5. **Access the API**

   Once the services are running, you can access the API at `http://localhost/docs`.

## Testing

To run tests, use pytest with SQLite. The tests are configured to run automatically in the GitHub Actions workflow.

1. **Run Tests Locally**

   Ensure you have pytest installed. Then, run the tests:

   ```bash
   pytest src
   ```

2. **GitHub Actions Workflow**

   The GitHub Actions workflow is set up to run tests on push and pull request events to the `main` branch.
