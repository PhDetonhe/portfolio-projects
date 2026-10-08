// Aquisição CNC no Opta: somente entradas, sem controle de relés.
#include <Arduino.h>
#include "config.h"

const char* ler(int pin, bool ativo) {
  return pin < 0 ? "null" : digitalRead(pin) == ativo ? "true" : "false";
}
unsigned long ultimo = 0;
uint32_t seq = 0;
char frame[600];
size_t posicao = 0, tamanho = 0;

void setup() {
  Serial.begin(115200);
  const int pins[] = {PIN_24V, PIN_CICLO, PIN_ALARME, PIN_EMERGENCIA};
  for (int pin : pins) if (pin >= 0) pinMode(pin, INPUT);
}

void loop() {
  if (posicao == tamanho && millis() - ultimo >= 500) {
    ultimo = millis();
    int n = snprintf(frame, sizeof(frame),
      "CNC_JSON:{\"device_id\":\"%s\",\"sequencia\":%lu,\"uptime_ms\":%lu,"
      "\"machine_active\":%s,\"voltage_24v\":%s,"
      "\"digital_signals\":{\"ciclo\":%s,\"alarme\":%s,\"emergencia\":%s},"
      "\"analog_signals\":{},\"extra_signals\":{\"source\":\"cnc_opta\",\"simulation\":false}}",
      DEVICE_ID, (unsigned long)++seq, ultimo,
      ler(PIN_24V, ATIVO_24V), ler(PIN_24V, ATIVO_24V),
      ler(PIN_CICLO, ATIVO_CICLO), ler(PIN_ALARME, ATIVO_ALARME), ler(PIN_EMERGENCIA, ATIVO_EMERGENCIA));
    tamanho = n > 0 && (size_t)n < sizeof(frame) ? n : 0;
    posicao = 0;
  }
  // O USB do core Mbed não fornece capacidade útil em availableForWrite().
  // Escrita USB pode bloquear: este sketch não controla a CNC.
  if (Serial && posicao < tamanho) {
    size_t count = tamanho - posicao;
    if (count > 32) count = 32;
    Serial.print("CNC_CHUNK:");
    Serial.write((const uint8_t*)frame + posicao, count);
    Serial.println();
    posicao += count;
  }
}
