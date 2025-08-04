#!/bin/bash
set -euo pipefail

# === Logging ===
echo "Startup script initiated at: $(date)"
echo "Running as: $(whoami)"

# === Config ===
USERNAME="bonisadar"
USER_HOME="/home/$USERNAME"
CONDA_DIR="$USER_HOME/miniconda3"
ENV_NAME="mlopsenv"
PROJECT_PARENT_DIR="$USER_HOME/projects"
PROJECT_NAME="dhakacity-precipitation-forecast-mlops25"
PROJECT_DIR="$PROJECT_PARENT_DIR/$PROJECT_NAME"
GIT_REPO_URL="https://github.com/bonisadar/$PROJECT_NAME"
REQS_FILE="/tmp/requirements.txt"

# === Wait until user home is available ===
echo "Waiting for user home directory..."
until [ -d "$USER_HOME" ]; do
    sleep 2
done

# === Ensure project parent directory exists ===
sudo mkdir -p "$PROJECT_PARENT_DIR"
sudo chown -R "$USERNAME:$USERNAME" "$PROJECT_PARENT_DIR"

# === System Update ===
echo "🛠️ Updating system..."
sudo apt-get update && sudo apt-get upgrade -y

echo "Installing essentials..."
sudo apt-get install -y \
  curl wget unzip git build-essential htop \
  bzip2 software-properties-common \
  ca-certificates gnupg lsb-release apt-transport-https

# === Docker Installation ===
if ! command -v docker &>/dev/null; then
  echo "🐳 Installing Docker..."
  sudo install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

  echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

  sudo apt-get update
  sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

  echo "🔧 Adding $USERNAME to docker group..."
  sudo usermod -aG docker "$USERNAME"
else
  echo "✅ Docker already installed."
fi

echo "ℹ️ You may need to reboot or re-login for Docker group changes to take effect."

# === Install Miniconda ===
if [ ! -d "$CONDA_DIR" ]; then
  echo "Installing Miniconda..."
  wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh
  bash /tmp/miniconda.sh -b -p "$CONDA_DIR"
  chown -R $USERNAME:$USERNAME "$CONDA_DIR"
else
  echo "✅ Miniconda already installed."
fi

# === Initialize conda ===
echo "🔁 Sourcing conda..."
source "$CONDA_DIR/etc/profile.d/conda.sh"

# Accept Terms of Service for channels
echo "✅ Accepting Conda Terms of Service..."
conda config --set always_yes yes
conda config --add channels defaults
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r

if ! grep -q "$CONDA_DIR/bin" "$USER_HOME/.bashrc"; then
  echo "export PATH=\"$CONDA_DIR/bin:\$PATH\"" >> "$USER_HOME/.bashrc"
fi


# === Create conda environment ===
if ! conda info --envs | grep -q "$ENV_NAME"; then
  echo "📦 Creating conda environment: $ENV_NAME"
  conda create -n "$ENV_NAME" python=3.10 -y
else
  echo "✅ Conda environment $ENV_NAME already exists."
fi

# === Activate the conda environment ===
echo "⚡ Activating conda environment: $ENV_NAME"
conda activate "$ENV_NAME"

# === Clone the project ===
if [ ! -d "$PROJECT_DIR/.git" ]; then
  echo "📁 Cloning project repository into $PROJECT_DIR..."
  git clone "$GIT_REPO_URL" "$PROJECT_DIR"
  sudo chown -R "$USERNAME:$USERNAME" "$PROJECT_DIR"
else
  echo "✅ Project already exists at $PROJECT_DIR — skipping clone."
fi

# === Python Requirements ===
echo "📄 Writing requirements.txt..."
cat <<EOF > "$REQS_FILE"
numpy==2.2.6
pandas==2.3.0
scikit-learn==1.7.0
xgboost==3.0.2

fastapi==0.115.13
uvicorn[standard]

google-cloud-storage==2.16.0
psycopg2-binary==2.9.10
pyarrow==20.0.0
fastparquet==2024.11.0

mlflow==3.1.1
prefect==3.4.6

requests==2.31.0
pytest
requests-mock
EOF

echo "📦 Installing system packages: tmux, nano, and net-tools (for netstat)..."
sudo apt update && sudo apt install -y tmux nano net-tools

echo "📦 Installing Python packages into '$ENV_NAME'..."
conda activate "$ENV_NAME"
python -m pip install --upgrade pip
python -m pip install -r "$REQS_FILE"
conda deactivate
rm "$REQS_FILE"

# === Aliases ===
echo "🔧 Adding helper aliases..."
if ! grep -q "alias actenv" "$USER_HOME/.bashrc"; then
  echo "alias actenv='conda activate $ENV_NAME'" >> "$USER_HOME/.bashrc"
fi

echo "✅ All done! Script finished at: $(date)"
