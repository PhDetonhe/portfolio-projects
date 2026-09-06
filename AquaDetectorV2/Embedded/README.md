# AquaDetector Embedded

Runtime Python para a Raspberry Pi (e para validação com webcam no computador).
Ele captura um único frame a cada intervalo, executa o modelo YOLO, cria um
evento JSON, grava-o em uma fila local durável e tenta publicá-lo ao backend.
Não há acesso direto ao MongoDB.

## Preparação

1. Instale as dependências: `pip install -r Embedded/requirements.txt`.
2. Coloque o modelo treinado em `Embedded/models/yolo26n.pt` ou defina
   `AQUADETECTOR_MODEL_PATH` com o caminho absoluto do arquivo `.pt`.
3. Copie os valores de `Embedded/.env.example` para o ambiente do serviço
   (ou exporte as variáveis equivalentes). Ajuste principalmente
   `AQUADETECTOR_BACKEND_URL` para o endpoint que receberá eventos.
4. Na raiz do repositório, execute `python -m Embedded.main`.

O primeiro ciclo é executado imediatamente; os demais respeitam
`AQUADETECTOR_DETECTION_INTERVAL`, cujo padrão é 3600 segundos (60 minutos).
A câmera é aberta somente durante a captura e liberada logo depois. O modelo é
carregado na primeira inferência e fica residente, sem processamento contínuo.

## Evento e sincronização

Os arquivos da fila local são um JSON por evento. Um evento só é removido após
uma resposta HTTP 2xx. Ao iniciar e após cada detecção, a fila pendente é
reenviada em ordem. Assim, a indisponibilidade de rede não perde detecções.

O backend deve aceitar `POST` no endereço configurado, com o JSON que contém
`station_id`, contadores de todas as classes, confiança média e detalhes de
cada detecção. As classes aceitas nesta versão são `bottle`, `can`, `carton`,
`paper` e `plastic`.
