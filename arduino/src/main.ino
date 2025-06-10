/**
 * @file: main.ino
 * @description: Главный модуль системы управления с синхронной обработкой команд
 * @dependencies: GyverStepper2, NBHX711, stepper_control, valves, commands
 * @created: 2024-12-19
 */

#include <Arduino.h>
#include <NBHX711.h>
#include "config.h"
#include "stepper_control.h"
#include "sensors.h"
#include "valves.h"
#include "commands.h"

// ============== ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ==============
NBHX711 scale(WEIGHT_SENSOR_DT, WEIGHT_SENSOR_SCK, 16);


// Таймеры для автоматического отчета (используется только если включен)
unsigned long lastWeightReportTime = 0;
const unsigned long WEIGHT_REPORT_INTERVAL = 1000;  // 1 секунда


// ============== ИНИЦИАЛИЗАЦИЯ СИСТЕМЫ ==============
void setup() {
  // Инициализация последовательного порта
  Serial.begin(115200);
  delay(1000);
  
  Serial.println(F("======== СИСТЕМА ЗАПУСКАЕТСЯ ========"));
  Serial.println(F("Версия: 2.1 (синхронная)"));
  Serial.println(F("Дата: 2024-12-19"));
  
  // Инициализация шаговых двигателей
  Serial.println(F("Инициализация шаговых двигателей..."));
  initializeSteppers();
  
  // Инициализация датчиков
  Serial.println(F("Инициализация датчиков..."));
  initializeSensors();
  
  // Инициализация датчика веса
  Serial.println(F("Инициализация датчика веса..."));
  scale.begin();
  scale.setScale(2230.0);
  scale.tare();
  Serial.println(F("Датчик веса инициализирован и тарирован"));
  
  // Инициализация клапанов и насоса
  Serial.println(F("Инициализация клапанов и насоса..."));
  initializeValves();
  
  // Настройка обработчиков команд
  Serial.println(F("Настройка обработчиков команд..."));
  setupCommandHandlers();
  
  // Вывод доступных команд
  Serial.println();
  Serial.println(F("======== СИСТЕМА ГОТОВА ========"));
  Serial.println(F("РЕЖИМ: Синхронная обработка команд"));
  Serial.println(F("Каждая команда выполняется полностью до завершения"));
  Serial.println();
  Serial.println(F("Доступные команды:"));
  Serial.println(F("Движение:"));
  Serial.println(F("  - move_multi <позиция>"));
  Serial.println(F("  - move_multizone <позиция>"));
  Serial.println(F("  - move_rright <позиция>"));
  Serial.println(F("Хоминг:"));
  Serial.println(F("  - zero_multi, zero_multizone, zero_rright"));
  Serial.println(F("Clamp (E0/E1):"));
  Serial.println(F("  - clamp <позиция>"));
  Serial.println(F("  - clamp_zero"));
  Serial.println(F("  - clamp_stop"));
  Serial.println(F("Клапаны:"));
  Serial.println(F("  - kl1 <время>, kl2 <время>"));
  Serial.println(F("  - kl1_on/off, kl2_on/off"));
  Serial.println(F("Насос:"));
  Serial.println(F("  - pump_on/off"));
  Serial.println(F("Датчики:"));
  Serial.println(F("  - weight, raw_weight"));
  Serial.println(F("  - calibrate_weight"));
  Serial.println(F("  - calibrate_weight_factor <коэффициент>"));
  Serial.println(F("  - weight_report_on/off"));
  Serial.println(F("  - staterotor, waste"));
  Serial.println(F("Диагностика:"));
  Serial.println(F("  - check_all_endstops"));
  Serial.println(F("  - test"));
  Serial.println();
  Serial.println(F("Ожидание команд..."));
}

// ============== ОСНОВНОЙ ЦИКЛ ==============
void loop() {
  // Только обработка входящих команд
  // Каждая команда является блокирующей и выполняется полностью
  if (Serial.available() > 0) {
    sCmd.readSerial();
  }
  
}