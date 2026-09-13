# Raspberry Pi

## Documento da estação

`station.json` contém somente o documento da estação no formato solicitado:
`_id`, `station_id`, `detections`, `status`, `location` (GeoJSON Point) e
`administrative`. Como `ObjectId(...)` não é JSON válido, `_id` usa MongoDB
Extended JSON: `{ "$oid": "..." }`. GeoJSON usa sempre `[longitude, latitude]`.

## GPS NEO-6M

O projeto é Python; não é necessário C++. Conecte o NEO-6M à UART da Raspberry
(TX do GPS → RX da Pi, GND comum) e habilite a serial no `raspi-config` sem
console serial. Ajuste `gps.serial_port` se necessário, normalmente
`/dev/serial0`, e execute:

```bash
pip install -r requirements.txt
python update_station_location.py
```

O leitor aceita frases NMEA RMC e GGA e só grava uma posição quando há fix
válido. O script não acessa backend, dashboard nem altera o fluxo YOLO.

## Detectores

O YOLO existente permanece em `monitor_residuos.py`:

```bash
export AQUADETECTOR_API_URL=http://192.168.1.10:8000
python monitor_residuos.py
```

`monitor_ssd_mobilenet.py` é uma alternativa separada que reutiliza o mesmo
`LineTracker`, contador local e evento HTTP. Coloque um modelo TensorFlow
congelado em `models/ssd_mobilenet/` e ajuste os caminhos em
`raspberrypi_config.json`. Para um modelo personalizado, crie `labels.txt` com
uma linha por classe no formato `id nome` (por exemplo, `1 bottle`). Um modelo
SSD MobileNet COCO padrão detecta apenas `bottle` entre as cinco classes do
projeto; para `can`, `carton`, `paper` e `plastic`, use SSD MobileNet treinado
com essas classes.
