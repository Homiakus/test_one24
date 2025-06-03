#include "commands.h"
#include <Arduino.h>
#include <NBHX711.h>
#include <GyverStepper2.h>
#include "config.h"
#include "stepper_control.h"
#include "sensors.h"
#include "valves.h"
#include <SerialCommand.h>

// Объявления внешних переменных для работы с весами
extern NBHX711 scale;
extern bool autoReportWeight;
extern void enableWeightReport();
extern void disableWeightReport();

// Объявление внешней функции для управления шаговыми двигателями
extern void resetClampFlag();

// Объявления обработчиков команд
void handleClampStop();

// Создание экземпляра обработчика команд
SerialCommand sCmd;

// Отправка сообщения о получении команды
void sendReceived() {
  Serial.println(MSG_RECEIVED);
}

// Отправка сообщения о завершении команды
void sendCompleted() {
  Serial.println(MSG_COMPLETED);
}

// Отправка сообщения об ошибке
void sendError(const char* errorMsg) {
  Serial.print(MSG_ERROR);
  Serial.print(": ");
  Serial.println(errorMsg);
}

// Обработка неизвестной команды
void handleUnrecognized(const char* command) {
  Serial.print("Unknown command: ");
  Serial.println(command);
}

// Тестовая функция для проверки связи
void testCommand() {
  Serial.println(F("RECEIVED"));
  Serial.println(F("Test command successful!"));
  Serial.println(F("COMPLETED"));
}

// Настройка обработчиков команд
void setupCommandHandlers() {
  Serial.println(F("Регистрация обработчиков команд..."));
  
  // Movement commands
  sCmd.addCommand("move_multi", handleMoveMulti);
  sCmd.addCommand("move_multizone", handleMoveMultizone);
  sCmd.addCommand("move_rright", handleMoveRRight);

  // Clamp commands для двигателей E0 и E1
  sCmd.addCommand("clamp", handleClamp);
  sCmd.addCommand("clamp_zero", handleClampZero);
  sCmd.addCommand("clamp_stop", handleClampStop);

  // Homing commands
  sCmd.addCommand("zero_multi", handleZeroMulti);
  sCmd.addCommand("zero_multizone", handleZeroMultizone);
  sCmd.addCommand("zero_rright", handleZeroRRight);
  
  // Pump commands
  Serial.println(F("Регистрация команд насоса..."));
  sCmd.addCommand("pump_on", handlePumpOn);
  sCmd.addCommand("pump_off", handlePumpOff);

  // Valve commands
  Serial.println(F("Регистрация команд клапанов..."));
  sCmd.addCommand("kl1_on", handleKl1On);
  sCmd.addCommand("kl2_on", handleKl2On);
  sCmd.addCommand("kl3_on", handleKl3On);
  sCmd.addCommand("kl1_off", handleKl1Off);
  sCmd.addCommand("kl2_off", handleKl2Off);
  sCmd.addCommand("kl3_off", handleKl3Off);

  // Sensor commands
  Serial.println(F("Регистрация команд датчиков..."));
  sCmd.addCommand("weight", handleWeight);
  sCmd.addCommand("raw_weight", handleRawWeight);
  sCmd.addCommand("calibrate_weight", handleCalibrateWeight);
  sCmd.addCommand("calibrate_weight_factor", handleCalibrateWeightFactor);
  sCmd.addCommand("weight_report_on", handleWeightReportOn);
  sCmd.addCommand("weight_report_off", handleWeightReportOff);
  sCmd.addCommand("staterotor", handleStateRotor);
  sCmd.addCommand("waste", handleWaste);
  
  // Diagnostic commands
  sCmd.addCommand("check_multi_endstop", handleCheckMultiEndstop);
  sCmd.addCommand("check_multizone_endstop", handleCheckMultizoneEndstop);
  sCmd.addCommand("check_rright_endstop", handleCheckRRightEndstop);
  sCmd.addCommand("check_all_endstops", handleCheckAllEndstops);

  // Добавляем тестовую команду
  sCmd.addCommand("test", testCommand);

  Serial.println(F("Установка обработчика для неизвестных команд..."));
  sCmd.setDefaultHandler(handleUnrecognized);
  
  Serial.println(F("Регистрация обработчиков завершена."));
}

// ============== ОБРАБОТЧИКИ КОМАНД ДВИЖЕНИЯ ==============
void handleMoveMulti() {
  sendReceived();
  char* arg = sCmd.next();
  if (arg) {
    if (setStepperPosition(multiStepper, atol(arg))) {
      sendCompleted();
    } else {
      sendError(MSG_NO_POSITION);
    }
  } else {
    sendError(MSG_NO_POSITION);
  }
}

void handleMoveMultizone() {
  sendReceived();
  char* arg = sCmd.next();
  if (arg) {
    if (setStepperPosition(multizoneSteper, atol(arg))) {
      sendCompleted();
    } else {
      sendError(MSG_NO_POSITION);
    }
  } else {
    sendError(MSG_NO_POSITION);
  }
}

void handleMoveRRight() {
  sendReceived();
  char* arg = sCmd.next();
  if (arg) {
    if (setStepperPosition(rRightStepper, atol(arg))) {
      sendCompleted();
    } else {
      sendError(MSG_NO_POSITION);
    }
  } else {
    sendError(MSG_NO_POSITION);
  }
}


// ============== ОБРАБОТЧИКИ КОМАНД ХОМИНГА ==============
void handleZeroMulti() {
  sendReceived();
  if (homeStepperMotor(multiStepper, MULTI_ENDSTOP_PIN)) {
    sendCompleted();
  } else {
    sendError(MSG_HOMING_TIMEOUT);
  }
}

void handleZeroMultizone() {
  sendReceived();
  if (homeStepperMotor(multizoneSteper, MULTIZONE_ENDSTOP_PIN)) {
    sendCompleted();
  } else {
    sendError(MSG_HOMING_TIMEOUT);
  }
}

void handleZeroRRight() {
  sendReceived();
  if (homeStepperMotor(rRightStepper, RRIGHT_ENDSTOP_PIN)) {
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
  
  Serial.println(F("Насос включен."));
  sendCompleted();
}

void handlePumpOff() {
  sendReceived();
  Serial.print(F("Выключение насоса (пин "));
  Serial.print(PUMP_PIN);
  Serial.println(F(")..."));
  
  setPumpState(false);
  
  Serial.println(F("Насос выключен."));
  sendCompleted();
}

// ============== ОБРАБОТЧИКИ КОМАНД КЛАПАНОВ ==============
void handleKl1On() {
  sendReceived();
  Serial.print(F("Включение клапана KL1 (пин "));
  Serial.print(KL1_PIN);
  Serial.println(F(")..."));
  
  turnValveOn(KL1_PIN);
  
  Serial.println(F("Клапан включен."));
  sendCompleted();
}

void handleKl2On() {
  sendReceived();
  Serial.print(F("Включение клапана KL2 (пин "));
  Serial.print(KL2_PIN);
  Serial.println(F(")..."));
  
  turnValveOn(KL2_PIN);
  
  Serial.println(F("Клапан включен."));
  sendCompleted();
}

void handleKl3On() {
  sendReceived();
  Serial.print(F("Включение клапана KL3 (пин "));
  Serial.print(KL3_PIN);
  Serial.println(F(")..."));
  
  turnValveOn(KL3_PIN);
  
  Serial.println(F("Клапан включен."));
  sendCompleted();
}

void handleKl1Off() {
  sendReceived();
  Serial.print(F("Выключение клапана KL1 (пин "));
  Serial.print(KL1_PIN);
  Serial.println(F(")..."));
  
  turnValveOff(KL1_PIN);
  
  Serial.println(F("Клапан выключен."));
  sendCompleted();
}

void handleKl2Off() {
  sendReceived();
  Serial.print(F("Выключение клапана KL2 (пин "));
  Serial.print(KL2_PIN);
  Serial.println(F(")..."));
  
  turnValveOff(KL2_PIN);
  
  Serial.println(F("Клапан выключен."));
  sendCompleted();
}

void handleKl3Off() {
  sendReceived();
  Serial.print(F("Выключение клапана KL3 (пин "));
  Serial.print(KL3_PIN);
  Serial.println(F(")..."));
  
  turnValveOff(KL3_PIN);
  
  Serial.println(F("Клапан выключен."));
  sendCompleted();
}

// ============== ОБРАБОТЧИКИ КОМАНД ДАТЧИКОВ ==============
void handleWeight() {
  sendReceived();
  float weight = scale.getUnits(5);
  Serial.println(weight, 2);
  sendCompleted();
}

// Обработчик команды для получения сырого (необработанного) значения датчика веса
void handleRawWeight() {
  sendReceived();
  long raw = scale.getRaw();
  Serial.println(raw);
  sendCompleted();
}

// Обработчик команды для получения расширенной отладочной информации о датчике веса
void handleWeightDebug() {
  sendReceived();
  
  long raw_value = scale.getRaw();
  float weight = scale.getUnits(5);
  long offset = scale.getOffset();
  float scale_factor = scale.getScale();
  
  Serial.print(F("Отладка датчика веса:\n"));
  Serial.print(F("Сырое значение: "));
  Serial.print(raw_value);
  Serial.print(F("\nТара (смещение): "));
  Serial.print(offset);
  Serial.print(F("\nКалибровочный коэффициент: "));
  Serial.print(scale_factor);
  Serial.print(F("\nВес в граммах: "));
  Serial.print(weight, 2);
  Serial.print(F("\nСреднее из 10 измерений: "));
  Serial.println(scale.getUnits(10), 2);
  
  sendCompleted();
}

// Обработчик команды обнуления весов
void handleCalibrateWeight() {
  sendReceived();
  Serial.println(F("Запуск процедуры обнуления датчика веса..."));
  
  // Выполняем тарирование
  Serial.println(F("Убедитесь, что на весах ничего нет"));
  delay(2000);
  Serial.println(F("Начинаю обнуление..."));
  scale.tare();
  Serial.println(F("Датчик веса успешно обнулен!"));
  
  sendCompleted();
}

// Чтение состояния ротора
void handleStateRotor() {
  sendReceived();
  char state[5];
  readRotorState(state);
  Serial.println(state);
  sendCompleted();
}

// Чтение состояния датчика отходов
void handleWaste() {
  sendReceived();
  Serial.println(readWasteSensor() ? "1" : "0");
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
}

void handleCheckRRightEndstop() {
  sendReceived();
  bool state = readEndstopState(RRIGHT_ENDSTOP_PIN);
  Serial.print("RRight endstop: ");
  Serial.println(state ? "TRIGGERED" : "NOT TRIGGERED");
}


void handleCheckAllEndstops() {
  sendReceived();
  handleCheckMultiEndstop();
  handleCheckMultizoneEndstop();
  handleCheckRRightEndstop();
}

// Обработчик команды для включения автоматического отчета о весе
void handleWeightReportOn() {
  sendReceived();
  enableWeightReport();
  sendCompleted();
}

// Обработчик команды для выключения автоматического отчета о весе
void handleWeightReportOff() {
  sendReceived();
  disableWeightReport();
  sendCompleted();
}

void handleDisableWeightReport() {
  disableWeightReport();
  Serial.println(F("WEIGHT_REPORT:DISABLED"));
}

// Обработчик команды для установки калибровочного коэффициента
void handleCalibrateWeightFactor() {
  sendReceived();
  
  char* arg = sCmd.next();
  if (arg) {
    float factor = atof(arg);
    Serial.print(F("Установка калибровочного коэффициента: "));
    Serial.println(factor);
    
    // Установка калибровочного коэффициента
    scale.setScale(factor);
    
    sendCompleted();
  } else {
    sendError(MSG_MISSING_PARAMETER);
  }
}

// ============== ОБРАБОТЧИКИ КОМАНД ДЛЯ ДВИГАТЕЛЕЙ E0 И E1 ==============
// Команда clamp вызывает функцию clampMotors с заданной абсолютной позицией
// Пример использования: отправить "clamp 100" для движения моторов в позицию 100
void handleClamp() {
  sendReceived();
  char* arg = sCmd.next();
  if (arg) {
    long position = atol(arg);
    Serial.print(F("Выполняю команду clamp в абсолютную позицию "));
    Serial.print(position);
    Serial.println(F("..."));
    
    if (clampMotors(position)) {
      Serial.println(F("Команда clamp успешно выполнена."));
      sendCompleted();
    } else {
      // Более детальное сообщение об ошибке
      Serial.println(F("Ошибка при выполнении команды clamp. Возможно, превышен таймаут или двигатели заблокированы."));
      sendError("CLAMP_FAILED");
      
      // Дополнительная безопасность: сбрасываем состояние
      e0Stepper.reset();
      e1Stepper.reset();
      resetClampFlag();
    }
  } else {
    sendError(MSG_MISSING_PARAMETER);
  }
}

void handleClampZero() {
  sendReceived();
  Serial.println(F("Начинаю процедуру обнуления двигателей E0 и E1..."));
  
  if (clampZeroMotors()) {
    // Команда запущена успешно
    Serial.println(F("Обнуление двигателей E0 и E1 успешно выполнено."));
    sendCompleted();
  } else {
    // Более детальное сообщение об ошибке
    Serial.println(F("Ошибка при выполнении обнуления. Возможно, превышен таймаут или датчик не сработал."));
    sendError("CLAMP_ZERO_FAILED");
    
    // Дополнительная безопасность: сбрасываем состояние
    e0Stepper.reset();
    e1Stepper.reset();
    resetClampFlag();
  }
}

// Обработчик команды аварийной остановки двигателей E0 и E1
void handleClampStop() {
  sendReceived();
  Serial.println(F("Выполняю аварийную остановку двигателей E0 и E1..."));
  
  // Остановка двигателей
  e0Stepper.brake();
  e1Stepper.brake();
  
  // Сброс позиций в текущее положение
  e0Stepper.reset();
  e1Stepper.reset();
  
  // Сброс состояния
  resetClampFlag();
  
  Serial.println(F("Двигатели E0 и E1 остановлены."));
  sendCompleted();
}