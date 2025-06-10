/**
 * @file: commands.cpp
 * @description: Модуль обработки команд с улучшенной архитектурой и обработкой ошибок
 * @dependencies: SerialCommand, NBHX711, stepper_control, sensors, valves
 * @created: 2024-12-19
 */

#include "commands.h"
#include <Arduino.h>
#include <NBHX711.h>
#include <GyverStepper2.h>
#include "config.h"
#include "stepper_control.h"
#include "sensors.h"
#include "valves.h"
#include <SerialCommand.h>

// ============== ВНЕШНИЕ ПЕРЕМЕННЫЕ ==============
extern NBHX711 scale;
extern bool autoReportWeight;
extern void enableWeightReport();
extern void disableWeightReport();
extern void resetClampFlag();

// Обработчики команд
void handleClampStop();

// Экземпляр обработчика команд
SerialCommand sCmd;

// ============== СЛУЖЕБНЫЕ ФУНКЦИИ ==============
void sendReceived() {
  Serial.println(MSG_RECEIVED);
}

void sendCompleted() {
  Serial.println(MSG_COMPLETED);
}

void sendError(const char* errorMsg) {
  Serial.print(MSG_ERROR);
  Serial.print(": ");
  Serial.println(errorMsg);
}

void handleUnrecognized(const char* command) {
  Serial.print("Unknown command: ");
  Serial.println(command);
}

void testCommand() {
  Serial.println(F("RECEIVED"));
  Serial.println(F("Test command successful!"));
  Serial.println(F("COMPLETED"));
}

// ============== РЕГИСТРАЦИЯ КОМАНД ==============
void setupCommandHandlers() {
  Serial.println(F("Регистрация обработчиков команд..."));
  
  // Команды движения шаговых двигателей
  sCmd.addCommand("move_multi", handleMoveMulti);
  sCmd.addCommand("move_multizone", handleMoveMultizone);
  sCmd.addCommand("move_rright", handleMoveRRight);
  sCmd.addCommand("move_e0", handleMoveE0);
  sCmd.addCommand("move_e1", handleMoveE1);

  // Команды двигателей E0 и E1 (clamp)
  sCmd.addCommand("clamp", handleClamp);
  sCmd.addCommand("clamp_zero", handleClampZero);
  sCmd.addCommand("clamp_stop", handleClampStop);

  // Команды хоминга
  sCmd.addCommand("zero_multi", handleZeroMulti);
  sCmd.addCommand("zero_multizone", handleZeroMultizone);
  sCmd.addCommand("zero_rright", handleZeroRRight);
  sCmd.addCommand("zero_e0", handleZeroE0);
  sCmd.addCommand("zero_e1", handleZeroE1);
  
  // Команды насоса
  sCmd.addCommand("pump_on", handlePumpOn);
  sCmd.addCommand("pump_off", handlePumpOff);

  // Команды клапанов
  sCmd.addCommand("kl1", handleKl1);
  sCmd.addCommand("kl2", handleKl2);
  sCmd.addCommand("kl1_on", handleKl1On);
  sCmd.addCommand("kl2_on", handleKl2On);
  sCmd.addCommand("kl1_off", handleKl1Off);
  sCmd.addCommand("kl2_off", handleKl2Off);

  // Команды датчиков
  sCmd.addCommand("weight", handleWeight);
  sCmd.addCommand("raw_weight", handleRawWeight);
  sCmd.addCommand("calibrate_weight", handleCalibrateWeight);
  sCmd.addCommand("calibrate_weight_factor", handleCalibrateWeightFactor);
  sCmd.addCommand("staterotor", handleStateRotor);
  sCmd.addCommand("waste", handleWaste);
  
  // Диагностические команды
  sCmd.addCommand("check_multi_endstop", handleCheckMultiEndstop);
  sCmd.addCommand("check_multizone_endstop", handleCheckMultizoneEndstop);
  sCmd.addCommand("check_rright_endstop", handleCheckRRightEndstop);
  sCmd.addCommand("check_all_endstops", handleCheckAllEndstops);
  sCmd.addCommand("check_enable_pins", handleCheckEnablePins);

  // Тестовая команда
  sCmd.addCommand("test", testCommand);

  sCmd.setDefaultHandler(handleUnrecognized);
  
  Serial.println(F("Регистрация обработчиков завершена."));
}

// ============== ОБРАБОТЧИКИ КОМАНД ДВИЖЕНИЯ ==============
void handleMoveMulti() {
  sendReceived();
  char* arg = sCmd.next();
  if (!arg) {
    sendError(MSG_MISSING_PARAMETER);
    return;
  }
  
  long position = atol(arg);
  if (position == 0) {
    sendError(MSG_INVALID_PARAMETER);
    return;
  }
  
  Serial.print(F("Движение Multi к позиции: "));
  Serial.println(position);
  
  if (setStepperPosition(multiStepper, position)) {
    sendCompleted();
  } else {
    sendError("MOVE_FAILED");
  }
}

void handleMoveMultizone() {
  sendReceived();
  char* arg = sCmd.next();
  if (!arg) {
    sendError(MSG_MISSING_PARAMETER);
    return;
  }
  
  long position = atol(arg);
  if (position == 0) {
    sendError(MSG_INVALID_PARAMETER);
    return;
  }
  
  Serial.print(F("Движение Multizone к позиции: "));
  Serial.println(position);
  
  if (setStepperPosition(multizoneSteper, position)) {
    sendCompleted();
  } else {
    sendError("MOVE_FAILED");
  }
}

void handleMoveRRight() {
  sendReceived();
  char* arg = sCmd.next();
  if (!arg) {
    sendError(MSG_MISSING_PARAMETER);
    return;
  }
  
  long position = atol(arg);
  if (position == 0) {
    sendError(MSG_INVALID_PARAMETER);
    return;
  }
  
  Serial.print(F("Движение RRight к позиции: "));
  Serial.println(position);
  
  if (setStepperPosition(rRightStepper, position)) {
    sendCompleted();
  } else {
    sendError("MOVE_FAILED");
  }
}

void handleMoveE0() {
  sendReceived();
  char* arg = sCmd.next();
  if (!arg) {
    sendError(MSG_MISSING_PARAMETER);
    return;
  }
  
  long position = atol(arg);
  if (position == 0) {
    sendError(MSG_INVALID_PARAMETER);
    return;
  }
  
  Serial.print(F("Индивидуальное движение E0 к позиции: "));
  Serial.println(position);
  
  if (moveE0(position)) {
    sendCompleted();
  } else {
    sendError("MOVE_FAILED");
  }
}

void handleMoveE1() {
  sendReceived();
  char* arg = sCmd.next();
  if (!arg) {
    sendError(MSG_MISSING_PARAMETER);
    return;
  }
  
  long position = atol(arg);
  if (position == 0) {
    sendError(MSG_INVALID_PARAMETER);
    return;
  }
  
  Serial.print(F("Индивидуальное движение E1 к позиции: "));
  Serial.println(position);
  
  if (moveE1(position)) {
    sendCompleted();
  } else {
    sendError("MOVE_FAILED");
  }
}

// ============== ОБРАБОТЧИКИ КОМАНД ХОМИНГА ==============
void handleZeroMulti() {
  sendReceived();
  Serial.println(F("Начало хоминга Multi..."));
  
  if (homeStepperMotor(multiStepper, MULTI_ENDSTOP_PIN)) {
    Serial.println(F("Хоминг Multi завершен"));
    sendCompleted();
  } else {
    sendError(MSG_HOMING_TIMEOUT);
  }
}

void handleZeroMultizone() {
  sendReceived();
  Serial.println(F("Начало хоминга Multizone..."));
  
  if (homeStepperMotor(multizoneSteper, MULTIZONE_ENDSTOP_PIN)) {
    Serial.println(F("Хоминг Multizone завершен"));
    sendCompleted();
  } else {
    sendError(MSG_HOMING_TIMEOUT);
  }
}

void handleZeroRRight() {
  sendReceived();
  Serial.println(F("Начало хоминга RRight..."));
  
  if (homeStepperMotor(rRightStepper, RRIGHT_ENDSTOP_PIN)) {
    Serial.println(F("Хоминг RRight завершен"));
    sendCompleted();
  } else {
    sendError(MSG_HOMING_TIMEOUT);
  }
}

void handleZeroE0() {
  sendReceived();
  Serial.println(F("Начало индивидуального хоминга E0..."));
  
  if (homeE0()) {
    Serial.println(F("Хоминг E0 завершен"));
    sendCompleted();
  } else {
    sendError(MSG_HOMING_TIMEOUT);
  }
}

void handleZeroE1() {
  sendReceived();
  Serial.println(F("Начало индивидуального хоминга E1..."));
  
  if (homeE1()) {
    Serial.println(F("Хоминг E1 завершен"));
    sendCompleted();
  } else {
    sendError(MSG_HOMING_TIMEOUT);
  }
}

// ============== ОБРАБОТЧИКИ КОМАНД НАСОСА ==============
void handlePumpOn() {
  sendReceived();
  Serial.print(F("Включение насоса (пин "));
  Serial.print(PUMP_PIN);
  Serial.println(F(")..."));
  
  setPumpState(true);
  
  Serial.println(F("Насос включен"));
  sendCompleted();
}

void handlePumpOff() {
  sendReceived();
  Serial.print(F("Выключение насоса (пин "));
  Serial.print(PUMP_PIN);
  Serial.println(F(")..."));
  
  setPumpState(false);
  
  Serial.println(F("Насос выключен"));
  sendCompleted();
}

// ============== ОБРАБОТЧИКИ КОМАНД КЛАПАНОВ ==============
void handleKl1() {
  sendReceived();
  char* arg = sCmd.next();
  if (!arg) {
    sendError(MSG_MISSING_PARAMETER);
    return;
  }
  
  int time = atoi(arg);
  if (time <= 0) {
    sendError(MSG_INVALID_PARAMETER);
    return;
  }
  
  Serial.print(F("Открытие клапана KL1 на "));
  Serial.print(time);
  Serial.println(F(" сотых секунды"));
  
  openValveForTime(KL1_PIN, time);
  
  Serial.println(F("Клапан KL1 закрыт"));
  sendCompleted();
}

void handleKl2() {
  sendReceived();
  char* arg = sCmd.next();
  if (!arg) {
    sendError(MSG_MISSING_PARAMETER);
    return;
  }
  
  int time = atoi(arg);
  if (time <= 0) {
    sendError(MSG_INVALID_PARAMETER);
    return;
  }
  
  Serial.print(F("Открытие клапана KL2 на "));
  Serial.print(time);
  Serial.println(F(" сотых секунды"));
  
  openValveForTime(KL2_PIN, time);
  
  Serial.println(F("Клапан KL2 закрыт"));
  sendCompleted();
}

void handleKl1On() {
  sendReceived();
  Serial.print(F("Включение клапана KL1 (пин "));
  Serial.print(KL1_PIN);
  Serial.println(F(")"));
  
  turnValveOn(KL1_PIN);
  
  Serial.println(F("Клапан KL1 включен"));
  sendCompleted();
}

void handleKl2On() {
  sendReceived();
  Serial.print(F("Включение клапана KL2 (пин "));
  Serial.print(KL2_PIN);
  Serial.println(F(")"));
  
  turnValveOn(KL2_PIN);
  
  Serial.println(F("Клапан KL2 включен"));
  sendCompleted();
}

void handleKl1Off() {
  sendReceived();
  Serial.print(F("Выключение клапана KL1 (пин "));
  Serial.print(KL1_PIN);
  Serial.println(F(")"));
  
  turnValveOff(KL1_PIN);
  
  Serial.println(F("Клапан KL1 выключен"));
  sendCompleted();
}

void handleKl2Off() {
  sendReceived();
  Serial.print(F("Выключение клапана KL2 (пин "));
  Serial.print(KL2_PIN);
  Serial.println(F(")"));
  
  turnValveOff(KL2_PIN);
  
  Serial.println(F("Клапан KL2 выключен"));
  sendCompleted();
}

// ============== ОБРАБОТЧИКИ КОМАНД ДАТЧИКОВ ==============
void handleWeight() {
  sendReceived();
  Serial.println(F("Чтение веса..."));
  float weight = scale.getUnits(5);
  Serial.println(weight, 2);
  sendCompleted();
}

void handleRawWeight() {
  sendReceived();
  Serial.println(F("Чтение сырого значения датчика веса..."));
  long raw = scale.getRaw();
  Serial.println(raw);
  sendCompleted();
}

void handleCalibrateWeight() {
  sendReceived();
  Serial.println(F("Запуск процедуры обнуления датчика веса..."));
  Serial.println(F("Убедитесь, что на весах ничего нет"));
  
  delay(2000);
  Serial.println(F("Начинаю обнуление..."));
  scale.tare();
  Serial.println(F("Датчик веса успешно обнулен!"));
  
  sendCompleted();
}

void handleCalibrateWeightFactor() {
  sendReceived();
  
  char* arg = sCmd.next();
  if (!arg) {
    sendError(MSG_MISSING_PARAMETER);
    return;
  }
  
  float factor = atof(arg);
  if (factor == 0.0) {
    sendError(MSG_INVALID_PARAMETER);
    return;
  }
  
  Serial.print(F("Установка калибровочного коэффициента: "));
  Serial.println(factor);
  
  scale.setScale(factor);
  
  sendCompleted();
}

void handleStateRotor() {
  sendReceived();
  char state[5];
  readRotorState(state);
  Serial.println(state);
  sendCompleted();
}

void handleWaste() {
  sendReceived();
  bool wasteState = readWasteSensor();
  Serial.println(wasteState ? "1" : "0");
  sendCompleted();
}

void handleWeightReportOn() {
  sendReceived();
  enableWeightReport();
  sendCompleted();
}

void handleWeightReportOff() {
  sendReceived();
  disableWeightReport();
  sendCompleted();
}

// ============== ОБРАБОТЧИКИ ДИАГНОСТИЧЕСКИХ КОМАНД ==============
void handleCheckMultiEndstop() {
  sendReceived();
  bool state = readEndstopState(MULTI_ENDSTOP_PIN);
  Serial.print("Multi endstop: ");
  Serial.println(state ? "TRIGGERED" : "NOT TRIGGERED");
  sendCompleted();
}

void handleCheckMultizoneEndstop() {
  sendReceived();
  bool state = readEndstopState(MULTIZONE_ENDSTOP_PIN);
  Serial.print("Multizone endstop: ");
  Serial.println(state ? "TRIGGERED" : "NOT TRIGGERED");
  sendCompleted();
}

void handleCheckRRightEndstop() {
  sendReceived();
  bool state = readEndstopState(RRIGHT_ENDSTOP_PIN);
  Serial.print("RRight endstop: ");
  Serial.println(state ? "TRIGGERED" : "NOT TRIGGERED");
  sendCompleted();
}

void handleCheckAllEndstops() {
  sendReceived();
  Serial.println(F("Проверка всех концевых выключателей:"));
  
  bool multiState = readEndstopState(MULTI_ENDSTOP_PIN);
  bool multizoneState = readEndstopState(MULTIZONE_ENDSTOP_PIN);
  bool rrightState = readEndstopState(RRIGHT_ENDSTOP_PIN);
  
  Serial.print("Multi: ");
  Serial.println(multiState ? "TRIGGERED" : "NOT TRIGGERED");
  Serial.print("Multizone: ");
  Serial.println(multizoneState ? "TRIGGERED" : "NOT TRIGGERED");
  Serial.print("RRight: ");
  Serial.println(rrightState ? "TRIGGERED" : "NOT TRIGGERED");
  
  sendCompleted();
}

void handleCheckEnablePins() {
  sendReceived();
  Serial.println(F("Проверка состояния enable пинов:"));
  
  Serial.print(F("Multi enable pin "));
  Serial.print(MULTI_ENABLE_PIN);
  Serial.print(F(": "));
  Serial.println(digitalRead(MULTI_ENABLE_PIN) ? "HIGH" : "LOW");
  
  Serial.print(F("Multizone enable pin "));
  Serial.print(MULTIZONE_ENABLE_PIN);
  Serial.print(F(": "));
  Serial.println(digitalRead(MULTIZONE_ENABLE_PIN) ? "HIGH" : "LOW");
  
  Serial.print(F("RRight enable pin "));
  Serial.print(RRIGHT_ENABLE_PIN);
  Serial.print(F(": "));
  Serial.println(digitalRead(RRIGHT_ENABLE_PIN) ? "HIGH" : "LOW");
  
  Serial.print(F("E0 enable pin "));
  Serial.print(E0_ENABLE_PIN);
  Serial.print(F(": "));
  Serial.println(digitalRead(E0_ENABLE_PIN) ? "HIGH" : "LOW");
  
  Serial.print(F("E1 enable pin "));
  Serial.print(E1_ENABLE_PIN);
  Serial.print(F(": "));
  Serial.println(digitalRead(E1_ENABLE_PIN) ? "HIGH" : "LOW");
  
  sendCompleted();
}

// ============== ОБРАБОТЧИКИ КОМАНД ДЛЯ ДВИГАТЕЛЕЙ E0 И E1 ==============
void handleClamp() {
  sendReceived();
  char* arg = sCmd.next();
  if (!arg) {
    sendError(MSG_MISSING_PARAMETER);
    return;
  }
  
  long position = atol(arg);
  Serial.print(F("Выполнение команды clamp к позиции: "));
  Serial.println(position);
  
  if (clampMotors(position)) {
    Serial.println(F("Команда clamp успешно выполнена"));
    sendCompleted();
  } else {
    Serial.println(F("Ошибка выполнения команды clamp"));
    sendError("CLAMP_FAILED");
    
    // Безопасность: сброс состояния
    e0Stepper.reset();
    e1Stepper.reset();
    resetClampFlag();
  }
}

void handleClampZero() {
  sendReceived();
  Serial.println(F("Начало процедуры обнуления двигателей E0 и E1..."));
  
  if (clampZeroMotors()) {
    Serial.println(F("Обнуление двигателей E0 и E1 успешно выполнено"));
    sendCompleted();
  } else {
    Serial.println(F("Ошибка при выполнении обнуления"));
    sendError("CLAMP_ZERO_FAILED");
    
    // Безопасность: сброс состояния
    e0Stepper.reset();
    e1Stepper.reset();
    resetClampFlag();
  }
}

void handleClampStop() {
  sendReceived();
  Serial.println(F("Выполнение аварийной остановки двигателей E0 и E1..."));
  
  // Остановка двигателей
  e0Stepper.brake();
  e1Stepper.brake();
  
  // Сброс позиций в текущее положение
  e0Stepper.reset();
  e1Stepper.reset();
  
  // Сброс состояния
  resetClampFlag();
  
  Serial.println(F("Двигатели E0 и E1 остановлены"));
  sendCompleted();
}