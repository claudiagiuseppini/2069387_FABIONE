# SYSTEM DESCRIPTION:

Mars Habitat Control is an IoT platform for monitoring and automating environmental conditions inside a simulated Mars habitat. The system collects telemetry from a simulator, normalizes and distributes sensor data through a message broker, evaluates automation rules, commands actuators, and exposes a web dashboard for real-time supervision. Through the dashboard, the user can manage automation rules, inspect sensor status, detect dangerous conditions, manually control actuators, and visualize live metrics and alerts.

# USER STORIES:

1) As the User I want to see all the rules in a compact way
2) As the User I want to add a new rule
3) As the User I want to remove an existing rule
4) As the User I want to modify an existing rule
5) As the User I want to enable/disable an existing rule
6) As the User I want to reset the rules
7) As the User I want to save all rules persistently
8) As the User I want to see which sensors violate the rules.
9) As the User I want to see the current active actuators
10) As the User I want to see the current active sensors
11) As the User I want to manually turn on/off a specific actuator
12) As the User I want to reset all actuators to off
13) As the User I want to visualize charts regarding current data from sensors
14) As the User I want to visualize related sensors near to each other
15) As the User I want to see how much time has passed since the latest update
16) As the User I want to visualize dangerous conditions as red
17) As the User I want to see the number of sensors, live telemetries, active rules and actuators currently on.
18) As the User I want to see which sensors are in warning status
19) As the User I want to directly access the alert section by clicking on a single button
20) As a User, I want to be notified when a rule has been broken, a violation has been resolved and when rules have been modified.

# CONTAINERS:

## CONTAINER_NAME: Simulator

### DESCRIPTION:
Provides the simulated Mars habitat environment. It exposes sensor and actuator APIs and produces the telemetry consumed by the platform.

### USER STORIES:
10) As the User I want to see the current active sensors
11) As the User I want to manually turn on/off a specific actuator
12) As the User I want to reset all actuators to off
13) As the User I want to visualize charts regarding current data from sensors
15) As the User I want to see how much time has passed since the latest update
17) As the User I want to see the number of sensors, live telemetries, active rules and actuators currently on.
18) As the User I want to see which sensors are in warning status

### PORTS:
8080:8080

### PERSISTENCE EVALUATION
The Simulator container does not manage persistent application data inside this project. It acts as the runtime source of telemetry and actuator state.

### EXTERNAL SERVICES CONNECTIONS
The Simulator container does not connect to external services from the project code. It is itself an external prebuilt image used by the platform.

### MICROSERVICES:

#### MICROSERVICE: simulator
- TYPE: backend
- DESCRIPTION: External simulator image that exposes REST endpoints for sensors, telemetry topics, health status, and actuator commands.
- PORTS: 8080
- TECHNOLOGICAL SPECIFICATION:
The service is provided as the Docker image `mars-iot-simulator:multiarch_v1`. Its source code is not included in the repository, but it is consumed through HTTP endpoints by the ingestion, processing, and backend services.
- SERVICE ARCHITECTURE:
The simulator works as an external data source and actuator target for the whole platform. Other services poll its sensor endpoints, retrieve available telemetry topics, and send actuator state changes back to it.

- ENDPOINTS:

	| HTTP METHOD | URL | Description | User Stories |
	| ----------- | --- | ----------- | ------------ |
    | GET | /health | Returns simulator health status | 15 |
    | GET | /api/sensors | Returns the list of available sensors | 10, 17 |
    | GET | /api/sensors/{sensor_id} | Returns the latest value for a specific sensor | 10, 13, 18 |
    | GET | /api/telemetry/topics | Returns available telemetry topics | 17 |
    | GET | /api/actuators | Returns current actuator states | 9, 17 |
    | POST | /api/actuators/{actuator_id} | Sets the state of a specific actuator | 11, 12 |

## CONTAINER_NAME: Ingestion

### DESCRIPTION:
Collects telemetry from the simulator, normalizes sensor payloads, and republishes them to the broker using STOMP topics.

### USER STORIES:
9) As the User I want to see the current active actuators
10) As the User I want to see the current active sensors
13) As the User I want to visualize charts regarding current data from sensors
15) As the User I want to see how much time has passed since the latest update
17) As the User I want to see the number of sensors, live telemetries, active rules and actuators currently on.
18) As the User I want to see which sensors are in warning status

### PORTS:
No published ports

### PERSISTENCE EVALUATION
The Ingestion container does not require persistent storage. It performs transient collection and normalization of live data.

### EXTERNAL SERVICES CONNECTIONS
The Ingestion container connects to the Simulator through HTTP and to the Broker through STOMP.

### MICROSERVICES:

#### MICROSERVICE: ingestion-service
- TYPE: backend
- DESCRIPTION: Polls sensor endpoints and telemetry topic lists from the simulator, normalizes raw telemetry, and publishes it to broker topics under the Mars namespace.
- PORTS: none
- TECHNOLOGICAL SPECIFICATION:
The microservice is developed in Python. It uses `requests` for HTTP communication with the simulator and `stomp.py` for broker communication. Its configuration defines the simulator URL, broker host, credentials, and polling interval.
- SERVICE ARCHITECTURE:
The service is organized into multiple modules:
    - `main.py` starts the ingestion loops.
    - `simulator_client.py` retrieves sensors and telemetry topics from the simulator.
    - `workers.py` handles polling and publishing tasks.
    - `normalization.py` transforms raw simulator payloads into a common structure.
    - `broker.py` manages STOMP broker connections.
    - `config.py` centralizes runtime configuration.

## CONTAINER_NAME: Broker

### DESCRIPTION:
Acts as the messaging backbone of the platform. It receives normalized sensors and telemetry from the ingestion service and distributes it to backend consumers.

### USER STORIES:
8) As a User, I want to see which sensors violate the rules.
9) As the User I want to see the current active actuators
10) As the User I want to see the current active sensors
13) As the User I want to visualize charts regarding current data from sensors
15) As the User I want to see how much time has passed since the latest update
17) As the User I want to see the number of sensors, live telemetries, active rules and actuators currently on.
18) As the User I want to see which sensors are in warning status
20) As a User, I want to be notified when a rule has been broken, a violation has been resolved and when rules have been modified.

### PORTS:
61616:61616
1883:1883
61613:61613
8161:8161

### PERSISTENCE EVALUATION
The Broker container is not used in the project as a persistent data store. Its role is transient message routing among services.

### EXTERNAL SERVICES CONNECTIONS
The Broker container does not connect to external services. It is used internally by ingestion, processing, and backend services.

### MICROSERVICES:

#### MICROSERVICE: broker
- TYPE: middleware
- DESCRIPTION: Message broker used for asynchronous communication among the services.
- PORTS: 61616, 1883, 61613, 8161
- TECHNOLOGICAL SPECIFICATION:
The platform uses the Docker image `apache/activemq-artemis:latest-alpine`. The configuration enables anonymous login and exposes ports for different messaging protocols, including STOMP.
- SERVICE ARCHITECTURE:
The broker receives normalized Mars telemetry and sensors from the ingestion service and allows the processing service and backend service to subscribe to the corresponding topics.

## CONTAINER_NAME: Processing

### DESCRIPTION:
Evaluates automation rules against incoming telemetry and sensors, and issues actuator commands when rule conditions are satisfied.

### USER STORIES:
None

### PORTS:
No published ports

### PERSISTENCE EVALUATION
The Processing container does not maintain its own persistent storage, but it depends on the database container to load persisted automation rules.

### EXTERNAL SERVICES CONNECTIONS
The Processing container connects to the Broker through STOMP, to the Database through MySQL, and to the Simulator through HTTP to send actuator commands.

### MICROSERVICES:

#### MICROSERVICE: processing_service
- TYPE: backend
- DESCRIPTION: Subscribes to telemetry topics, reads enabled rules from the database, evaluates them against incoming sensor values, and commands actuators according to the consensus decision.
- PORTS: none
- TECHNOLOGICAL SPECIFICATION:
The microservice is developed in Python. It uses `stomp.py` for broker subscriptions, `mysql-connector-python` for database access, and `requests` for sending actuator commands to the simulator.
- SERVICE ARCHITECTURE:
The service is organized into several modules:
    - `main.py` manages broker connection and subscription.
    - `engine.py` parses telemetry messages and evaluates automation logic.
    - `database.py` retrieves enabled rules from MariaDB.
    - `simulator_client.py` sends actuator commands.
    - `models.py` defines the internal telemetry dataclass.
    - `config.py` contains broker, database, and operator configuration.

## CONTAINER_NAME: Gateway

### DESCRIPTION:
Provides the REST API and server-side event stream used by the frontend dashboard. It exposes rule management, actuator control, health monitoring, event logging, and access to the latest sensor state.

### USER STORIES:
1) As the User I want to see all the rules in a compact way
2) As the User I want to add a new rule
3) As the User I want to remove an existing rule
4) As the User I want to modify an existing rule
5) As the User I want to enable/disable an existing rule
6) As the User I want to reset the rules
7) As the User I want to save all rules persistently
8) As a User, I want to see which sensors violate the rules.
9) As the User I want to see the current active actuators
10) As the User I want to see the current active sensors
11) As the User I want to manually turn on/off a specific actuator
12) As the User I want to reset all actuators to off
15) As the User I want to see how much time has passed since the latest update
17) As the User I want to see the number of sensors, live telemetries, active rules and actuators currently on.
20) As a User, I want to be notified when a rule has been broken, a violation has been resolved and when rules have been modified.

### PORTS:
8000:8000

### PERSISTENCE EVALUATION
The Gateway container keeps transient in-memory caches for latest sensor data, event logs, and actuator state, but relies on the database container for persistent storage of automation rules.

### EXTERNAL SERVICES CONNECTIONS
The Gateway container connects to the Broker through STOMP, to the Database through MySQL, and to the Simulator through HTTP for actuator state synchronization.

### MICROSERVICES:

#### MICROSERVICE: backend
- TYPE: backend
- DESCRIPTION: Main application API that serves dashboard data, manages rules, exposes event streams, and forwards actuator commands to the simulator.
- PORTS: 8000
- TECHNOLOGICAL SPECIFICATION:
The microservice is developed in Python using FastAPI. It uses:
    - `fastapi` for REST endpoints and SSE streaming
    - `uvicorn` as ASGI server
    - `stomp.py` for broker subscription
    - `mysql-connector-python` for MariaDB access
    - `requests` for HTTP communication with the simulator
    - `pydantic` for request validation
- SERVICE ARCHITECTURE:
The service is organized into several functional modules to ensure separation of concerns and maintainability:
    - `main.py`: The entry point of the application; it initializes the FastAPI instance, includes the API routers, and orchestrates the startup/shutdown of background services.
    - `workers.py`: Manages the asynchronous background tasks, specifically the STOMP broker connection, message subscription, and the continuous ingestion loop for incoming data.
    - `database.py`: Handles all interactions with the MariaDB database.
    - `state.py`: Manages the global in-memory state of the habitat, storing the latest normalized metrics, current actuator statuses, and the rolling event log for the dashboard.
    - `models.py`: Defines the standardized schemas and internal dataclasses.
    - `config.py`: Centralizes all environment variables and constant settings, such as connection strings for the Broker, Database, and Simulator API.
 The Gateway also reads default rules from `default_rules.json` when the user requests a reset.

- ENDPOINTS:

	| HTTP METHOD | URL | Description | User Stories |
	| ----------- | --- | ----------- | ------------ |
    | GET | /api/health | Returns backend health information and dashboard counters | 15, 17 |
    | GET | /api/stream/dashboard | Streams dashboard updates through Server-Sent Events | 15, 20 |
    | GET | /api/latest | Returns the latest cached sensor metrics | 10, 13, 18 |
    | GET | /api/latest/{sensor_id} | Returns latest metrics for a specific sensor | 10, 13, 18 |
    | GET | /api/events | Returns the recent event log | 8, 20 |
    | GET | /api/actuators | Returns current actuator states | 9, 17 |
    | POST | /api/actuators/reset | Resets all known actuators to OFF | 12 |
    | POST | /api/actuators/{actuator_id} | Manually sets the state of an actuator | 11 |
    | GET | /api/rules | Returns all automation rules | 1 |
    | POST | /api/rules | Creates a new automation rule | 2 |
    | PUT | /api/rules/{rule_id} | Updates an existing automation rule | 4, 5 |
    | DELETE | /api/rules/{rule_id} | Deletes an existing automation rule | 3 |
    | POST | /api/rules/reset | Resets rules to the backend default set | 6 |

## CONTAINER_NAME: Database

### DESCRIPTION:
Stores the automation rules used by the system and initializes the Mars Habitat Control database schema.

### USER STORIES:
2) As the User I want to add a new rule
3) As the User I want to remove an existing rule
4) As the User I want to modify an existing rule
5) As the User I want to enable/disable an existing rule
6) As the User I want to reset the rules
7) As the User I want to save all rules persistently

### PORTS:
No published application port in the compose file

### PERSISTENCE EVALUATION
The Database container is the main persistence layer of the platform. It stores the automation rules in MariaDB and mounts `./db/data` to preserve data across container restarts.

### EXTERNAL SERVICES CONNECTIONS
The Database container does not connect to external services. It is used internally by the backend and processing services.

### MICROSERVICES:

#### MICROSERVICE: db
- TYPE: database
- DESCRIPTION: MariaDB instance used to persist automation rules and initialize the database schema at startup.
- PORTS: internal MariaDB port
- TECHNOLOGICAL SPECIFICATION:
The microservice uses the Docker image `mariadb:latest`. Initialization is performed through the SQL script `db/init.sql`, while persistent data is stored in the mounted `/var/lib/mysql` volume.
- SERVICE ARCHITECTURE:
The database is initialized at container startup. It creates the `mars_iot` schema, the application user, and the `automation_rules` table, then inserts an initial set of default rules.

- DB STRUCTURE:

	**_automation_rules_** : | **_id_** | sensor_name | metric_name | operator | threshold | actuator_name | action_value | enabled |

## CONTAINER_NAME: Frontend

### DESCRIPTION:
Provides the web dashboard used by the user to monitor the habitat, manage rules, inspect alerts, visualize charts, and control actuators.

### USER STORIES:
1) As the User I want to see all the rules in a compact way
2) As the User I want to add a new rule
3) As the User I want to remove an existing rule
4) As the User I want to modify an existing rule
5) As the User I want to enable/disable an existing rule
6) As the User I want to reset the rules
8) As a User, I want to see which sensors violate the rules.
9) As the User I want to see the current active actuators
10) As the User I want to see the current active sensors
11) As the User I want to manually turn on/off a specific actuator
12) As the User I want to reset all actuators to off
13) As the User I want to visualize charts regarding current data from sensors
14) As the User I want to visualize related sensors near to each other
15) As the User I want to see how much time has passed since the latest update
16) As the User I want to visualize dangerous conditions as red
17) As the User I want to see the number of sensors, live telemetries, active rules and actuators currently on.
18) As the User I want to see which sensors are in warning status
19) As the User I want to directly access the alert section by clicking on a single button
20) As a User, I want to be notified when a rule has been broken, a violation has been resolved and when rules have been modified.

### PORTS:
3000:80

### PERSISTENCE EVALUATION
The Frontend container does not store persistent application data. It is a static web interface that consumes the backend API.

### EXTERNAL SERVICES CONNECTIONS
The Frontend container connects to the Backend API through HTTP and Server-Sent Events.

### MICROSERVICES:

#### MICROSERVICE: frontend
- TYPE: frontend
- DESCRIPTION: Single-page dashboard for monitoring telemetry, managing automation rules, viewing alerts, and controlling actuators.
- PORTS: 80 inside the container, published as 3000 on the host
- TECHNOLOGICAL SPECIFICATION:
The frontend is implemented as a static web application served through Nginx. It uses HTML, CSS, and vanilla JavaScript. The interface includes rule tables, grouped sensor cards, chart visualization, alert/event areas, actuator controls, and overview counters.
- SERVICE ARCHITECTURE:
The frontend is composed of:
    - `index.html` for dashboard structure and UI sections
    - `style.css` for the visual theme and component styling
    - `app.js` for API integration, SSE updates, chart rendering, rule management, and actuator interactions
    - a static Mars favicon/icon asset

- PAGES:

	| Name | Description | Related Microservice | User Stories |
	| ---- | ----------- | -------------------- | ------------ |
    | index.html | Main dashboard page containing overview cards, rules section, alerts, sensor groups, actuator controls, and chart area | backend | 1, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20 |
    | app.js | Client-side logic for loading dashboard data, handling SSE, managing rules, showing notifications, and updating UI state | backend | 1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12, 13, 15, 17, 19, 20 |
    | style.css | Presentation layer for dashboard layout, status highlighting, red warning states, and responsive grouping of sensors | frontend | 14, 16, 18 |
