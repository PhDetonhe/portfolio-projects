# Raspberry Pi → backend

`raspberrypi_config.json` concentra a configuração. O `station_id` precisa
existir em `aquamonitor.stations`; os tipos aceitos são `bottle`, `can`,
`carton`, `paper` e `plastic`.

Na Raspberry, aponte para a máquina do backend antes de iniciar:

```bash
export AQUADETECTOR_API_URL=http://192.168.1.10:8000
python monitor_residuos.py
```

Na inicialização, o programa valida a conectividade e a estação por
`GET /api/stations`. Cada cruzamento envia `POST /api/detections` com
`event_id`, `station_id`, `detection_type`, `confidence`, `track_id` e
`detected_at`.
