#### Start Kafka broker
```bash
cd kafka
docker compose up
```

### Start Kafka Stream Processor
```bash
cd cep_engine/aggregate
docker build -t cep_aggregate .
docker run --network=host --name cep_aggregate cep_aggregate
```
```bash
cd cep_engine/raw_alert
docker build -t cep_raw_alert .
docker run --network=host --name cep_raw_alert cep_raw_alert
```
```bash
cd cep_engine/agg_alert
docker build -t agg_alert .
docker run --network=host --name agg_alert agg_alert
```

### Build Producer and Produce Events
```bash
cd capture_daemon
docker build -t capture_daemon .
docker run --network=host --name capture_daemon capture_daemon
```