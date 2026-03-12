Gan Shmuel Project
Welcome to the Gan Shmuel repository. This project is structured to handle automated CI/CD workflows and multi-service deployments using Docker and Bash scripting.

🚀 Getting Started
Follow these steps to set up the environment and trigger the production deployment.

1. Clone the Repository
First, clone the project to your local machine or EC2 instance using SSH:

Bash
git clone git@github.com:GanShmuel-Develeap/Gan_Shmuel.git
cd Gan_Shmuel
2. Navigate to the DevOps Directory
All infrastructure and deployment scripts are centralized within the devops folder:

Bash
cd devops
3. Run the Production Script
To deploy the integrated environment, execute the production script. Ensure you have the necessary permissions to run bash scripts and interface with Docker:

Bash
chmod +x production.sh
./production.sh
🛠 Project Structure
/billing: Contains the Billing service logic, Dockerfile, and unit/integration tests.

/weight: Contains the Weight service logic, Dockerfile, and unit/integration tests.

/devops: Contains the CI/CD pipeline scripts (pipeline.sh), E2E tests, and the final production deployment logic.

🧪 CI/CD Workflow
The project utilizes a pipeline.sh script that automates the following:

Branch Syncing: Fetches the latest code from the specified branch.

Testing: Runs Unit and Integration tests within Docker containers.

Health Checks: Verifies connectivity between services and databases (e.g., billing-db to weight-db).

Slack Integration: Sends real-time status reports to the team.

Promotion: Automatically promotes stable code to the devops branch for E2E verification.

📋 Prerequisites
Docker & Docker Compose: Ensure both are installed and the daemon is running.

Git: Configured with SSH access to the GitHub repository.

Environment Variables: A .env file should be present in the root directory containing your SLACK_WEBHOOK_URL for notifications.

Would you like me to add a "Troubleshooting" section to this README with common Docker network and permission fixes?
