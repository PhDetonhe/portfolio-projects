# Sistema embarcado — Raspberry Pi

Esta pasta reúne exclusivamente os componentes que executam na estação Raspberry Pi do AquaDetector. Os arquivos foram apenas reorganizados por responsabilidade; o conteúdo dos códigos e das configurações não foi alterado.

## Estrutura

```text
RaspberryPi/
├── camera/             # Abertura e parâmetros da webcam USB
├── communication/      # Cliente HTTP para comunicação com o backend
├── config/             # Configuração da estação e dependências Python
├── data/               # Contagem local de resíduos
├── detection/          # Detectores YOLO e SSD MobileNet
├── gps/                # Leitura do módulo GPS NEO-6M pela UART
├── models/             # Pesos e arquivos dos modelos de visão computacional
├── monitoring/         # Processos principais de monitoração e detecção
├── runtime/            # Artefatos temporários gerados pelo Python
├── station/            # Documento local e atualização de localização da estação
└── tracking/           # Rastreamento de objetos e contagem por cruzamento de linha
```

## Componentes

- `camera/webcam_config.py`: configura e abre a câmera usada pela estação.
- `communication/backend_client.py`: envia eventos de detecção para a API.
- `config/raspberrypi_config.json`: concentra parâmetros da estação, GPS, câmera, backend e detectores.
- `config/requirements.txt`: dependências Python do ambiente embarcado.
- `detection/`: implementações dos detectores YOLO e SSD MobileNet.
- `gps/gps_neo6m.py`: recebe e interpreta dados NMEA do GPS NEO-6M.
- `monitoring/`: pontos de entrada para os monitores com YOLO e SSD MobileNet.
- `station/`: mantém o documento da estação e atualiza sua posição com o GPS.
- `tracking/line_tracker.py`: acompanha objetos e identifica cruzamentos da linha de contagem.

## Dados e modelos

- `models/best (1).pt` é o peso YOLO disponível atualmente.
- Modelos SSD MobileNet devem ficar em `models/ssd_mobilenet/`, conforme definido na configuração.
- `data/contagem_residuos.json` guarda a contagem local persistida.
- `station/station.json` guarda o documento local da estação, com localização em GeoJSON (`[longitude, latitude]`).

`runtime/__pycache__/` contém cache gerado automaticamente pelo Python e pode ser recriado quando necessário.

## Execução

Os módulos devem ser executados a partir da raiz do projeto, usando o formato de pacote Python. Assim, os imports entre as pastas e todos os caminhos de configuração são resolvidos corretamente.

```bash
pip install -r RaspberryPi/config/requirements.txt
python -m RaspberryPi.monitoring.monitor_residuos
```

Alternativas disponíveis:

```bash
python -m RaspberryPi.monitoring.monitor_ssd_mobilenet
python -m RaspberryPi.station.update_station_location
```
