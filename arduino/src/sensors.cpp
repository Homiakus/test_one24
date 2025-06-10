/**
 * @file: sensors.cpp
 * @description: Модуль для работы с датчиками системы (ротор, отходы, концевые выключатели)
 * @dependencies: Arduino.h, config.h, stepper_control.h
 * @created: 2024-12-19
 */

#include "sensors.h"
#include "stepper_control.h"
#include <Arduino.h>

// Массив пинов ротора
const byte rotorPins[4] = ROTOR_PINS;

// Инициализация пинов датчиков
void initializeSensors() {
  // Датчик отходов
  pinMode(WASTE_PIN, INPUT_PULLUP);
  
  // Пины ротора
  for (int i = 0; i < 4; i++) {
    pinMode(rotorPins[i], INPUT_PULLUP);
  }
}

// Чтение состояния ротора
void readRotorState(char* stateBuffer) {
  for (int i = 0; i < 4; i++) {
    stateBuffer[i] = digitalRead(rotorPins[i]) ? '1' : '0';
  }
  stateBuffer[4] = '\0';
}

// Чтение состояния датчика отходов
bool readWasteSensor() {
  return digitalRead(WASTE_PIN);
}

// Чтение состояния концевых выключателей с учетом индивидуальных настроек
bool readEndstopState(int endstopPin) {
  // Определяем тип датчика на основе пина
  bool isNPN = true; // По умолчанию NPN
  
  if (endstopPin == MULTI_ENDSTOP_PIN) {
    isNPN = MULTI_ENDSTOP_TYPE_NPN;
  } else if (endstopPin == MULTIZONE_ENDSTOP_PIN) {
    isNPN = MULTIZONE_ENDSTOP_TYPE_NPN;
  } else if (endstopPin == RRIGHT_ENDSTOP_PIN) {
    isNPN = RRIGHT_ENDSTOP_TYPE_NPN;
  } else if (endstopPin == CLAMP_SENSOR_PIN) {
    isNPN = E0_ENDSTOP_TYPE_NPN; // Используем настройки E0 для clamp датчика
  }
  
  // Используем функцию из stepper_control для корректного чтения
  return readEndstopWithType(endstopPin, isNPN);
} 