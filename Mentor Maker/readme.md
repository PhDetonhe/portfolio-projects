VISÃO GERAL DO SISTEMA

Seu projeto é basicamente isso:

ESP32 → Flask (servidor) → Pepper (robô) → IA → resposta → tablet

Fluxo real:

ESP32 detecta grupo → manda pro servidor
Flask organiza fila/prioridade
Pepper pede próximo grupo (/next)
Pepper vai até o grupo
Aluno fala → Pepper escuta (ASR)
Pepper envia frase pra IA (/pergunta)
IA responde
Pepper fala resposta
Atendimento encerra → Pepper volta pra base
🧰 O QUE VOCÊ PRECISA INSTALAR (DO ZERO)
💻 1. Sistema operacional
Windows 10/11 (ok)
Ou Linux (melhor, mas opcional)
🐍 2. Python

Instale:

Python 3.10 ou 3.11 (não usa 3.12, pode dar dor de cabeça)

👉 Marcar:
✔ Add to PATH

📦 3. Bibliotecas Python

No terminal:

pip install flask requests

Se quiser garantir:

pip install flask requests urllib3
🌐 4. Servidor Flask

Seu arquivo:

server.py

Rodar:

python server.py

Tem que aparecer:

Running on http://0.0.0.0:5000
🤖 5. Pepper (NAOqi / Choregraphe)

Você precisa:

Choregraphe instalado
Conectar no IP do Pepper
Rodar seu script Python dentro dele

Serviços usados:

ALMotion
ALTextToSpeech
ALSpeechRecognition
ALMemory
ALTabletService
📡 6. Rede (MUITO IMPORTANTE)

Tudo precisa estar na mesma rede Wi-Fi:

Dispositivo	Deve acessar
Notebook	localhost:5000
Pepper	IP_DO_NOTEBOOK:5000
ESP32	IP_DO_NOTEBOOK:5000
🔥 7. Descobrir seu IP

No Windows:

ipconfig

Procure:

IPv4 Address: 192.168.x.x

E coloque aqui no Pepper:

self.base_url = "http://192.168.x.x:5000"
📁 ESTRUTURA DE PASTAS
/projeto
│
├── server.py
├── templates/
│   ├── index.html
│   └── dashboard.html
│
├── static/
│   ├── home.js
│   └── style.css
│
└── pepper/
    └── scriptComTablet.py
⚙️ FLUXO COMPLETO (DETALHADO)
🟡 1. ESP32

Ele chama:

/update?grupo=1&nivel=2&urgente=0

Servidor:

adiciona na fila
define prioridade
🔵 2. Pepper pede próximo grupo

Loop chama:

/next

Servidor responde:

{ "grupo": 1 }

E muda:

modo = "indo"
🟢 3. Pepper se move

Função:

ir_para_grupo()

Ele:

anda no corredor
vira
anda até o grupo
🟣 4. Atendimento começa

Pepper chama:

/atendimento_start?grupo=1

Servidor:

modo = "atendendo"
🎤 5. Reconhecimento de voz

Modo livre:

self.asr.setVocabulary([], True)

Sistema:

vai acumulando palavras
detecta silêncio (5s)
monta frase completa
🧠 6. Pergunta vai pra IA
POST /pergunta

Servidor:

chama OpenRouter
gera resposta
fallback se der erro
🗣️ 7. Pepper responde
tts.say(resposta)
🔴 8. Encerramento

Agora você tem DOIS caminhos:

✔ Automático (após resposta)

Pepper chama:

/encerrar_manual

Servidor:

modo = "voltando"
✔ Manual (botão no tablet)

Frontend chama:

POST /encerrar_manual
🔁 9. Pepper volta

Loop detecta:

modo == "voltando"

Executa:

voltar_base()
desfaz movimento
chega na base
chama:
POST /retorno_concluido

Servidor:

modo = "ouvindo"
⚠️ COISAS QUE VOCÊ PRECISA TESTAR ANTES DA COMPETIÇÃO
🔥 CRÍTICO
1. Rede
Pepper acessa o servidor?
ESP32 acessa?

👉 Testa no navegador do Pepper:

http://IP:5000
2. IA funcionando
API KEY válida?
resposta vem?
3. Movimento
distâncias corretas?
não bate em ninguém?
4. ASR (voz)
ambiente silencioso?
microfone ok?

👉 Se der ruim: usa botão + texto fixo

5. Botão encerrar
aparece?
chama endpoint?
💡 MELHORIAS RÁPIDAS (SE DER TEMPO)
🔹 Colocar timeout de atendimento
🔹 Melhorar prompt da IA
🔹 Mostrar pergunta no tablet
🔹 Adicionar som ao detectar voz

🧨 PROBLEMAS COMUNS
Problema	          Causa
Pepper não responde	  IP errado
IA não responde	      API key inválida
Não escuta	          ASR bugado
Não volta	          endpoint não chamado
Travando	          processando mal controlado

# ############################ #
PRA FUNCIONAR LLAMA CPP 

Git ✅
CMake ✅
C++ Build Tools ✅






-----------------------------------------------------------------------------------------------------------------------
// ============================================================
// ⚠️ CONFIGURAÇÕES QUE PRECISAM SER ALTERADAS NA COMPETIÇÃO
// ============================================================
//
// ─────────────────────────────────────────────────────────────
// [ESP32]
// ─────────────────────────────────────────────────────────────
//
// const char* ssid = "makerthon";
//
// ⚠️ ALTERAR:
// Nome da rede Wi-Fi da competição.
//
// Exemplo:
// const char* ssid = "SESI_EVENTO";
//
//
// ------------------------------------------------------------
//
// const char* password = "12345678";
//
// ⚠️ ALTERAR:
// Senha do Wi-Fi da competição.
//
// Exemplo:
// const char* password = "senha_evento";
//
//
// ------------------------------------------------------------
//
// const char* serverUrl = "http://192.168.137.59:5000/update";
//
// ⚠️ ALTERAR:
// IP do computador rodando o Flask.
//
// COMO DESCOBRIR:
// Windows CMD:
// ipconfig
//
// Procurar:
// "Endereço IPv4"
//
// Exemplo:
// 192.168.0.25
//
// Então ficará:
// const char* serverUrl = "http://192.168.0.25:5000/update";
//
//
// ------------------------------------------------------------
//
// #define GRUPO 1
//
// ⚠️ ALTERAR:
// Número do grupo da ESP atual.
//
// Exemplo:
// ESP do grupo 2:
// #define GRUPO 2
//
//
// ------------------------------------------------------------
//
// const int LED_PINS[NUM_LEDS] = {...}
//
// ⚠️ ALTERAR SOMENTE SE:
// - trocar fios
// - trocar GPIOs
// - mudar montagem da fita/LEDs
//
//
// ------------------------------------------------------------
//
// #define BOTAO_ENVIO 5
// #define BOTAO_URGENTE 18
// #define POT 34
//
// ⚠️ ALTERAR SOMENTE SE:
// os componentes forem ligados em outras portas.
//
//
// ------------------------------------------------------------
//
// const unsigned long timeoutLED = 10000;
//
// ⚠️ ALTERAR SE QUISER:
// tempo para apagar LEDs por inatividade.
//
// 10000 = 10 segundos
//
//
// ------------------------------------------------------------
//
// unsigned long sendCooldown = 3000;
//
// ⚠️ ALTERAR SE NECESSÁRIO:
// intervalo mínimo entre envios.
//
// 3000 = 3 segundos
//
// ============================================================
// ⚠️ CONFIGURAÇÕES DO PEPPER
// ============================================================
//
// self.base_url = "http://10.121.235.45:5000"
//
// ⚠️ ALTERAR:
// IP do computador rodando o Flask.
//
// MESMO IP usado no ESP32.
//
// Exemplo:
// self.base_url = "http://192.168.0.25:5000"
//
//
// ============================================================
// ⚠️ DISTÂNCIAS / MOVIMENTAÇÃO DO ROBÔ
// ============================================================
//
// DISTANCIA_CORREDOR = 1.5
//
// ⚠️ ALTERAR:
// distância até o ponto de decisão.
//
// Unidade:
// METROS
//
// Exemplo:
// corredor maior:
// DISTANCIA_CORREDOR = 2.0
//
//
// ------------------------------------------------------------
//
// DISTANCIA_FINAL = 1.5
//
// ⚠️ ALTERAR:
// distância do ponto de decisão até o grupo.
//
// Unidade:
// METROS
//
//
// ------------------------------------------------------------
//
// ANGULO_90 = 1.57
//
// ⚠️ NORMALMENTE NÃO PRECISA ALTERAR.
//
// 1.57 rad ≈ 90 graus
//
// MAS pode ajustar se:
// - Pepper estiver virando torto
// - piso escorregar
// - espaço da competição mudar
//
//
// ============================================================
// ⚠️ MAPEAMENTO DOS GRUPOS
// ============================================================
//
// if grupo == 1:
//     motion.moveTo(0, 0, -ANGULO_90)
//
// elif grupo == 2:
//     motion.moveTo(0, 0, ANGULO_90)
//
// ⚠️ ALTERAR SE:
// posição física dos grupos mudar.
//
// Exemplo:
// grupo 1 ficar à esquerda:
// trocar sinais.
//
//
// ============================================================
// ⚠️ OPENROUTER / IA
// ============================================================
//
// API_KEY = ""
//
// ⚠️ ALTERAR:
// chave da API OpenRouter.
//
// Exemplo:
// API_KEY = "sk-or-v1-xxxxxxxx"
//
//
// ------------------------------------------------------------
//
// "model": "openai/gpt-oss-120b"
//
// ⚠️ OPCIONAL:
// trocar modelo da IA.
//
// Exemplo:
// "openai/gpt-4.1-mini"
//
//
// ============================================================
// ⚠️ PORTA DO FLASK
// ============================================================
//
// app.run(host="0.0.0.0", port=5000)
//
// ⚠️ NORMALMENTE NÃO ALTERAR.
//
// Mas se a porta 5000 estiver ocupada:
//
// app.run(host="0.0.0.0", port=8000)
//
// E então mudar:
//
// ESP32:
// :8000/update
//
// Pepper:
// :8000
//
//
// ============================================================
// ⚠️ COISAS IMPORTANTES PRA TESTAR ANTES DA COMPETIÇÃO
// ============================================================
//
// ✅ Pepper conectado no mesmo Wi-Fi
// ✅ ESP32 conectando no Wi-Fi
// ✅ Flask rodando
// ✅ Firewall liberado
// ✅ IP correto
// ✅ Movimento calibrado
// ✅ Distâncias calibradas
// ✅ Microfone funcionando
// ✅ TTS funcionando
// ✅ Dashboard abrindo
// ✅ Botão urgente funcionando
// ✅ Fila funcionando
// ✅ Retorno à base funcionando
//
// ============================================================
// ⚠️ COMANDO RÁPIDO PRA PEGAR O IP
// ============================================================
//
// WINDOWS:
//
// ipconfig
//
// Procurar:
//
// Adaptador Wi-Fi
// Endereço IPv4
//
// Exemplo:
//
// IPv4: 192.168.0.25
//
// ============================================================