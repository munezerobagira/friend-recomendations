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

   quick note: if you are running the script on a local machine, you can use the following command:

   ```bash
   python src/etl.py

   ```

   as it would be more fast

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

## Lessons Learned

One important thing I learned is about database management. It's not possible to delete a database while it is in use, i.e., when there are some uncommitted transactions. It's better to properly handle closing connections so that transactions are either committed or rolled back before closing the connection. If you haven't handled closing connections well, you can close all connections to the database using:

```sql
SELECT
 pg_terminate_backend(pid)
FROM
 pg_stat_activity
WHERE
 datname = '<TARGET_DB_NAME>'
AND
 leader_pid IS NULL
;
```

## Achievements

I am proud of improving the ETL process to save data in chunks to avoid memory errors using multiple processes. Previously, it was taking over 6 hours to save data to the cloud database, and now it takes a little over 40 minutes. For a local machine, it was over 10 minutes, but I managed to reduce it to below 40 seconds.

The complex part was loading data on a server with only one CPU and 1GB of RAM. I had to use my computer locally, which has more RAM and CPU, and send the data to be saved in the database on the server, which increased the latency.

## Future improvements

- **Optimize the ETL process**: The ETL process can be further optimized to reduce the time it takes to load the data.
- **Improve the API**: The API can be improved by reducing the response, when the pharse is too short and for the hashtag.
