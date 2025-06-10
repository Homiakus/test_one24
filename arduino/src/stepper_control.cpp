/**
 * @file: stepper_control.cpp
 * @description: Модуль управления шаговыми двигателями с индивидуальными настройками для каждого двигателя
 * @dependencies: GyverStepper2, config.h
 * @created: 2024-12-19
 */

#include "stepper_control.h"
#include <Arduino.h>

// Создание экземпляров шаговых двигателей (используем GStepper2)
GStepper2<STEPPER2WIRE> multiStepper(MULTI_STEPS_PER_REVOLUTION, MULTI_STEP_PIN, MULTI_DIR_PIN, MULTI_ENABLE_PIN);
GStepper2<STEPPER2WIRE> multizoneSteper(MULTIZONE_STEPS_PER_REVOLUTION, MULTIZONE_STEP_PIN, MULTIZONE_DIR_PIN, MULTIZONE_ENABLE_PIN);
GStepper2<STEPPER2WIRE> rRightStepper(RRIGHT_STEPS_PER_REVOLUTION, RRIGHT_STEP_PIN, RRIGHT_DIR_PIN, RRIGHT_ENABLE_PIN);
GStepper2<STEPPER2WIRE> e0Stepper(E0_STEPS_PER_REVOLUTION, E0_STEP_PIN, E0_DIR_PIN, E0_ENABLE_PIN);
GStepper2<STEPPER2WIRE> e1Stepper(E1_STEPS_PER_REVOLUTION, E1_STEP_PIN, E1_DIR_PIN, E1_ENABLE_PIN);

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

// ============== КОНФИГУРАЦИЯ ДВИГАТЕЛЕЙ ==============
StepperConfig getStepperConfig(StepperType type) {
  StepperConfig config;
  
  switch (type) {
    case STEPPER_MULTI:
      config.stepPin = MULTI_STEP_PIN;
      config.dirPin = MULTI_DIR_PIN;
      config.enablePin = MULTI_ENABLE_PIN;
      config.endstopPin = MULTI_ENDSTOP_PIN;
      config.stepsPerRevolution = MULTI_STEPS_PER_REVOLUTION;
      config.maxSpeed = MULTI_MAX_SPEED;
      config.acceleration = MULTI_ACCELERATION;
      config.homingSpeed = MULTI_HOMING_SPEED;
      config.endstopTypeNPN = MULTI_ENDSTOP_TYPE_NPN;
      config.powerAlwaysOn = MULTI_POWER_ALWAYS_ON;
      break;
      
    case STEPPER_MULTIZONE:
      config.stepPin = MULTIZONE_STEP_PIN;
      config.dirPin = MULTIZONE_DIR_PIN;
      config.enablePin = MULTIZONE_ENABLE_PIN;
      config.endstopPin = MULTIZONE_ENDSTOP_PIN;
      config.stepsPerRevolution = MULTIZONE_STEPS_PER_REVOLUTION;
      config.maxSpeed = MULTIZONE_MAX_SPEED;
      config.acceleration = MULTIZONE_ACCELERATION;
      config.homingSpeed = MULTIZONE_HOMING_SPEED;
      config.endstopTypeNPN = MULTIZONE_ENDSTOP_TYPE_NPN;
      config.powerAlwaysOn = MULTIZONE_POWER_ALWAYS_ON;
      break;
      
    case STEPPER_RRIGHT:
      config.stepPin = RRIGHT_STEP_PIN;
      config.dirPin = RRIGHT_DIR_PIN;
      config.enablePin = RRIGHT_ENABLE_PIN;
      config.endstopPin = RRIGHT_ENDSTOP_PIN;
      config.stepsPerRevolution = RRIGHT_STEPS_PER_REVOLUTION;
      config.maxSpeed = RRIGHT_MAX_SPEED;
      config.acceleration = RRIGHT_ACCELERATION;
      config.homingSpeed = RRIGHT_HOMING_SPEED;
      config.endstopTypeNPN = RRIGHT_ENDSTOP_TYPE_NPN;
      config.powerAlwaysOn = RRIGHT_POWER_ALWAYS_ON;
      break;
      
    case STEPPER_E0:
      config.stepPin = E0_STEP_PIN;
      config.dirPin = E0_DIR_PIN;
      config.enablePin = E0_ENABLE_PIN;
      config.endstopPin = CLAMP_SENSOR_PIN; // Используется для clamp_zero
      config.stepsPerRevolution = E0_STEPS_PER_REVOLUTION;
      config.maxSpeed = E0_MAX_SPEED;
      config.acceleration = E0_ACCELERATION;
      config.homingSpeed = E0_HOMING_SPEED;
      config.endstopTypeNPN = E0_ENDSTOP_TYPE_NPN;
      config.powerAlwaysOn = E0_POWER_ALWAYS_ON;
      break;
      
    case STEPPER_E1:
      config.stepPin = E1_STEP_PIN;
      config.dirPin = E1_DIR_PIN;
      config.enablePin = E1_ENABLE_PIN;
      config.endstopPin = CLAMP_SENSOR_PIN; // Используется для clamp_zero
      config.stepsPerRevolution = E1_STEPS_PER_REVOLUTION;
      config.maxSpeed = E1_MAX_SPEED;
      config.acceleration = E1_ACCELERATION;
      config.homingSpeed = E1_HOMING_SPEED;
      config.endstopTypeNPN = E1_ENDSTOP_TYPE_NPN;
      config.powerAlwaysOn = E1_POWER_ALWAYS_ON;
      break;
  }
  
  return config;
}

GStepper2<STEPPER2WIRE>* getStepperByType(StepperType type) {
  switch (type) {
    case STEPPER_MULTI: return &multiStepper;
    case STEPPER_MULTIZONE: return &multizoneSteper;
    case STEPPER_RRIGHT: return &rRightStepper;
    case STEPPER_E0: return &e0Stepper;
    case STEPPER_E1: return &e1Stepper;
    default: return nullptr;
  }
}

void applyStepperConfig(GStepper2<STEPPER2WIRE>& stepper, const StepperConfig& config) {
  Serial.print(F("Активация двигателя... "));
  
  // Диагностика enable пина ДО активации
  Serial.print(F("Enable pin "));
  Serial.print(config.enablePin);
  Serial.print(F(" ДО активации: "));
  Serial.print(digitalRead(config.enablePin));
  
  stepper.enable();
  
  // Небольшая задержка для стабилизации
  delay(10);
  
  // Диагностика enable пина ПОСЛЕ активации
  Serial.print(F(", ПОСЛЕ активации: "));
  Serial.print(digitalRead(config.enablePin));
  
  stepper.setMaxSpeed(config.maxSpeed);
  stepper.setAcceleration(config.acceleration);
  
  Serial.print(F(". Конфигурация: скорость="));
  Serial.print(config.maxSpeed);
  Serial.print(F(", ускорение="));
  Serial.print(config.acceleration);
  Serial.print(F(", шагов/оборот="));
  Serial.print(config.stepsPerRevolution);
  Serial.print(F(", enable_pin="));
  Serial.print(config.enablePin);
  Serial.println(F(" [АКТИВИРОВАН]"));
}

bool readEndstopWithType(int endstopPin, bool isNPN) {
  bool rawState = digitalRead(endstopPin);
  
  if (isNPN) {
    // NPN: сработал = LOW (0), не сработал = HIGH (1)
    return !rawState;
  } else {
    // PNP: сработал = HIGH (1), не сработал = LOW (0) 
    return rawState;
  }
}

// ============== ИНИЦИАЛИЗАЦИЯ СИСТЕМЫ ==============
void initializeSteppers() {
  Serial.println(F("Инициализация шаговых двигателей с индивидуальными настройками..."));
  
  // Настройка пинов для всех двигателей
  pinMode(MULTI_STEP_PIN, OUTPUT);
  pinMode(MULTI_DIR_PIN, OUTPUT);
  pinMode(MULTI_ENABLE_PIN, OUTPUT); // Добавлено обратно для корректной работы
  
  pinMode(MULTIZONE_STEP_PIN, OUTPUT);
  pinMode(MULTIZONE_DIR_PIN, OUTPUT);
  pinMode(MULTIZONE_ENABLE_PIN, OUTPUT); // Добавлено обратно для корректной работы
  
  pinMode(RRIGHT_STEP_PIN, OUTPUT);
  pinMode(RRIGHT_DIR_PIN, OUTPUT);
  pinMode(RRIGHT_ENABLE_PIN, OUTPUT); // Добавлено обратно для корректной работы
  
  pinMode(E0_STEP_PIN, OUTPUT);
  pinMode(E0_DIR_PIN, OUTPUT);
  pinMode(E0_ENABLE_PIN, OUTPUT); // Добавлено обратно для корректной работы
  
  pinMode(E1_STEP_PIN, OUTPUT);
  pinMode(E1_DIR_PIN, OUTPUT);
  pinMode(E1_ENABLE_PIN, OUTPUT); // Добавлено обратно для корректной работы
  
  // НЕ устанавливаем значения enable пинов - это делает GyverStepper2 при stepper.enable()
  
  // Настройка датчиков
  pinMode(MULTI_ENDSTOP_PIN, INPUT_PULLUP);
  pinMode(MULTIZONE_ENDSTOP_PIN, INPUT_PULLUP);
  pinMode(RRIGHT_ENDSTOP_PIN, INPUT_PULLUP);
  pinMode(CLAMP_SENSOR_PIN, INPUT_PULLUP);
  
  // Применение индивидуальных конфигураций
  Serial.println(F("Применение конфигураций двигателей:"));
  
  Serial.print(F("Multi: "));
  applyStepperConfig(multiStepper, getStepperConfig(STEPPER_MULTI));
  
  Serial.print(F("Multizone: "));
  applyStepperConfig(multizoneSteper, getStepperConfig(STEPPER_MULTIZONE));
  
  Serial.print(F("RRight: "));
  applyStepperConfig(rRightStepper, getStepperConfig(STEPPER_RRIGHT));
  
  Serial.print(F("E0: "));
  applyStepperConfig(e0Stepper, getStepperConfig(STEPPER_E0));
  
  Serial.print(F("E1: "));
  applyStepperConfig(e1Stepper, getStepperConfig(STEPPER_E1));
  
  Serial.println(F("Инициализация шаговых двигателей завершена"));
  Serial.println(F("Enable пины настроены, управляются библиотекой GyverStepper2"));
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
  
  // Определяем какой это двигатель и получаем его конфигурацию
  StepperType stepperType;
  if (&stepper == &multiStepper) stepperType = STEPPER_MULTI;
  else if (&stepper == &multizoneSteper) stepperType = STEPPER_MULTIZONE;
  else if (&stepper == &rRightStepper) stepperType = STEPPER_RRIGHT;
  else if (&stepper == &e0Stepper) stepperType = STEPPER_E0;
  else if (&stepper == &e1Stepper) stepperType = STEPPER_E1;
  else {
    Serial.println(F("Ошибка: Неизвестный двигатель"));
    return false;
  }
  
  StepperConfig config = getStepperConfig(stepperType);
  
  String motorName = "UNKNOWN";
  if (&stepper == &multiStepper) motorName = "Multi";
  else if (&stepper == &multizoneSteper) motorName = "Multizone";
  else if (&stepper == &rRightStepper) motorName = "RRight";
  else if (&stepper == &e0Stepper) motorName = "E0";
  else if (&stepper == &e1Stepper) motorName = "E1";
  
  long currentPos = stepper.getCurrent();
  Serial.print(F("ДИАГНОСТИКА "));
  Serial.print(motorName);
  Serial.print(F(": текущая позиция="));
  Serial.print(currentPos);
  Serial.print(F(", целевая="));
  Serial.print(position);
  Serial.print(F(", расстояние="));
  Serial.println(abs(position - currentPos));
  
  // Включаем питание двигателя
  enableStepper(stepper, config);
  
  Serial.print(F("Движение к позиции: "));
  Serial.println(position);
  
  stepper.setTarget(position);
  
  // Блокирующее ожидание завершения движения с подробной диагностикой
  unsigned long startTime = millis();
  unsigned long lastProgressTime = 0;
  const unsigned long moveTimeout = HOMING_TIMEOUT; // Используем общий таймаут
  
  while (!stepper.ready()) {
    unsigned long currentTime = millis();
    
    // Проверка таймаута
    if (currentTime - startTime > moveTimeout) {
      Serial.print(F("ДИАГНОСТИКА ТАЙМАУТА "));
      Serial.print(motorName);
      Serial.print(F(": время="));
      Serial.print(currentTime - startTime);
      Serial.print(F("мс, текущая позиция="));
      Serial.print(stepper.getCurrent());
      Serial.print(F(", цель="));
      Serial.println(stepper.getTarget());
      Serial.println(F("Ошибка: Таймаут движения"));
      stepper.brake();
      
      // Выключаем питание в случае ошибки
      disableStepper(stepper, config);
      return false;
    }
    
    // Периодический вывод прогресса каждые 2 секунды
    if (currentTime - lastProgressTime >= 2000) {
      lastProgressTime = currentTime;
      Serial.print(F("ПРОГРЕСС "));
      Serial.print(motorName);
      Serial.print(F(": позиция="));
      Serial.print(stepper.getCurrent());
      Serial.print(F("/"));
      Serial.print(stepper.getTarget());
      Serial.print(F(", время="));
      Serial.print((currentTime - startTime) / 1000);
      Serial.println(F("с"));
    }
    
    stepper.tick();
    yield();
  }
  
  Serial.print(F("Движение завершено. Текущая позиция: "));
  Serial.println(stepper.getCurrent());
  
  // Выключаем питание для двигателей с временным питанием
  disableStepper(stepper, config);
  
  return true;
}

bool homeStepperMotor(GStepper2<STEPPER2WIRE>& stepper, int endstopPin) {
  // Проверка занятости двигателей E0 и E1
  if ((&stepper == &e0Stepper || &stepper == &e1Stepper) && clampInProgress) {
    Serial.println(F("Ошибка: Двигатели E0/E1 заняты командой clamp"));
    return false;
  }
  
  // Определяем тип двигателя для получения правильной конфигурации
  StepperType stepperType;
  if (&stepper == &multiStepper) stepperType = STEPPER_MULTI;
  else if (&stepper == &multizoneSteper) stepperType = STEPPER_MULTIZONE;
  else if (&stepper == &rRightStepper) stepperType = STEPPER_RRIGHT;
  else if (&stepper == &e0Stepper) stepperType = STEPPER_E0;
  else if (&stepper == &e1Stepper) stepperType = STEPPER_E1;
  else return false;
  
  StepperConfig config = getStepperConfig(stepperType);
  return homeStepperMotorWithConfig(stepper, config);
}

bool homeStepperMotorWithConfig(GStepper2<STEPPER2WIRE>& stepper, const StepperConfig& config) {
  Serial.println(F("Начало процедуры хоминга с индивидуальными настройками..."));
  
  // Определяем название двигателя для диагностики
  String motorName = "UNKNOWN";
  if (&stepper == &multiStepper) motorName = "Multi";
  else if (&stepper == &multizoneSteper) motorName = "Multizone";
  else if (&stepper == &rRightStepper) motorName = "RRight";
  else if (&stepper == &e0Stepper) motorName = "E0";
  else if (&stepper == &e1Stepper) motorName = "E1";
  
  Serial.print(F("Хоминг "));
  Serial.print(motorName);
  Serial.print(F(" со скоростью "));
  Serial.print(config.homingSpeed);
  Serial.print(F(" steps/sec, датчик тип: "));
  Serial.println(config.endstopTypeNPN ? "NPN" : "PNP");
  
  // Остановка двигателя
  stepper.brake();
  delay(100);
  
  // Настройка параметров для хоминга
  stepper.setMaxSpeed(config.homingSpeed);
  stepper.setAcceleration(config.acceleration);
  
  // Проверка начального состояния датчика
  bool initialEndstopState = readEndstopWithType(config.endstopPin, config.endstopTypeNPN);
  Serial.print(F("Начальное состояние датчика: "));
  Serial.println(initialEndstopState ? "СРАБОТАЛ" : "НЕ СРАБОТАЛ");
  
  // Если датчик уже сработал, сначала отъезжаем
  if (initialEndstopState) {
    Serial.println(F("Датчик уже сработал, отъезжаем..."));
    stepper.setTarget(stepper.getCurrent() + 200); // Отъезжаем на 200 шагов
    
    unsigned long escapeStart = millis();
    while (!stepper.ready() && (millis() - escapeStart < 10000)) {
      stepper.tick();
      yield();
    }
    
    stepper.brake();
    delay(100);
    
    // Проверяем, что датчик отпустился
    if (readEndstopWithType(config.endstopPin, config.endstopTypeNPN)) {
      Serial.println(F("Ошибка: не удалось отъехать от датчика"));
      return false;
    }
    Serial.println(F("Успешно отъехали от датчика"));
  }
  
  // Движение к концевику
  Serial.println(F("Движемся к концевику..."));
  long startPosition = stepper.getCurrent();
  stepper.setTarget(startPosition - 50000); // Движемся на много шагов назад
  
  unsigned long startTime = millis();
  unsigned long lastProgressTime = 0;
  
  while (!stepper.ready()) {
    unsigned long currentTime = millis();
    
    // Проверка таймаута
    if (currentTime - startTime >= HOMING_TIMEOUT) {
      stepper.brake();
      Serial.println(F("Ошибка: Таймаут хоминга"));
      return false;
    }
    
    // Проверка датчика
    if (readEndstopWithType(config.endstopPin, config.endstopTypeNPN)) {
      Serial.println(F("Концевик сработал!"));
      stepper.brake();
      break;
    }
    
    // Периодический прогресс
    if (currentTime - lastProgressTime >= 3000) {
      lastProgressTime = currentTime;
      Serial.print(F("ХОМИНГ "));
      Serial.print(motorName);
      Serial.print(F(": позиция="));
      Serial.print(stepper.getCurrent());
      Serial.print(F(", время="));
      Serial.print((currentTime - startTime) / 1000);
      Serial.println(F("с"));
    }
    
    stepper.tick();
    yield();
  }
  
  // Проверяем, что концевик действительно сработал
  if (!readEndstopWithType(config.endstopPin, config.endstopTypeNPN)) {
    Serial.println(F("Ошибка: концевик не сработал за отведенное время"));
    return false;
  }
  
  // Сброс позиции в 0
  stepper.reset();
  Serial.print(F("Концевик сработал (тип: "));
  Serial.print(config.endstopTypeNPN ? "NPN" : "PNP");
  Serial.println(F("), позиция сброшена в 0"));
  
  delay(200); // Стабилизация
  
  // Отъезд от концевика
  Serial.println(F("Отъезжаем от концевика..."));
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
  
  // Финальная проверка
  if (readEndstopWithType(config.endstopPin, config.endstopTypeNPN)) {
    Serial.println(F("Предупреждение: датчик все еще активен после отъезда"));
  }
  
  stepper.reset(); // Устанавливаем новую нулевую точку
  Serial.print(F("Хоминг "));
  Serial.print(motorName);
  Serial.println(F(" завершен успешно"));
  return true;
}

// ============== ФУНКЦИИ ДЛЯ ДВИГАТЕЛЕЙ E0/E1 ==============
bool clampMotors(long targetPosition) {
  if (clampInProgress) {
    Serial.println(F("Ошибка: Команда clamp уже выполняется"));
    return false;
  }
  
  clampInProgress = true;
  Serial.println(F("Начало выполнения команды clamp с временным питанием"));
  
  // Получение конфигураций для E0 и E1
  StepperConfig e0Config = getStepperConfig(STEPPER_E0);
  StepperConfig e1Config = getStepperConfig(STEPPER_E1);
  
  // Включаем питание двигателей
  enableStepper(e0Stepper, e0Config);
  enableStepper(e1Stepper, e1Config);
  
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
  
  // Настройка параметров движения из конфигурации
  e0Stepper.setMaxSpeed(e0Config.maxSpeed);
  e1Stepper.setMaxSpeed(e1Config.maxSpeed);
  e0Stepper.setAcceleration(e0Config.acceleration);
  e1Stepper.setAcceleration(e1Config.acceleration);
  
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
      
      // Выключаем питание
      disableStepper(e0Stepper, e0Config);
      disableStepper(e1Stepper, e1Config);
      
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
  
  // Выключаем питание двигателей
  disableStepper(e0Stepper, e0Config);
  disableStepper(e1Stepper, e1Config);
  
  clampInProgress = false;
  return true;
}

bool clampZeroMotors() {
  if (clampInProgress) {
    Serial.println(F("Ошибка: Команда clamp уже выполняется"));
    return false;
  }
  
  clampInProgress = true;
  Serial.println(F("Начало процедуры clamp_zero с временным питанием"));
  
  // Получение конфигураций для E0 и E1
  StepperConfig e0Config = getStepperConfig(STEPPER_E0);
  StepperConfig e1Config = getStepperConfig(STEPPER_E1);
  
  // Включаем питание двигателей
  enableStepper(e0Stepper, e0Config);
  enableStepper(e1Stepper, e1Config);
  
  // Остановка двигателей
  e0Stepper.brake();
  e1Stepper.brake();
  delay(100);
  
  // Настройка параметров из конфигурации
  e0Stepper.setMaxSpeed(e0Config.homingSpeed);
  e1Stepper.setMaxSpeed(e1Config.homingSpeed);
  e0Stepper.setAcceleration(e0Config.acceleration);
  e1Stepper.setAcceleration(e1Config.acceleration);
  
  // Начальная проверка датчика с учетом типа
  if (readEndstopWithType(CLAMP_SENSOR_PIN, e0Config.endstopTypeNPN)) {
    Serial.println(F("Датчик уже активен, начинаю отъезд"));
    // Если датчик уже нажат, сначала отъезжаем
    e0Stepper.setTarget(e0Stepper.getCurrent() + 200);
    e1Stepper.setTarget(e1Stepper.getCurrent() + 200);
    
    unsigned long escapeStart = millis();
    while ((!e0Stepper.ready() || !e1Stepper.ready()) && (millis() - escapeStart < 5000)) {
      e0Stepper.tick();
      e1Stepper.tick();
      yield();
    }
    
    e0Stepper.brake();
    e1Stepper.brake();
    delay(100);
  }
  
  // Движение к датчику
  Serial.print(F("Движение к датчику (тип: "));
  Serial.print(e0Config.endstopTypeNPN ? "NPN" : "PNP");
  Serial.println(F(")..."));
  
  long startE0 = e0Stepper.getCurrent();
  long startE1 = e1Stepper.getCurrent();
  e0Stepper.setTarget(startE0 - 5000);
  e1Stepper.setTarget(startE1 - 5000);
  
  unsigned long startTime = millis();
  
  while (!readEndstopWithType(CLAMP_SENSOR_PIN, e0Config.endstopTypeNPN)) {
    if (millis() - startTime >= HOMING_TIMEOUT) {
      Serial.println(F("Ошибка: Таймаут при движении к датчику"));
      e0Stepper.brake();
      e1Stepper.brake();
      
      // Выключаем питание
      disableStepper(e0Stepper, e0Config);
      disableStepper(e1Stepper, e1Config);
      
      clampInProgress = false;
      return false;
    }
    
    e0Stepper.tick();
    e1Stepper.tick();
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
      
      // Выключаем питание
      disableStepper(e0Stepper, e0Config);
      disableStepper(e1Stepper, e1Config);
      
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
  
  // Выключаем питание двигателей
  disableStepper(e0Stepper, e0Config);
  disableStepper(e1Stepper, e1Config);
  
  clampInProgress = false;
  return true;
}

// ============== ИНДИВИДУАЛЬНЫЕ ФУНКЦИИ ДЛЯ E0 И E1 ==============
bool moveE0(long position) {
  Serial.print(F("Индивидуальное движение E0 к позиции: "));
  Serial.println(position);
  return setStepperPosition(e0Stepper, position);
}

bool moveE1(long position) {
  Serial.print(F("Индивидуальное движение E1 к позиции: "));
  Serial.println(position);
  return setStepperPosition(e1Stepper, position);
}

bool homeE0() {
  Serial.println(F("Индивидуальный хоминг E0..."));
  return homeStepperMotor(e0Stepper, CLAMP_SENSOR_PIN);
}

bool homeE1() {
  Serial.println(F("Индивидуальный хоминг E1..."));
  return homeStepperMotor(e1Stepper, CLAMP_SENSOR_PIN);
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

// ============== УПРАВЛЕНИЕ ПИТАНИЕМ ДВИГАТЕЛЕЙ ==============
void enableStepper(GStepper2<STEPPER2WIRE>& stepper, const StepperConfig& config) {
  stepper.enable();
  Serial.print(F("Enable pin "));
  Serial.print(config.enablePin);
  Serial.print(F(": ВКЛЮЧЕН (режим: "));
  Serial.print(config.powerAlwaysOn ? "постоянный" : "временный");
  Serial.println(F(")"));
}

void disableStepper(GStepper2<STEPPER2WIRE>& stepper, const StepperConfig& config) {
  if (!config.powerAlwaysOn) {
    stepper.disable();
    Serial.print(F("Enable pin "));
    Serial.print(config.enablePin);
    Serial.println(F(": ВЫКЛЮЧЕН (временный режим)"));
  } else {
    Serial.print(F("Enable pin "));
    Serial.print(config.enablePin);
    Serial.println(F(": ОСТАЕТСЯ ВКЛЮЧЕННЫМ (постоянный режим)"));
  }
} 