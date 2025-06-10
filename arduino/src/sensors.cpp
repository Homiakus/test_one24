/**
 * @file: sensors.cpp
 * @description: Модуль для работы с датчиками системы (ротор, отходы, концевые выключатели)
 * @dependencies: Arduino.h, config.h
 * @created: 2024-12-19
 */

#include "sensors.h"
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

// Чтение состояния концевых выключателей
bool readEndstopState(int endstopPin) {
  return !digitalRead(endstopPin); // Инвертировано, так как INPUT_PULLUP
} 