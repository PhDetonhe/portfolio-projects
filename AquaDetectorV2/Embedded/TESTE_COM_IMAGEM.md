# Teste do AquaDetector com uma imagem

Este guia testa o caminho completo sem webcam:

`imagem JPEG -> YOLO -> evento JSON -> FastAPI -> MongoDB -> dashboard`

O arquivo de imagem não é enviado para o banco. A aplicação usa a imagem apenas
para executar a inferência; o que é enviado é o JSON com as detecções e as
contagens.

## 1. O que é necessário

- Python 3.10 ou mais recente;
- MongoDB Community Server em execução;
- uma foto `.jpg` ou `.jpeg` com uma ou mais garrafas;
- um modelo Ultralytics YOLO em formato `.pt`, cujas classes usem os nomes
  `bottle`, `can`, `carton`, `paper` e/ou `plastic`.
- o projeto AquaMonitor.

Coloque o modelo em `Embedded/models/`. O nome pode ser `best.pt`.

## 2. Preparar o ambiente

Abra o PowerShell na pasta raiz do projeto e crie um ambiente virtual:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install fastapi "uvicorn[standard]" pymongo
pip install -r Embedded\requirements.txt
```

Se o PowerShell bloquear a ativação, execute os demais comandos com
`.\.venv\Scripts\python.exe` no lugar de `python`.

## 3. Iniciar e popular o MongoDB

Inicie o serviço **MongoDB Server** pelo aplicativo *Serviços* do Windows. Em
seguida, ainda na raiz do projeto, importe as estações de exemplo:

```powershell
mongoimport --db aquamonitor --collection stations --file stations.json --jsonArray
```

Esse comando deve ser executado uma única vez. A estação usada no teste será a
de ID `1`, que já existe nesse arquivo.

## 4. Iniciar o backend

Abra um segundo PowerShell na pasta do projeto, ative o ambiente virtual e
execute:

```powershell
cd backend
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

Deixe essa janela aberta. Para conferir se o backend responde, acesse
`http://127.0.0.1:8000/api/stations` no navegador. Uma lista de estações deve
aparecer.

## 5. Abrir o dashboard

Abra um terceiro PowerShell na raiz do projeto e execute:

```powershell
python -m http.server 5500 --directory dashboard
```

No navegador, abra `http://127.0.0.1:5500`. Deixe essa aba aberta.

## 6. Configurar o teste por imagem

Abra um quarto PowerShell na raiz do projeto, ative o ambiente virtual e defina
as variáveis apenas para esta janela:

```powershell
$env:AQUADETECTOR_MODEL_PATH = "Embedded/models/best.pt"
$env:AQUADETECTOR_BACKEND_URL = "http://127.0.0.1:8000/api/detections"
$env:AQUADETECTOR_STATION_ID = "1"
$env:AQUADETECTOR_CONFIDENCE_THRESHOLD = "0.40"
```

Troque `best.pt` pelo nome real do modelo, se necessário. Não use `localhost`
quando backend e detector estiverem em computadores diferentes: nesse caso,
use o IP ou domínio do computador que está executando o backend.

## 7. Analisar a foto e enviar o evento

Execute, trocando o caminho pela imagem de teste:

```powershell
python -m Embedded.analyze_image "C:\caminho\para\foto-com-garrafas.jpg"
```

O terminal exibirá o JSON gerado. Verifique principalmente as contagens por
classe em `residuos` e o total:

```json
"residuos": {
  "bottle": 1,
  "can": 0,
  "carton": 0,
  "paper": 0,
  "plastic": 0
},
"quantidade_total": 1
```

Ao fim, a mensagem `Evento enviado ao backend` confirma que o FastAPI aceitou
o evento. O terminal do backend também deve mostrar uma requisição `POST
/api/detections` com status `200`.

Para validar só a IA e o JSON, sem modificar o banco, acrescente `--no-send`:

```powershell
python -m Embedded.analyze_image "C:\caminho\para\foto.jpg" --no-send
```

## 8. Conferir no dashboard

Recarregue a página do dashboard. A estação de ID `1` deve mostrar uma
detecção adicional.

O backend atual incrementa o campo `detections` da estação em **1 para cada
evento de imagem aceito**, independentemente de quantas garrafas a IA encontrou
no JSON. O número individual de garrafas fica preservado em
`residuos.bottle` no evento salvo na coleção `detection_events`.

## Problemas comuns

- **`YOLO model was not found`**: confira o caminho em
  `AQUADETECTOR_MODEL_PATH` e se o arquivo `.pt` está em `Embedded/models/`.
- **A imagem gera tudo como `0`**: tente uma foto mais nítida, ajuste o limiar
  para `0.25` ou confirme que os nomes das classes do modelo são exatamente
  `bottle`, `can`, `carton`, `paper` ou `plastic`.
- **`Station not found` / erro 404**: importe `stations.json` ou use um
  `AQUADETECTOR_STATION_ID` existente.
- **`Could not send event`**: confirme que o backend está aberto na porta
  `8000` e que a URL da variável termina em `/api/detections`.
- **O dashboard não mudou**: recarregue a página; ele não atualiza os dados
  automaticamente.
