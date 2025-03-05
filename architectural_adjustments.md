# High-Level Architecture Description
To handle 1000 URLs per minute we need to implement an event-driven architecture with message queues and scalable workers.

## Proposed Architecture Components:
### Queue System (Kafka, RabbitMQ, or Redis Streams)

Acts as a buffer to handle spikes in traffic.

Ensures messages are processed asynchronously.

### Database

Stores processed URLs with timeouts and depth.

### Scaling Mechanism

Auto-scaling based on queue size.
For example Kubernetes (K8s) with Horizontal Pod Autoscaler (HPA).

### Workers

Each worker pulls URLs from the queue.

Workers process URLs in parallel using asyncio.

As of now, the script takes home page from a given URL and scan all the links with depth for a given URL within internal async query.
To optimize auto-scaling based on queue size, I recommend using a centralized queue, such as Kafka, to store URL and depth tuples. This approach consolidates all URLs in one location, simplifying both processing and monitoring.

For storing URLs and timestamps, we’ll initially save this data to a database table. A dedicated worker will then read the data from the database and write it to a file. The frequency of file creation can be tailored to specific needs, such as generating a new file every day.
These files can be stored on external storage, such as an SFTP server, ensuring easy access for further processing or retrieval.

### Monitoring & Logging

Use monitoring and dashboard tools for example Prometheus + Grafana.

## Fault Tolerance

Retry Mechanism: If a worker fails, messages remain in the queue for reprocessing.

Dead Letter Queue (DLQ): Failed messages after multiple retries are sent here for debugging.

## Other things to pay attention on

### avoid scanning the same URL in a short period of time

To prevent scanning the same URL within a short period, we can store the URLs and timestamps in a database. By implementing a time window (e.g., 7 days), we can check if a URL is already in the queue. If it appears again within this period, it will be skipped to avoid re-scanning.

### adding regexes to ignore some of the links

Enhance the script by adding regular expressions (regex) to filter out certain links. This will help prevent scanning pages from the same resource or domain, ensuring only relevant URLs are processed.

### clean db data

Create a cron job to clean history data in the database for some period.

### prevent blocking

To prevent blocking, analyze broken links and implement measures such as using proxy servers for requests. Additionally, introduce timeouts between requests to the same domain to avoid overloading or triggering rate-limiting mechanisms.
