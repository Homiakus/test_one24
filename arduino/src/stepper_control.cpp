/**
 * @file: stepper_control.cpp
 * @description: Модуль управления шаговыми двигателями с оптимизированными алгоритмами
 * @dependencies: GyverStepper2, config.h
 * @created: 2024-12-19
 */

#include "stepper_control.h"
#include <Arduino.h>

// Создание экземпляров шаговых двигателей (используем GStepper2)
GStepper2<STEPPER2WIRE> multiStepper(200, MULTI_STEP_PIN, MULTI_DIR_PIN, MULTI_ENABLE_PIN);
GStepper2<STEPPER2WIRE> multizoneSteper(200, MULTIZONE_STEP_PIN, MULTIZONE_DIR_PIN, MULTIZONE_ENABLE_PIN);
GStepper2<STEPPER2WIRE> rRightStepper(200, RRIGHT_STEP_PIN, RRIGHT_DIR_PIN, RRIGHT_ENABLE_PIN);
GStepper2<STEPPER2WIRE> e0Stepper(200, E0_STEP_PIN, E0_DIR_PIN, E0_ENABLE_PIN);
GStepper2<STEPPER2WIRE> e1Stepper(200, E1_STEP_PIN, E1_DIR_PIN, E1_ENABLE_PIN);

// Флаг для предотвращения одновременного запуска команд, влияющих на E0/E1
static bool clampInProgress = false;

// ============== УПРАВЛЕНИЕ ФЛАГОМ ЗАНЯТОСТИ ==============
void resetClampFlag() {
  clampInProgress = false;
  Serial.println(F("Флаг занятости clamp сброшен"));
}

bool isClampInProgress() {
  return clampInProgress;
}

// ============== ИНИЦИАЛИЗАЦИЯ СИСТЕМЫ ==============
void initializeSteppers() {
  Serial.println(F("Инициализация шаговых двигателей..."));
  
  // Настройка пинов для двигателей E0 и E1
  pinMode(E0_STEP_PIN, OUTPUT);
  pinMode(E0_DIR_PIN, OUTPUT);
  pinMode(E0_ENABLE_PIN, OUTPUT);
  pinMode(E1_STEP_PIN, OUTPUT);
  pinMode(E1_DIR_PIN, OUTPUT);
  pinMode(E1_ENABLE_PIN, OUTPUT);
  
  // Активация двигателей (активный LOW для enable)
  digitalWrite(E0_ENABLE_PIN, LOW);
  digitalWrite(E1_ENABLE_PIN, LOW);
  
  // Настройка датчика для функции clamp_zero
  pinMode(CLAMP_SENSOR_PIN, INPUT_PULLUP);
  
  // Универсальная конфигурация для всех двигателей
  auto configureMotor = [](GStepper2<STEPPER2WIRE>& stepper, const char* name) {
    stepper.enable();
    stepper.setMaxSpeed(500);
    stepper.setAcceleration(800);
    Serial.print(F("Двигатель "));
    Serial.print(name);
    Serial.println(F(" настроен"));
  };

  configureMotor(multiStepper, "Multi");
  configureMotor(multizoneSteper, "Multizone");
  configureMotor(rRightStepper, "RRight");
  configureMotor(e0Stepper, "E0");
  configureMotor(e1Stepper, "E1");
  
  Serial.println(F("Инициализация шаговых двигателей завершена"));
}

// ============== БАЗОВЫЕ ФУНКЦИИ УПРАВЛЕНИЯ ==============
bool setStepperPosition(GStepper2<STEPPER2WIRE>& stepper, long position) {
  if (position == 0) {
    Serial.println(F("Ошибка: Нулевая позиция не допускается"));
    return false;
  }
  
  // Проверка занятости двигателей E0 и E1
  if ((&stepper == &e0Stepper || &stepper == &e1Stepper) && clampInProgress) {
    Serial.println(F("Ошибка: Двигатели E0/E1 заняты командой clamp"));
    return false;
  }
  
  Serial.print(F("Движение к позиции: "));
  Serial.println(position);
  
  stepper.setTarget(position);
  
  // Блокирующее ожидание завершения движения
  unsigned long startTime = millis();
  const unsigned long moveTimeout = 30000; // 30 секунд таймаут
  
  while (!stepper.ready()) {
    if (millis() - startTime > moveTimeout) {
      Serial.println(F("Ошибка: Таймаут движения"));
      stepper.brake();
      return false;
    }
    stepper.tick();
    yield();
  }
  
  Serial.print(F("Движение завершено. Текущая позиция: "));
  Serial.println(stepper.getCurrent());
  return true;
}

bool homeStepperMotor(GStepper2<STEPPER2WIRE>& stepper, int endstopPin) {
  // Проверка занятости двигателей E0 и E1
  if ((&stepper == &e0Stepper || &stepper == &e1Stepper) && clampInProgress) {
    Serial.println(F("Ошибка: Двигатели E0/E1 заняты командой clamp"));
    return false;
  }
  
  Serial.println(F("Начало процедуры хоминга..."));
  
  // Установка скорости для хоминга
  stepper.setSpeed(-HOMING_SPEED);
  
  unsigned long startTime = millis();
  
  // Движение к концевику
  while (digitalRead(endstopPin)) {
    if (millis() - startTime >= HOMING_TIMEOUT) {
      stepper.brake();
      Serial.println(F("Ошибка: Таймаут хоминга"));
      return false;
    }
    stepper.tickManual();
    yield();
  }
  
  // Концевик сработал
  stepper.brake();
  stepper.reset(); // Сброс позиции в 0
  Serial.println(F("Концевик сработал, позиция сброшена"));
  
  delay(100); // Стабилизация
  
  // Отъезд от концевика
  stepper.setTarget(100);
  startTime = millis();
  
  while (!stepper.ready()) {
    if (millis() - startTime > 10000) { // 10 секунд на отъезд
      stepper.brake();
      Serial.println(F("Ошибка: Таймаут отъезда от концевика"));
      return false;
    }
    stepper.tick();
    yield();
  }
  
  stepper.reset(); // Устанавливаем новую нулевую точку
  Serial.println(F("Хоминг завершен успешно"));
  return true;
}

// ============== ФУНКЦИИ ДЛЯ ДВИГАТЕЛЕЙ E0/E1 ==============
bool clampMotors(long targetPosition) {
  if (clampInProgress) {
    Serial.println(F("Ошибка: Команда clamp уже выполняется"));
    return false;
  }
  
  clampInProgress = true;
  Serial.println(F("Начало выполнения команды clamp"));
  
  // Получение текущих позиций
  long currentE0 = e0Stepper.getCurrent();
  long currentE1 = e1Stepper.getCurrent();
  
  Serial.print(F("Текущие позиции - E0: "));
  Serial.print(currentE0);
  Serial.print(F(", E1: "));
  Serial.println(currentE1);
  
  // Остановка двигателей перед движением
  e0Stepper.brake();
  e1Stepper.brake();
  delay(50);
  
  // Настройка параметров движения
  e0Stepper.setMaxSpeed(CLAMP_SPEED);
  e1Stepper.setMaxSpeed(CLAMP_SPEED);
  e0Stepper.setAcceleration(CLAMP_ACCELERATION);
  e1Stepper.setAcceleration(CLAMP_ACCELERATION);
  
  // Установка целевых позиций
  e0Stepper.setTarget(targetPosition);
  e1Stepper.setTarget(targetPosition);
  
  Serial.print(F("Целевая позиция: "));
  Serial.println(targetPosition);
  
  // Расчет динамического таймаута
  long maxDistance = max(abs(targetPosition - currentE0), abs(targetPosition - currentE1));
  unsigned long dynamicTimeout = HOMING_TIMEOUT + (maxDistance / 10) * 100;
  
  Serial.print(F("Максимальное расстояние: "));
  Serial.print(maxDistance);
  Serial.print(F(", таймаут: "));
  Serial.println(dynamicTimeout);
  
  // Синхронное движение обоих двигателей
  unsigned long startTime = millis();
  unsigned long lastProgressTime = 0;
  
  while (!e0Stepper.ready() || !e1Stepper.ready()) {
    unsigned long currentTime = millis();
    
    // Проверка таймаута
    if (currentTime - startTime >= dynamicTimeout) {
      Serial.println(F("Ошибка: Таймаут выполнения команды clamp"));
      e0Stepper.brake();
      e1Stepper.brake();
      clampInProgress = false;
      return false;
    }
    
    // Обновление двигателей
    e0Stepper.tick();
    e1Stepper.tick();
    
    // Периодический вывод прогресса
    if (currentTime - lastProgressTime >= 2000) {
      lastProgressTime = currentTime;
      Serial.print(F("Прогресс - E0: "));
      Serial.print(e0Stepper.getCurrent());
      Serial.print(F("/"));
      Serial.print(e0Stepper.getTarget());
      Serial.print(F(", E1: "));
      Serial.print(e1Stepper.getCurrent());
      Serial.print(F("/"));
      Serial.println(e1Stepper.getTarget());
    }
    
    yield();
  }
  
  Serial.print(F("Движение завершено - E0: "));
  Serial.print(e0Stepper.getCurrent());
  Serial.print(F(", E1: "));
  Serial.println(e1Stepper.getCurrent());
  
  clampInProgress = false;
  return true;
}

bool clampZeroMotors() {
  if (clampInProgress) {
    Serial.println(F("Ошибка: Команда clamp уже выполняется"));
    return false;
  }
  
  clampInProgress = true;
  Serial.println(F("Начало процедуры clamp_zero"));
  
  // Остановка двигателей
  e0Stepper.brake();
  e1Stepper.brake();
  delay(100);
  
  // Настройка параметров
  e0Stepper.setMaxSpeed(CLAMP_ZERO_SPEED);
  e1Stepper.setMaxSpeed(CLAMP_ZERO_SPEED);
  e0Stepper.setAcceleration(CLAMP_ACCELERATION);
  e1Stepper.setAcceleration(CLAMP_ACCELERATION);
  
  // Начальная проверка датчика
  if (!digitalRead(CLAMP_SENSOR_PIN)) {
    Serial.println(F("Датчик уже активен, начинаю отъезд"));
    // Если датчик уже нажат, сначала отъезжаем
    e0Stepper.setSpeed(CLAMP_ZERO_SPEED);
    e1Stepper.setSpeed(CLAMP_ZERO_SPEED);
    
    unsigned long escapeStart = millis();
    while (!digitalRead(CLAMP_SENSOR_PIN) && (millis() - escapeStart < 5000)) {
      e0Stepper.tickManual();
      e1Stepper.tickManual();
      yield();
    }
    
    e0Stepper.brake();
    e1Stepper.brake();
    delay(100);
  }
  
  // Движение к датчику
  Serial.println(F("Движение к датчику..."));
  e0Stepper.setSpeed(-CLAMP_ZERO_SPEED);
  e1Stepper.setSpeed(-CLAMP_ZERO_SPEED);
  
  unsigned long startTime = millis();
  
  while (digitalRead(CLAMP_SENSOR_PIN)) {
    if (millis() - startTime >= HOMING_TIMEOUT) {
      Serial.println(F("Ошибка: Таймаут при движении к датчику"));
      e0Stepper.brake();
      e1Stepper.brake();
      clampInProgress = false;
      return false;
    }
    
    e0Stepper.tickManual();
    e1Stepper.tickManual();
    yield();
  }
  
  // Датчик сработал
  Serial.println(F("Датчик сработал"));
  e0Stepper.brake();
  e1Stepper.brake();
  
  // Установка нулевой позиции
  e0Stepper.setCurrent(0);
  e1Stepper.setCurrent(0);
  
  delay(200); // Стабилизация
  
  // Отъезд от датчика на позицию 100
  Serial.println(F("Отъезд от датчика..."));
  e0Stepper.setTarget(100);
  e1Stepper.setTarget(100);
  
  startTime = millis();
  
  while (!e0Stepper.ready() || !e1Stepper.ready()) {
    if (millis() - startTime >= 10000) {
      Serial.println(F("Ошибка: Таймаут отъезда от датчика"));
      e0Stepper.brake();
      e1Stepper.brake();
      clampInProgress = false;
      return false;
    }
    
    e0Stepper.tick();
    e1Stepper.tick();
    yield();
  }
  
  Serial.print(F("Обнуление завершено - E0: "));
  Serial.print(e0Stepper.getCurrent());
  Serial.print(F(", E1: "));
  Serial.println(e1Stepper.getCurrent());
  
  // Проверка корректности позиций
  if (e0Stepper.getCurrent() != 100 || e1Stepper.getCurrent() != 100) {
    Serial.println(F("Коррекция позиций до 100"));
    e0Stepper.setCurrent(100);
    e1Stepper.setCurrent(100);
  }
  
  clampInProgress = false;
  return true;
}

// ============== ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ ==============
bool moveMultiToPosition(long position) {
  return setStepperPosition(multiStepper, position);
}

bool moveRRightToPosition(long position) {
  return setStepperPosition(rRightStepper, position);
}

bool zeroAndMoveMulti(long position) {
  if (!homeStepperMotor(multiStepper, MULTI_ENDSTOP_PIN)) {
    Serial.println(F("Ошибка: не удалось выполнить обнуление Multi"));
    return false;
  }
  
  Serial.print(F("Перемещение Multi в позицию "));
  Serial.println(position);
  return setStepperPosition(multiStepper, position);
}

bool zeroAndMoveRRight(long position) {
  if (!homeStepperMotor(rRightStepper, RRIGHT_ENDSTOP_PIN)) {
    Serial.println(F("Ошибка: не удалось выполнить обнуление RRight"));
    return false;
  }
  
  Serial.print(F("Перемещение RRight в позицию "));
  Serial.println(position);
  return setStepperPosition(rRightStepper, position);
} 