"""Adapta os sinais das fontes existentes sem inventar medições."""
import math


def boolean(value):
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, int) and value in (0, 1):
        return bool(value)
    raise ValueError("sinal digital deve ser booleano ou null")


def normalize(body):
    if not isinstance(body, dict) or not body:
        raise ValueError("payload deve ser um objeto não vazio")
    if not any(k in body for k in ('dispositivo', 'device_id', 'esp_id')):
        raise ValueError("dispositivo ausente")
    if not any(k in body for k in ('digital_signals', 'entradas', 'digital_signal', 'motor1_on', 'motor_on')):
        raise ValueError("sinais ausentes")
    for name in ('digital_signals', 'analog_signals', 'extra_signals', 'entradas', 'saidas', 'contadores'):
        if name in body and not isinstance(body[name], dict):
            raise ValueError(f"{name} deve ser um objeto")
    data = dict(body)
    data['device_id'] = str(body.get('device_id') or body.get('esp_id') or body.get('dispositivo'))
    if not 1 <= len(data['device_id']) <= 128:
        raise ValueError('identificação inválida')
    digital = dict(body.get('digital_signals', {}))
    if 'digital_signal' in body:
        digital.setdefault('ciclo', body['digital_signal'])
    elif 'motor1_on' in body or 'motor_on' in body:
        digital.setdefault('ciclo', boolean(body.get('motor1_on', body.get('motor_on'))) is True or boolean(body.get('motor2_on')) is True)
    for name in ('ciclo', 'alarme', 'emergencia'):
        digital[name] = boolean(digital.get(name))
    data['digital_signals'] = digital
    analog = dict(body.get('analog_signals', {}))
    if 'simulated_temperature_c' in body:
        analog.setdefault('temperature', body['simulated_temperature_c'])
    for value in analog.values():
        if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)):
            raise ValueError('medição analógica inválida')
    data['analog_signals'] = analog
    data['machine_active'] = boolean(body.get('machine_active'))
    data['voltage_24v'] = boolean(body.get('voltage_24v'))
    extra = dict(body.get('extra_signals', {}))
    if body.get('dispositivo') == 'opta1':
        extra.update(source='mesa_seletora_v2', simulation=True)
    elif 'esp_id' in body:
        extra.setdefault('source', 'esp32_digital')
    if 'simulated_temperature_c' in body:
        extra['temperature_simulated'] = True
    data['extra_signals'] = extra
    power = data['voltage_24v'] if data['voltage_24v'] is not None else data['machine_active']
    data['status'] = ('DESLIGADA' if power is False else
                      'EMERGENCIA' if digital['emergencia'] is True else
                      'ALARME' if digital['alarme'] is True else
                      'OPERANDO' if digital['ciclo'] is True else
                      'PARADA' if power is True and digital['ciclo'] is False else
                      'DESCONHECIDA')
    # Somente contadores concluídos; contadorTotal da V2 significa iniciadas.
    counts = body.get('contadores', {})
    if all(isinstance(counts.get(k), int) and not isinstance(counts[k], bool) and counts[k] >= 0 for k in ('reto', 'queda1', 'queda2')):
        extra['parts_count'] = sum(counts[k] for k in ('reto', 'queda1', 'queda2'))
    return data
