/**
 * @file: valves.cpp
 * @description: Модуль управления клапанами и насосом
 * @dependencies: Arduino.h, config.h
 * @created: 2024-12-19
 */

#include "valves.h"
#include <Arduino.h>

// Инициализация пинов клапанов и насоса
void initializeValves() {
  // Насос
  pinMode(PUMP_PIN, OUTPUT);
  digitalWrite(PUMP_PIN, LOW);
  
  // Клапаны
  pinMode(KL1_PIN, OUTPUT);
  pinMode(KL2_PIN, OUTPUT);
  
  digitalWrite(KL1_PIN, LOW);
  digitalWrite(KL2_PIN, LOW);
}

// Управление насосом
void setPumpState(bool state) {
  digitalWrite(PUMP_PIN, state ? HIGH : LOW);
}

// Переключение состояния клапана
void toggleValveState(int valvePin) {
  digitalWrite(valvePin, !digitalRead(valvePin));
}

// Установка состояния клапана
void setValveState(int valvePin, bool state) {
  digitalWrite(valvePin, state ? HIGH : LOW);
}

// Включение клапана
void turnValveOn(int valvePin) {
  setValveState(valvePin, HIGH);
}

// Выключение клапана
void turnValveOff(int valvePin) {
  setValveState(valvePin, LOW);
}

// Открытие клапана на указанное время (в сотых долях секунды)
void openValveForTime(int valvePin, int timeInCentiseconds) {
  turnValveOn(valvePin);
  delay(timeInCentiseconds * 10); // Переводим сотые доли секунды в миллисекунды (1/100 сек = 10 мс)
  turnValveOff(valvePin);
} 