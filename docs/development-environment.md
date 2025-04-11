# Setting Up a Development Environment

This project depends on multiple external services:

- **MongoDB** for storing links.
- **AWS S3** for file storage.
- **Qdrant** for vector database embeddings.
- **OpenAI** for API requests.
- **LangSmith** (via LangChain) for tracing.

Depending on the value of the `PYTHON_ENV` variable, the project can run in two modes:

- **Development (dev):** Runs on local containers.
- **Production (prod):** Uses cloud-hosted services.

Before diving into the steps, make sure you have the following prerequisites installed:

- [Docker](https://docs.docker.com/get-docker/) (for running containers in development)
- [Python 3.8+](https://www.python.org/downloads/)
- [uv dependency management tool](https://pypi.org/project/uv/) (used to manage Python dependencies)

## Step 1. Create Your Environment Variable File

1. Navigate to the project’s root folder.
2. Copy the sample environment file and rename it to `.env` by running:

   ```bash
   cp .env.sample .env
   ```

3. Open the newly created `.env` file and update the values as needed (see the table below for an overview).

## Environment Variables Reference

| Variable Name              | Description                                                                            | Example / Notes                                                                                                                   |
| -------------------------- | -------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| **LOG_LEVEL**              | Sets the logging level for the application (e.g., `INFO`, `DEBUG`).                    | `LOG_LEVEL="INFO"`                                                                                                                |
| **PYTHON_ENV**             | Specifies the environment mode. Set to `dev` for development or `prod` for production. | `PYTHON_ENV="dev"`                                                                                                                |
| **OPENAI_API_KEY**         | Your API key for accessing OpenAI services.                                            | `OPENAI_API_KEY="YOUR_OPENAI_API_KEY"`                                                                                            |
| **QDRANT_COLLECTION_NAME** | Name of the collection in Qdrant where embeddings are stored.                          | `QDRANT_COLLECTION_NAME="ragify"`                                                                                                 |
| **LANGSMITH_TRACING**      | Enable or disable LangSmith tracing. Use `"true"` to enable.                           | `LANGSMITH_TRACING="true"`                                                                                                        |
| **LANGSMITH_ENDPOINT**     | URL endpoint for the LangSmith API.                                                    | `LANGSMITH_ENDPOINT="https://api.smith.langchain.com"`                                                                            |
| **LANGSMITH_API_KEY**      | API key for LangSmith.                                                                 | `LANGSMITH_API_KEY="YOUR_LANGSMITH_API_KEY"`                                                                                      |
| **LANGSMITH_PROJECT**      | The project name used in LangSmith for tracing.                                        | `LANGSMITH_PROJECT="Ragify"`                                                                                                      |
| **MONGODB_URI**            | Connection string for your MongoDB database (production only).                         | `MONGODB_URI="mongodb+srv://username:password@your_mongodb_cluster.mongodb.net/?retryWrites=true&w=majority&appName=YourAppName"` |
| **AWS_ACCESS_KEY_ID**      | AWS access key identifier for S3. (Production only)                                    | `AWS_ACCESS_KEY_ID="YOUR_AWS_ACCESS_KEY_ID"`                                                                                      |
| **AWS_SECRET_ACCESS_KEY**  | AWS secret key for S3 authentication. (Production only)                                | `AWS_SECRET_ACCESS_KEY="YOUR_AWS_SECRET_ACCESS_KEY"`                                                                              |
| **AWS_REGION**             | AWS region for your S3 bucket.                                                         | `AWS_REGION="us-east-2"`                                                                                                          |
| **AWS_BUCKET_NAME**        | The name of the AWS S3 bucket where files will be stored. (Production only)            | `AWS_BUCKET_NAME="your_aws_bucket_name"`                                                                                          |
| **QDRANT_URL**             | URL for your Qdrant deployment. (Production only)                                      | `QDRANT_URL="https://your-qdrant-url.com"`                                                                                        |
| **QDRANT_API_KEY**         | API key for accessing the Qdrant vector database. (Production only)                    | `QDRANT_API_KEY="YOUR_QDRANT_API_KEY"`                                                                                            |

> **Note:** If you're running in **development mode**, you can leave the production credentials (starting with `MONGODB_URI` and beyond) empty.

## Step 2. Run the Application in Development Mode

When using **development mode** (`PYTHON_ENV="dev"`), you will run the services locally using Docker containers:

1. **Start Docker Containers:**

   Open a terminal and change the directory to `docker/`:

   ```bash
   cd docker/
   docker-compose up
   ```

   This will launch all necessary containers locally.

2. **Install Python Dependencies using uv:**

   In the project’s root directory, ensure you have `uv` installed. If not, install it using pip:

   ```bash
   pip install uv
   ```

   Then, run the following command to install your Python dependencies:

   ```bash
   uv install
   ```

   For more details on using `uv`, check out the [uv documentation on PyPI](https://pypi.org/project/uv/).

3. **Run the Application:**

   Return to the project’s root directory and run:

   ```bash
   streamlit run app/Chat.py
   ```

   This command launches the Streamlit app so you can start interacting with it.

## Step 3. Running in Production Mode

When deploying in **production mode** (`PYTHON_ENV="prod"`), the project uses cloud services. Make sure to fill in **all** the production credentials in your `.env` file:

- MongoDB connection (MongoDB Atlas):
  - [MongoDB Atlas Documentation](https://www.mongodb.com/cloud/atlas)
- AWS S3 setup:
  - [AWS S3 Documentation](https://aws.amazon.com/s3/)
- Qdrant vector database:
  - [Qdrant Documentation](https://qdrant.tech/documentation/)

By following these detailed steps and using the environment variable table for reference, you should have a much easier time configuring and running the project in both development and production environments. Happy coding!
