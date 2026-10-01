# Food Storage Room – Auto Temperature Control (Docker)

## Chalano
1. Docker Desktop open kore running koro.
2. `start.bat` double-click kro (build + start + browser open, sob auto), othoba CMD te:
   ```
   cd food-storage-temp
   docker compose up -d --build
   ```
   Container prothome off thake; ei command dile tobei localhost:8080 on hoy. Docker/PC restart dileo auto-start hoy na.
3. Browser: http://localhost:8080
4. Bondho: `stop.bat` othoba `docker compose down`

## Kivabe kaj kore
- Controller (hysteresis): temp > target+band hole COOLER ON, < target-band hole HEATER ON, target e pouchale OFF.
- Default mode `sim`: room-er thermal simulation chole, tai hardware charao demo dekha jay.
- Alarm: temp limit er baire gele / sensor 30s data na dile.
- Log: `data/log.csv` (container restart holeo thake).

## Real hardware (optional)
- Sensor (ESP32+DS18B20/DHT22 ityadi) theke POST koro: `POST http://<laptop-ip>:8080/api/sensor` body `{"temp":21.4,"hum":55}` ; mode `real` koro.
- Relay/smart plug control: `ACTUATOR_URL` e webhook URL dao; state change hole `{"cooler":true,"heater":false}` POST hobe.
- Laptop er nijer kono temperature/relay pin nai, tai real use e external sensor+relay lagbe.
- Settings docker-compose.yml e change kore `docker compose up -d --build`.

## API
GET /api/status | GET /api/log | POST /api/config | POST /api/sensor
