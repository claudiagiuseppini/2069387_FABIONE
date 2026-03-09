# 2069387_FABIONE

## Mars Habitat Control System

Mars Habitat Control is an integrated IoT platform designed to monitor and automate environmental conditions in a simulated Martian habitat. The system receives data from various sensors and telemetries, normalizes it via a **Gateway**, evaluates automation rules, and controls actuators to maintain habitat safety.



## Startup

### 1. Prerequisites
Before starting the system, ensure you have **Docker** and **Docker Compose** installed on your machine.

### 2. Simulator Image Configuration
The system relies on an external simulator. Per project requirements, the simulator image must be available locally and must have the exact name specified in the `docker-compose.yml` file.
Therefore, before starting, ensure that the image is present in your local Docker registry and renamed exactly as:
**`mars-iot-simulator:multiarch_v1`**

> **Note:** The `docker compose up` command will fail if an image with this specific name is not found on your machine.

### 3. Deployment
To start the entire ecosystem (Gateway, Database, Broker, Frontend, and Simulator), run the following command from the project's root directory:

```bash
docker compose up -d
```

> **Note:** The `docker compose up` command is sufficient; adding the `-d` (detach) flag keeps the terminal cleaner. To read the logs, you will need to use the command `docker logs <container name>`.
