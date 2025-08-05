## Manually create (From your local machine)

- A GCP service account with billing enabled.
- A Project linked to the billing.
- Granting necessary permissions.
- verification.

- Authenticating with the gcolud CLI
  - $ gcloud auth login

- Create a project.
  - $ gcloud projects create dhakacity-forecast-mlops95 --name="Precipitation-95" --set-as-default

- Get the id of your billing account.
  - $ gcloud billing accounts list

- Link billing
  - gcloud beta billing projects link dhakacity-forecast-mlops25 \
     --billing-account=your-billing-id

- Enable APIs:
  - $ gcloud services enable compute.googleapis.com iam.googleapis.com storage.googleapis.com cloudresourcemanager.googleapis.com

- Grant Roles to the Service Account
  - $ gcloud config list account
  - $ gcloud projects add-iam-policy-binding dhakacity-forecast-mlops95 --member="serviceAccount:name@ml-name.iam.gserviceaccount.com" --role="roles/owner"

- Your donwloaded key file for the service account
  - $ gcloud auth activate-service-account --key-file=.gcp/Your-key-file.json

- Verify it's active
  - $ gcloud config list account

- Enabling Cloud Resource Manager API
  - $ gcloud config set project dhakacity-forecast-mlops95

Open the API activation link in your browser: Click enable wait for a few minutes

- Quick sanity check:
  - $ gcloud projects list
