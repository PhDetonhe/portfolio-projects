function setText(id, value) {
    const el = document.getElementById(id);

    if (el) {
        el.textContent = value;
    }
}

let mediaRecorder = null;
let audioChunks = [];
let gravando = false;
let streamAtual = null;

async function alternarEscuta() {

    console.log("Clique microfone");

    if (!gravando) {

        try {

            streamAtual =
                await navigator.mediaDevices.getUserMedia({
                    audio: true
                });

            console.log("Microfone autorizado");

            mediaRecorder =
                new MediaRecorder(streamAtual);

            audioChunks = [];

            mediaRecorder.ondataavailable =
                (event) => {

                if (event.data.size > 0) {
                    audioChunks.push(event.data);
                }
            };

            mediaRecorder.onstop =
                async () => {

                console.log("Gravação finalizada");

                const audioBlob =
                    new Blob(audioChunks, {
                        type: "audio/webm"
                    });

                const formData =
                    new FormData();

                formData.append(
                    "audio",
                    audioBlob,
                    "audio.webm"
                );

                setText(
                    "ia-status",
                    "🤔 Transcrevendo..."
                );

                try {

                    const response =
                        await fetch("/audio", {
                            method: "POST",
                            body: formData
                        });

                    const data =
                        await response.json();

                    console.log(data);

                    if (data.ok) {

                        setText(
                            "ia-pergunta",
                            data.texto
                        );

                        setText(
                            "ia-resposta",
                            data.resposta
                        );

                        setText(
                            "ia-status",
                            "✅ Pronto"
                        );

                        falar(data.resposta);

                    } else {

                        console.log(data.erro);

                        setText(
                            "ia-status",
                            "❌ Erro"
                        );
                    }

                } catch (error) {

                    console.error(error);

                    setText(
                        "ia-status",
                        "❌ Falha"
                    );
                }

                if (streamAtual) {

                    streamAtual
                        .getTracks()
                        .forEach(track =>
                            track.stop()
                        );
                }
            };

            mediaRecorder.start();

            gravando = true;

            document
                .getElementById("listen-pill")
                .textContent =
                    "🎤 Ouvindo...";

            document
                .getElementById(
                    "toggle-listen-button"
                )
                .querySelector(
                    ".voice-button-text"
                )
                .textContent =
                    "Clique para parar";

        } catch (error) {

            console.error(
                "Erro microfone:",
                error
            );

            alert(
                "Permita acesso ao microfone."
            );
        }

    } else {

        gravando = false;

        mediaRecorder.stop();

        document
            .getElementById("listen-pill")
            .textContent =
                "🤔 Processando...";

        document
            .getElementById(
                "toggle-listen-button"
            )
            .querySelector(
                ".voice-button-text"
            )
            .textContent =
                "Toque para falar comigo";
    }
}

function limparTextoFalado(texto) {

    return texto
        .replace(/²/g, " ao quadrado ")
        .replace(/\+/g, " mais ")
        .replace(/\-/g, " menos ")
        .replace(/\//g, " dividido por ")
        .replace(/\*/g, " vezes ")
        .replace(/=/g, " igual a ");
}

function falar(texto) {

    speechSynthesis.cancel();

    const textoLimpo =
        limparTextoFalado(texto);

    const fala =
        new SpeechSynthesisUtterance(
            textoLimpo
        );

    fala.lang = "pt-BR";

    fala.rate = 1;

    speechSynthesis.speak(fala);
}

document
    .getElementById(
        "toggle-listen-button"
    )
    .addEventListener(
        "click",
        alternarEscuta
    );

    document
    .getElementById(
        "encerrar-atendimento-button"
    )
    .addEventListener(
        "click",
        async function(event) {

            event.preventDefault();
            event.stopPropagation();

            console.log(
                "ENCERRAMENTO SOLICITADO"
            );

            try {

                const response =
                    await fetch(
                        "/solicitar_encerramento",
                        {
                            method: "POST"
                        }
                    );

                const data =
                    await response.json();

                console.log(data);

                setText(
                    "ia-status",
                    "🛑 Encerrando atendimento..."
                );

            } catch (error) {

                console.error(
                    "ERRO ENCERRAMENTO:",
                    error
                );

            }
        }
    );