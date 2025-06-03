#include "stepper_control.h"

// Создание экземпляров шаговых двигателей (используем GStepper2)
GStepper2<STEPPER2WIRE> multiStepper(200, MULTI_STEP_PIN, MULTI_DIR_PIN, MULTI_ENABLE_PIN);
GStepper2<STEPPER2WIRE> multizoneSteper(200, MULTIZONE_STEP_PIN, MULTIZONE_DIR_PIN, MULTIZONE_ENABLE_PIN);
GStepper2<STEPPER2WIRE> rRightStepper(200, RRIGHT_STEP_PIN, RRIGHT_DIR_PIN, RRIGHT_ENABLE_PIN);
GStepper2<STEPPER2WIRE> e0Stepper(200, E0_STEP_PIN, E0_DIR_PIN, E0_ENABLE_PIN);
GStepper2<STEPPER2WIRE> e1Stepper(200, E1_STEP_PIN, E1_DIR_PIN, E1_ENABLE_PIN);

// Флаг для предотвращения одновременного запуска команд, влияющих на E0/E1
bool clampInProgress = false;

// Функции для управления флагом clampInProgress
void resetClampFlag() {
  clampInProgress = false;
}

bool isClampInProgress() {
  return clampInProgress;
}

// Инициализация шаговых двигателей
void initializeSteppers() {
  // Проверяем пины для E0 и E1, чтобы убедиться, что они правильно определены
  pinMode(E0_STEP_PIN, OUTPUT);
  pinMode(E0_DIR_PIN, OUTPUT);
  pinMode(E0_ENABLE_PIN, OUTPUT);
  pinMode(E1_STEP_PIN, OUTPUT);
  pinMode(E1_DIR_PIN, OUTPUT);
  pinMode(E1_ENABLE_PIN, OUTPUT);
  
  // Включаем двигатели (активный LOW)
  // digitalRead(E0_ENABLE_PIN); // Не нужно читать, просто устанавливаем
  digitalWrite(E0_ENABLE_PIN, LOW);
  digitalWrite(E1_ENABLE_PIN, LOW);
  
  // Настройка общих параметров для всех двигателей
  auto config = [](GStepper2<STEPPER2WIRE>& stepper) {
    stepper.enable(); // Включаем enable пин (если есть)
    // stepper.autoPower(true); // В GStepper2 этого метода нет, enable управляется явно
    // stepper.setRunMode(FOLLOW_POS); // В GStepper2 это режим по умолчанию при setTarget
    stepper.setMaxSpeed(500); // Устанавливаем максимальную скорость для движения к цели
    stepper.setAcceleration(800);
  };

  config(multiStepper);
  config(multizoneSteper);
  config(rRightStepper);
  config(e0Stepper);
  config(e1Stepper);
  
  // Настроим пин датчика для функции clamp_zero
  pinMode(CLAMP_SENSOR_PIN, INPUT_PULLUP);
}

// Установка позиции для двигателя (блокирующая, с GyverStepper2)
bool setStepperPosition(GStepper2<STEPPER2WIRE>& stepper, long position) {
  if (position == 0) {
    Serial.println(F("Ошибка: Нулевая позиция не допускается.")); 
    return false; 
  }
  
  // Проверка для E0 и E1, если они заняты командой clamp
  if ((&stepper == &e0Stepper || &stepper == &e1Stepper) && clampInProgress) {
      Serial.println(F("Ошибка: Двигатели E0/E1 заняты командой clamp."));
      return false;
  }
  
  stepper.setTarget(position); // Устанавливаем цель (абсолютную по умолчанию)
  
  // Блокирующий цикл ожидания завершения движения (используем ready() и tick())
  while (!stepper.ready()) { // Ждем, пока ready() не вернет true
    stepper.tick();
    yield(); 
  } 
  
  return true;
}

// Выполнение хоминга для двигателя (блокирующее, с GyverStepper2)
bool homeStepperMotor(GStepper2<STEPPER2WIRE>& stepper, int endstopPin) {
  
  // Проверка для E0 и E1, если они заняты командой clamp
  if ((&stepper == &e0Stepper || &stepper == &e1Stepper) && clampInProgress) {
      Serial.println(F("Ошибка: Двигатели E0/E1 заняты командой clamp."));
      return false;
  }
    
  // stepper.setRunMode(KEEP_SPEED); // В GStepper2 нет setRunMode, используем setSpeed для вращения
  stepper.setSpeed(-HOMING_SPEED); // Запускаем вращение с постоянной скоростью
  
  unsigned long startTime = millis();
  // Блокирующий цикл ожидания срабатывания концевика
  while (digitalRead(endstopPin)) {
    if (millis() - startTime >= HOMING_TIMEOUT) {
       stepper.brake(); // Останавливаем двигатель при таймауте
       Serial.println(F("Ошибка: Таймаут хоминга!"));
       return false; // Ошибка таймаута
    }
    stepper.tickManual(); // Используем tickManual, так как tick() остановит мотор после setSpeed()
    yield(); 
  }
  
  // Концевик сработал
  stepper.brake(); // Останавливаем вращение
  stepper.reset(); // Сбрасываем текущую позицию в 0
  delay(50); // Небольшая пауза
  
  // Отъезжаем от концевика на 100 шагов
  // stepper.setRunMode(FOLLOW_POS); // Режим по умолчанию
  stepper.setTarget(100); // Устанавливаем цель для отъезда
  
  // Блокирующий цикл ожидания завершения отъезда
  while (!stepper.ready()) {
      stepper.tick(); // Используем tick() для движения к цели
      yield();
  } 
  
  stepper.reset(); // Снова сбрасываем позицию в 0 после отъезда - теперь это наша нулевая точка
  
  return true;
}

// Синхронное вращение двигателей E0 и E1 на заданную абсолютную позицию (блокирующее, с GyverStepper2)
bool clampMotors(long targetPosition) {
  if (clampInProgress) {
    Serial.println(F("Ошибка: Команда clamp уже выполняется."));
    return false; 
  }
  
  clampInProgress = true; // Устанавливаем флаг занятости
  
  // Получаем текущие позиции
  long currentPositionE0 = e0Stepper.getCurrent();
  long currentPositionE1 = e1Stepper.getCurrent();
  
  Serial.print(F("Текущие позиции: E0=")); 
  Serial.print(currentPositionE0);
  Serial.print(F(", E1="));
  Serial.println(currentPositionE1);
  
  // Вычисляем относительное смещение, которое нужно сделать
  long relativeMove = targetPosition - currentPositionE0;
  
  Serial.print(F("Целевая позиция: "));
  Serial.print(targetPosition);
  Serial.print(F(", относительное смещение: "));
  Serial.println(relativeMove);
  
  // Если нет смещения, нечего делать
  if (relativeMove == 0) {
    Serial.println(F("Двигатели уже в заданной позиции."));
    clampInProgress = false;
    return true;
  }
  
  // Настраиваем параметры движения
  e0Stepper.setMaxSpeed(CLAMP_SPEED); 
  e1Stepper.setMaxSpeed(CLAMP_SPEED);
  e0Stepper.setAcceleration(CLAMP_ACCELERATION);
  e1Stepper.setAcceleration(CLAMP_ACCELERATION);
  
  // Остановка двигателей перед новым движением
  e0Stepper.brake();
  e1Stepper.brake();
  
  // Устанавливаем целевые позиции ОТНОСИТЕЛЬНО текущих
  // Это ключевое изменение - используем RELATIVE вместо ABSOLUTE
  e0Stepper.setTarget(relativeMove, RELATIVE);
  e1Stepper.setTarget(relativeMove, RELATIVE);
  
  Serial.print(F("Установлены новые целевые позиции: E0="));
  Serial.print(e0Stepper.getTarget());
  Serial.print(F(", E1="));
  Serial.println(e1Stepper.getTarget());
  
  // Рассчитываем таймаут в зависимости от расстояния
  unsigned long dynamicTimeout = HOMING_TIMEOUT + (abs(relativeMove) / 10) * 100;
  Serial.print(F("Расстояние: "));
  Serial.print(abs(relativeMove));
  Serial.print(F(", Расчетный таймаут: "));
  Serial.println(dynamicTimeout);
  
  // Добавляем таймаут для предотвращения зависания
  unsigned long startTime = millis();
  unsigned long lastUpdateTime = 0;
  
  // Блокирующий цикл ожидания завершения движения ОБОИХ двигателей
  bool e0Moving = true;
  bool e1Moving = true;
  
  while (e0Moving || e1Moving) {
    unsigned long currentTime = millis();
    
    // Проверяем таймаут
    if (currentTime - startTime >= dynamicTimeout) {
      Serial.println(F("Ошибка: Таймаут при выполнении команды clamp!"));
      e0Stepper.brake();
      e1Stepper.brake();
      clampInProgress = false;
      return false;
    }
    
    // Выполняем шаг для каждого двигателя
    e0Moving = e0Stepper.tick();
    e1Moving = e1Stepper.tick();
    
    // Периодически выводим информацию о прогрессе
    if (currentTime - lastUpdateTime >= 1000) {
      lastUpdateTime = currentTime;
      Serial.print(F("Прогресс: E0="));
      Serial.print(e0Stepper.getCurrent());
      Serial.print(F("/"));
      Serial.print(e0Stepper.getTarget());
      Serial.print(F(" (движется: "));
      Serial.print(e0Moving ? "да" : "нет");
      Serial.print(F("), E1="));
      Serial.print(e1Stepper.getCurrent());
      Serial.print(F("/"));
      Serial.print(e1Stepper.getTarget());
      Serial.print(F(" (движется: "));
      Serial.print(e1Moving ? "да" : "нет");
      Serial.println(F(")"));
    }
    
    // Небольшая задержка для предотвращения зависания
    yield();
  }
  
  Serial.print(F("Движение завершено. Новые позиции: E0="));
  Serial.print(e0Stepper.getCurrent());
  Serial.print(F(", E1="));
  Serial.println(e1Stepper.getCurrent());
  
  clampInProgress = false;
  return true;
}

// Обнуление двигателей E0 и E1 по датчику CLAMP_SENSOR_PIN (блокирующее, с GyverStepper2)
bool clampZeroMotors() {
  if (clampInProgress) {
    Serial.println(F("Ошибка: Команда clamp уже выполняется."));
    return false; 
  }
  
  clampInProgress = true; // Устанавливаем флаг занятости
  
  // Остановка двигателей перед началом хоминга
  e0Stepper.brake();
  e1Stepper.brake();
  
  Serial.println(F("Начало процедуры обнуления по датчику..."));
  
  // Устанавливаем параметры движения
  e0Stepper.setMaxSpeed(CLAMP_SPEED); 
  e1Stepper.setMaxSpeed(CLAMP_SPEED);
  e0Stepper.setAcceleration(CLAMP_ACCELERATION);
  e1Stepper.setAcceleration(CLAMP_ACCELERATION);
  
  // Настраиваем режим и скорость для хоминга
  e0Stepper.setSpeed(-CLAMP_ZERO_SPEED); 
  e1Stepper.setSpeed(-CLAMP_ZERO_SPEED);
  
  unsigned long startTime = millis();
  
  // Движение к датчику
  Serial.println(F("ClampZero: Движение к датчику..."));
  while (digitalRead(CLAMP_SENSOR_PIN)) { // Движемся, пока датчик НЕ нажат (HIGH)
    if (millis() - startTime >= HOMING_TIMEOUT) {
      Serial.println(F("Ошибка: Таймаут ClampZero при движении к датчику!"));
      e0Stepper.brake();
      e1Stepper.brake();
      clampInProgress = false;
      return false;
    }
    
    // Используем tickManual для движения с постоянной скоростью
    e0Stepper.tickManual(); 
    e1Stepper.tickManual();
    
    // Периодически сообщаем о текущем положении
    if ((millis() - startTime) % 1000 < 10) {
      Serial.print(F("Движение к датчику: E0="));
      Serial.print(e0Stepper.getCurrent());
      Serial.print(F(", E1="));
      Serial.println(e1Stepper.getCurrent());
    }
    
    yield();
  }
  
  // Датчик сработал - останавливаемся
  Serial.println(F("ClampZero: Датчик сработал. Остановка."));
  e0Stepper.brake();
  e1Stepper.brake();
  
  // Устанавливаем текущую позицию как "0" - это важно!
  // Теперь библиотека будет считать, что мы находимся в позиции 0
  e0Stepper.setCurrent(0);
  e1Stepper.setCurrent(0);
  
  Serial.println(F("ClampZero: Позиции установлены в 0."));
  
  delay(100); // Пауза для стабилизации
  
  // Отъезжаем от датчика на 100 шагов
  Serial.println(F("ClampZero: Отъезд от датчика..."));
  
  // Устанавливаем целевую позицию 100 ОТНОСИТЕЛЬНО текущей позиции (которая сейчас 0)
  e0Stepper.setTarget(100, RELATIVE);
  e1Stepper.setTarget(100, RELATIVE);
  
  // Обновляем startTime для нового таймаута
  startTime = millis();
  unsigned long lastUpdateTime = 0;
  
  // Блокирующий цикл ожидания завершения отъезда
  bool e0Moving = true;
  bool e1Moving = true;
  
  while (e0Moving || e1Moving) {
    unsigned long currentTime = millis();
    
    // Проверяем таймаут для отъезда
    if (currentTime - startTime >= HOMING_TIMEOUT) {
      Serial.println(F("Ошибка: Таймаут ClampZero при отъезде от датчика!"));
      e0Stepper.brake();
      e1Stepper.brake();
      clampInProgress = false;
      return false;
    }
    
    // Выполняем шаг для каждого двигателя
    e0Moving = e0Stepper.tick();
    e1Moving = e1Stepper.tick();
    
    // Периодически выводим информацию о прогрессе
    if (currentTime - lastUpdateTime >= 1000) {
      lastUpdateTime = currentTime;
      Serial.print(F("Отъезд от датчика: E0="));
      Serial.print(e0Stepper.getCurrent());
      Serial.print(F("/"));
      Serial.print(e0Stepper.getTarget());
      Serial.print(F(" (движется: "));
      Serial.print(e0Moving ? "да" : "нет");
      Serial.print(F("), E1="));
      Serial.print(e1Stepper.getCurrent());
      Serial.print(F("/"));
      Serial.print(e1Stepper.getTarget());
      Serial.print(F(" (движется: "));
      Serial.print(e1Moving ? "да" : "нет");
      Serial.println(F(")"));
    }
    
    yield();
  }
  
  // Движение завершено, теперь мы должны быть в позиции 100
  Serial.print(F("ClampZero: Обнуление завершено, текущие позиции: E0="));
  Serial.print(e0Stepper.getCurrent());
  Serial.print(F(", E1="));
  Serial.println(e1Stepper.getCurrent());
  
  // После обнуления текущая позиция двигателей должна быть 100
  // Убедимся, что это так
  if (e0Stepper.getCurrent() != 100 || e1Stepper.getCurrent() != 100) {
    Serial.println(F("ВНИМАНИЕ: Позиции после обнуления не 100! Исправляем..."));
    e0Stepper.setCurrent(100);
    e1Stepper.setCurrent(100);
  }
  
  Serial.println(F("ClampZero: Базовая позиция 100 установлена для обоих двигателей."));
  
  clampInProgress = false;
  return true;
} 