# Safi
**Safi** is a web-based utility designed to simplify and automate shared expense calculations for small groups.

The application is built to eliminate the confusion and manual effort involved when groups of people (like roommates, friends, or coworkers) share costs. Users log expenses they have paid for the group, and the application calculates the most efficient way to settle all debts so that each member has contributed their equal share.

The primary goal is to provide a clear, accurate, and simple solution that prevents financial disagreements and makes living or working together easier. The key benefit is transforming a complex calculation mess into a simple clear set of who-pays-whom instructions.


## Prerequisites

Before you start, ensure you have the following installed:

- **WSL** (for windows)
- **Docker**
- **MiniConda**
- **Python 3.13+**
- **black formatter**
- **flake8**
- **isort**

## ⚡ Quick Start (Onboarding)

Follow these steps to get the app running on your local machine

### 1\. Clone the Repository

```
$git clone https://github.com/OsamaAshraf01/Safi.git
$cd Safi
```

### 2\. Configure Environment

**Create your Secret `.env` file:**

```
$cp .env.example .env
```

_Action:_ Open `.env` and fill in any missing secrets (ask the Team Lead for keys).

### 3\. Setup the environment
Download and install MiniConda from [here](https://www.anaconda.com/docs/main)

Create a new environment using the following command:

````
$conda create -n safi python=3.13
````

Activate the environment:

```
$conda activate safi
```

Install the requiremnets:

```
$pip install -r requirments.txt
```
### 4\. Install Pre-Commit Hooks

Install hooks

```
$pre-commit install
```

_Now, Git will automatically fix your formatting when you commit code._

### 5\. Run the App

```
$docker-compose up --build
```

- **Backend:** <http://localhost:5000>

## Development Workflow

### Checking Logs
Check your terminal for Flask logs when running the container.
<br>Or acces the throught terminal
```
$docker logs safi_dev
```
### Running Tests

We run tests **inside** the Docker container to match the environment using the following commands:

- Run all tests
```
$docker-compose exec web pytest
```

- Run only unit tests
```
$docker-compose exec web pytest tests/unit
```

### Installing New Dependencies

If `requirements.txt` gets updated you need to Rebuild the container as follows:
```
$docker-compose up -d --build
```
## Extentions for VSCode user
if you use vscode for development you may need to download the following extentions:
- **Github Actions**
- **black formatter**
- **flake8**
- **isort**
