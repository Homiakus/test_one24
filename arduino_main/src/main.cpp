/**
 * @file: main_improved.cpp
 * @description: SECURE 5-motor control system using GyverPlanner - IMPROVED VERSION
 * @platform: PlatformIO / Arduino
 * @version: 3.0 - Security & Safety Enhanced
 * 
 * ПОДРОБНОЕ ОПИСАНИЕ:
 * Система управления 5 шаговыми двигателями с координированным движением.
 * Использует библиотеку GyverStepper для планирования траекторий.
 * Обеспечивает защиту от ошибок, таймауты операций и аварийную остановку.
 * 
 * ОСНОВНЫЕ КОМПОНЕНТЫ:
 * - 5 шаговых двигателей (X, Y, Z, E0, E1)
 * - 10 дополнительных контрольных пинов (насосы, клапаны, роторы)
 * - Концевые выключатели для каждого мотора
 * - Система валидации и безопасности
 */

 #include <Arduino.h>
 #include "GyverStepper.h"
 #include "GyverPlanner.h"
 #include "HX711.h"
 
 // ============================================
 // SECURITY & SAFETY CONFIGURATION
 // ============================================
 
 // Конфигурация безопасности буфера команд
 constexpr uint8_t MAX_COMMAND_LENGTH = 64;      // Максимальная длина команды (защита от переполнения)
 constexpr uint32_t HOMING_TIMEOUT_MS = 30000;   // Таймаут операции homing - 30 секунд
 constexpr uint32_t MOVE_TIMEOUT_MS = 60000;     // Таймаут операции движения - 60 секунд
 constexpr uint32_t EMERGENCY_CHECK_INTERVAL = 100; // Интервал проверки аварийных условий в мс
 constexpr uint32_t WATCHDOG_TIMEOUT_MS = 600000;  // Watchdog таймаут - 10 минут без активности
 
 constexpr uint8_t NUM_MOTORS = 5;  // Общее количество моторов в системе
 
 // Константы для весов и пинов
 constexpr uint8_t NUM_INPUT_PINS = 8;  // Количество входных пинов для мониторинга
 constexpr uint32_t WEIGHT_MEASUREMENT_TIMEOUT = 5000;  // Таймаут измерения веса (5 сек)
 
 // Идентификаторы моторов - используются для индексации массивов
 // Имена соответствуют физическим осям или функциям
 enum MotorID : uint8_t {
     MULTI = 0,      // X-axis - основная горизонтальная ось
     MULTIZONE = 1,  // Y-axis - вторая горизонтальная ось
     RRIGHT = 2,     // Z-axis - вертикальная ось
     E0 = 3,         // Экструдер/захват 0
     E1 = 4          // Экструдер/захват 1
 };
 
 // Идентификаторы контрольных пинов
 // Используются для управления дополнительным оборудованием
 enum ControlPin : uint8_t {
     PUMP = 0,       // Насос
     KL1, KL2,       // Клапаны 1 и 2
     WASTE,          // Слив/отходы
     ROTOR1, ROTOR2, ROTOR3, ROTOR4,  // Роторы 1-4
     HX711_SCK,      // Тактовый сигнал для датчика веса HX711
     HX711_DT        // Данные от датчика веса HX711
 };
 
 // Коды ошибок системы для диагностики проблем
 enum ErrorCode : uint8_t {
     ERROR_NONE = 0,              // Нет ошибок
     ERROR_INVALID_POSITION,      // Позиция выходит за допустимые пределы
     ERROR_INVALID_PIN,           // Неверный индекс пина
     ERROR_TIMEOUT,               // Превышено время выполнения операции
     ERROR_EMERGENCY_STOP,        // Активирована аварийная остановка
     ERROR_OUT_OF_BOUNDS,         // Выход за границы массива
     ERROR_BUFFER_OVERFLOW,       // Переполнение буфера команд
     ERROR_INVALID_COMMAND,       // Неизвестная или некорректная команда
     ERROR_WEIGHT_SENSOR,         // Ошибка датчика веса
     ERROR_RESERVOIR_OVERFLOW     // Переполнение резервуара
 };
 
 // ============================================
 // ENHANCED STRUCTURES
 // ============================================
 
 /**
  * Структура конфигурации мотора
  * Содержит все параметры для управления шаговым двигателем
  */
 struct MotorConfig {
     uint8_t stepPin;        // Пин для подачи импульсов шага
     uint8_t dirPin;         // Пин направления вращения
     uint8_t enablePin;      // Пин включения/выключения драйвера
     uint8_t homePin;        // Пин концевого выключателя
     const char* name;       // Имя мотора для отладки
     uint16_t maxSpeed;      // Максимальная скорость в шагах/сек
     uint16_t acceleration;  // Ускорение в шагах/сек²
     uint16_t homingSpeed;   // Скорость при поиске home позиции
     bool isNPN;            // true = NPN концевик (инвертированная логика)
     bool alwaysOn;         // true = мотор всегда включен (не отключается после движения)
     uint16_t stepsPerUnit; // Количество шагов на единицу измерения (мм, градус и т.д.)
     uint32_t maxSteps;     // Максимальное расстояние для поиска концевика
     uint16_t homeBackoff;  // Отход после срабатывания концевика
     uint16_t preBackoff;   // Предварительный отход перед homing
     // Параметры безопасности:
     float minPosition;     // Минимально допустимая позиция в единицах
     float maxPosition;     // Максимально допустимая позиция в единицах
     float safeSpeed;       // Безопасная скорость движения
 };
 
 /**
  * Структура конфигурации контрольного пина
  * Для управления дополнительным оборудованием
  */
 struct PinConfig {
     uint8_t pin;           // Номер физического пина Arduino
     const char* name;      // Имя для отладки
 };
 
 /**
  * Структура лимитов безопасности
  * Определяет допустимые диапазоны движения
  */
 struct SafetyLimits {
     float motorLimits[NUM_MOTORS][2];  // [мотор][min=0/max=1] позиции
     float maxSafeSpeed;                 // Максимальная безопасная скорость
     bool limitsEnabled;                 // Флаг активации проверки лимитов
 };
 
 /**
  * Менеджер таймаутов
  * Контролирует время выполнения операций
  */
 struct TimeoutManager {
     uint32_t startTime;        // Время начала операции (millis)
     uint32_t timeoutDuration;  // Длительность таймаута в мс
     bool active;               // Флаг активности таймаута
 };
 
 /**
  * Структура конфигурации входного пина
  * Для мониторинга состояния системы
  */
 struct InputPinConfig {
     uint8_t pin;           // Номер физического пина Arduino
     const char* name;      // Имя для отладки
     bool isActiveLow;      // true = активный низкий уровень
 };
 
 /**
  * Структура состояния весов
  * Управляет датчиком веса HX711
  */
 struct WeightSensor {
     HX711* sensor;         // Указатель на объект датчика
     float calibrationFactor; // Калибровочный коэффициент
     float offset;          // Смещение нуля
     bool isCalibrated;     // Флаг калибровки
     bool isMeasuring;      // Флаг активного измерения
     uint32_t lastMeasurement; // Время последнего измерения
 };
 
 // ============================================
 // ENHANCED MOTOR CONFIGURATIONS
 // ============================================
 
 /**
  * Массив конфигураций всех моторов системы
  * Содержит физические параметры и настройки безопасности
  * 
  * ВАЖНО: Эти параметры должны быть настроены под конкретное оборудование!
  */
 constexpr MotorConfig motors[NUM_MOTORS] = {
     // Multi (X-axis) - основная горизонтальная ось
     {A0, A1, 38, 14, "Multi(X)", 500, 500, 3000, false, true, 40, 16000, 1000, 1000, -200.0, 200.0, 300},
     
     // Multizone (Y-axis) - вторая горизонтальная ось
     // Имеет меньшую скорость и NPN концевик
     {A6, A7, A2, 2, "Multizone(Y)", 200, 300, 40, true, true, 80, 16000, 200, 0, -100.0, 100.0, 150},
     
     // RRight (Z-axis) - вертикальная ось
     // Высокая скорость homing, большой диапазон движения
     {46, 48, A8, 2, "RRight(Z)", 1000, 200, 10000, true, true, 200, 60000, 100, 60, -300.0, 0.0, 800},
     
     // E0 - первый экструдер/захват
     // Высокая скорость, отключается после использования
     {26, 28, 24, 15, "E0", 2000, 2000, 2000, true, false, 200, 16000, 200, 0, -50.0, 50.0, 1500},
     
     // E1 - второй экструдер/захват
     // Аналогичен E0, используется для парной работы
     {36, 34, 30, 15, "E1", 2000, 2000, 2000, true, false, 200, 16000, 200, 0, -50.0, 50.0, 1500}
 };
 
 /**
  * Массив конфигураций контрольных пинов
  * Управляет дополнительным оборудованием: насосами, клапанами, роторами
  */
 constexpr PinConfig controlPins[] = {
     {18, "PUMP"},      // Основной насос системы
     {8, "KL1"},        // Клапан 1 - входной
     {10, "KL2"},       // Клапан 2 - выходной
     {19, "WASTE"},     // Клапан слива/отходов
     {27, "ROTOR1"},    // Ротор 1 - перемешивание
     {29, "ROTOR2"},    // Ротор 2
     {23, "ROTOR3"},    // Ротор 3
     {25, "ROTOR4"},    // Ротор 4
     {42, "HX711_SCK"}, // Тактовый сигнал датчика веса
     {40, "HX711_DT"}   // Данные датчика веса
 };
 
 // Вычисляем количество контрольных пинов на этапе компиляции
 constexpr uint8_t NUM_CTRL_PINS = sizeof(controlPins) / sizeof(PinConfig);
 
 /**
  * Массив конфигураций входных пинов
  * Для мониторинга состояния системы
  */
 constexpr InputPinConfig inputPins[] = {
     {3, "INPUT1", false},      // Входной пин 1
     {4, "INPUT2", false},      // Входной пин 2
     {5, "INPUT3", false},      // Входной пин 3
     {6, "INPUT4", false},      // Входной пин 4
     {7, "INPUT5", false},      // Входной пин 5
     {9, "INPUT6", false},      // Входной пин 6
     {11, "INPUT7", false},     // Входной пин 7
     {12, "INPUT8", false}      // Входной пин 8
 };
 
 // ============================================
 // ENHANCED GLOBAL OBJECTS
 // ============================================
 
 /**
  * Массив объектов Stepper для управления моторами
  * Каждый объект содержит текущую позицию и управляет пинами STEP/DIR
  */
 Stepper<STEPPER2WIRE> steppers[NUM_MOTORS] = {
     Stepper<STEPPER2WIRE>(motors[0].stepPin, motors[0].dirPin),
     Stepper<STEPPER2WIRE>(motors[1].stepPin, motors[1].dirPin),
     Stepper<STEPPER2WIRE>(motors[2].stepPin, motors[2].dirPin),
     Stepper<STEPPER2WIRE>(motors[3].stepPin, motors[3].dirPin),
     Stepper<STEPPER2WIRE>(motors[4].stepPin, motors[4].dirPin)
 };
 
 // Планировщик движения - координирует движение всех моторов
 GPlanner<STEPPER2WIRE, NUM_MOTORS> planner;
 
 /**
  * Глобальное состояние системы
  * volatile - для переменных, изменяемых в прерываниях или критических секциях
  */
 struct SystemState {
     volatile bool motorsEnabled = true;       // Флаг включения моторов
     volatile bool homingActive = false;       // Флаг выполнения homing
     volatile bool emergencyStop = false;      // Флаг аварийной остановки
     volatile ErrorCode lastError = ERROR_NONE; // Последний код ошибки
     volatile bool commandInProgress = false;  // Флаг выполнения команды
     uint32_t lastActivityTime = 0;           // Время последней активности (для watchdog)
     
     // БЕЗОПАСНОСТЬ: Фиксированный буфер вместо динамической String
     char inputBuffer[MAX_COMMAND_LENGTH];    // Буфер для накопления команды
     uint8_t inputBufferPos = 0;              // Текущая позиция в буфере
     bool commandReady = false;               // Флаг готовности команды к обработке
 } state;
 
 // Глобальные менеджеры безопасности
 SafetyLimits safetyLimits;      // Лимиты движения
 TimeoutManager timeoutManager;   // Менеджер таймаутов
 
 // Глобальные объекты для весов и мониторинга
 HX711 weightSensor; // Датчик веса
 WeightSensor weightManager = {&weightSensor, 1.0, 0.0, false, false, 0};    // Менеджер весов
 
 // ============================================
 // FORWARD DECLARATIONS
 // ============================================
 
 // Функции обработки команд
 void processCommand(const char* command);
 void parseHomingFlags(const char* args, bool flags[]);
 void parseMoveCommand(const char* args, float positions[], bool active[]);
 void printSystemStatus();
 void printHelp();
 void printVersion();
 
 // Функции движения
 void coordinatedMove(float positions[], bool active[]);
 void homeMotors(bool flags[]);
 void performBackoff(const char* phase, int32_t positions[]);
 
 // Функции безопасности
 void emergencyStop();
 void checkEmergency();
 void startTimeout(uint32_t duration);
 bool isTimeoutExpired();
 void clearTimeout();
 
 // Функции управления моторами
 void setMotorPower(uint8_t motor, bool enable);
 void enableAllMotors();
 void disableTemporaryMotors();
 
 // Функции управления пинами
 void controlPin(uint8_t pinIndex, bool state);
 
 // Вспомогательные функции
 void clearCommandBuffer();
 bool validateMotorPosition(uint8_t motor, float position);
 bool validatePinIndex(int pinIndex);
 bool isPositionSafe(uint8_t motor, float position);
 bool validateMove(float positions[], bool active[]);
 inline int32_t toSteps(uint8_t motor, float units);
 inline float toUnits(uint8_t motor, int32_t steps);
 bool readEndstop(uint8_t motor);
 
 // Функции мониторинга и весов
 void readInputPins();
 void startWeightMeasurement();
 void stopWeightMeasurement();
 void calibrateWeightSensor();
 void zeroWeightSensor();
 float getWeight();
 bool checkReservoirOverflow();
 
 // ============================================
 // SECURITY & VALIDATION FUNCTIONS
 // ============================================
 
 /**
  * Безопасная очистка буфера команд
  * Использует критическую секцию для защиты от гонок
  */
 void clearCommandBuffer() {
     noInterrupts(); // Отключаем прерывания для атомарности операции
     memset(state.inputBuffer, 0, MAX_COMMAND_LENGTH);  // Обнуляем весь буфер
     state.inputBufferPos = 0;                          // Сбрасываем позицию
     state.commandReady = false;                        // Сбрасываем флаг готовности
     interrupts();   // Включаем прерывания обратно
 }
 
 /**
  * Валидация позиции мотора
  * Проверяет, что позиция находится в допустимых пределах
  * 
  * @param motor - индекс мотора
  * @param position - проверяемая позиция
  * @return true если позиция валидна
  */
 bool validateMotorPosition(uint8_t motor, float position) {
     // Проверка корректности индекса мотора
     if (motor >= NUM_MOTORS) return false;
     
     // Проверка на специальные значения (Not a Number, Infinity)
     if (isnan(position) || isinf(position)) return false;
     
     // Проверка диапазона позиции
     return (position >= motors[motor].minPosition && 
             position <= motors[motor].maxPosition);
 }
 
 /**
  * Валидация индекса контрольного пина
  * 
  * @param pinIndex - проверяемый индекс
  * @return true если индекс корректен
  */
 bool validatePinIndex(int pinIndex) {
     return (pinIndex >= 0 && pinIndex < NUM_CTRL_PINS);
 }
 
 /**
  * Проверка безопасности позиции с установкой кода ошибки
  * 
  * @param motor - индекс мотора
  * @param position - проверяемая позиция
  * @return true если позиция безопасна
  */
 bool isPositionSafe(uint8_t motor, float position) {
     if (!validateMotorPosition(motor, position)) {
         state.lastError = ERROR_INVALID_POSITION;
         return false;
     }
     
     // Здесь можно добавить дополнительные проверки:
     // - Проверка на коллизии между осями
     // - Проверка на запрещенные зоны
     // - Проверка на механические ограничения
     
     return true;
 }
 
 /**
  * Валидация полной команды движения
  * Проверяет все активные оси перед началом движения
  * 
  * @param positions - массив целевых позиций
  * @param active - массив флагов активности осей
  * @return true если движение безопасно
  */
 bool validateMove(float positions[], bool active[]) {
     for (uint8_t i = 0; i < NUM_MOTORS; i++) {
         if (active[i] && !isPositionSafe(i, positions[i])) {
             // Выводим детальную информацию об ошибке
             Serial.print("ERROR: Invalid position for ");
             Serial.print(motors[i].name);
             Serial.print(": ");
             Serial.println(positions[i]);
             return false;
         }
     }
     return true;
 }
 
 // ============================================
 // TIMEOUT & EMERGENCY MANAGEMENT  
 // ============================================
 
 /**
  * Запуск таймаута для контроля длительности операции
  * 
  * @param duration - длительность таймаута в миллисекундах
  */
 void startTimeout(uint32_t duration) {
     timeoutManager.startTime = millis();
     timeoutManager.timeoutDuration = duration;
     timeoutManager.active = true;
 }
 
 /**
  * Проверка истечения таймаута
  * 
  * @return true если таймаут истёк
  */
 bool isTimeoutExpired() {
     if (!timeoutManager.active) return false;
     
     // Проверяем с учётом переполнения millis() (каждые ~49 дней)
     return (millis() - timeoutManager.startTime) > timeoutManager.timeoutDuration;
 }
 
 /**
  * Сброс таймаута после завершения операции
  */
 void clearTimeout() {
     timeoutManager.active = false;
 }
 
 /**
  * КРИТИЧЕСКАЯ ФУНКЦИЯ: Аварийная остановка системы
  * Немедленно останавливает все операции и блокирует систему
  */
 void emergencyStop() {
     noInterrupts(); // Критическая секция - отключаем прерывания
     
     // Устанавливаем флаги аварийного состояния
     state.emergencyStop = true;
     state.commandInProgress = false;
     state.homingActive = false;
     
     // Останавливаем планировщик движения
     planner.brake();
     
     // Немедленно отключаем все моторы
     for (uint8_t i = 0; i < NUM_MOTORS; i++) {
         digitalWrite(motors[i].enablePin, HIGH); // Выключение моторов
     }
     
     state.lastError = ERROR_EMERGENCY_STOP;
     interrupts(); // Восстанавливаем прерывания
     
     // Информируем оператора
     Serial.println("!!! EMERGENCY STOP ACTIVATED !!!");
     Serial.println("Send 'reset' command to resume operations");
 }
 
 /**
  * Периодическая проверка аварийных условий
  * Вызывается из основного цикла каждые 100мс
  */
 void checkEmergency() {
     // Проверка 1: Watchdog - отсутствие активности более 10 минут
     if (millis() - state.lastActivityTime > WATCHDOG_TIMEOUT_MS) {
         Serial.println("WATCHDOG: Auto-shutdown due to inactivity");
         emergencyStop();
         return;
     }
     
     // Проверка 2: Истечение таймаута текущей операции
     if (isTimeoutExpired()) {
         Serial.println("TIMEOUT: Operation exceeded time limit");
         emergencyStop();
     }
     
     // Здесь можно добавить дополнительные проверки:
     // - Температура драйверов
     // - Напряжение питания
     // - Состояние концевиков
     // - Ошибки связи
 }
 
 // ============================================
 // INPUT PINS & WEIGHT SENSOR FUNCTIONS
 // ============================================
 
 /**
  * Чтение состояния всех входных пинов
  * Возвращает битовую маску состояния пинов
  * 
  * @return битовая маска (8 бит) состояния входных пинов
  */
 void readInputPins() {
     uint8_t pinMask = 0;
     
     for (uint8_t i = 0; i < NUM_INPUT_PINS; i++) {
         bool pinState = digitalRead(inputPins[i].pin);
         
         // Инвертируем логику если пин активный низкий
         if (inputPins[i].isActiveLow) {
             pinState = !pinState;
         }
         
         // Устанавливаем соответствующий бит в маске
         if (pinState) {
             pinMask |= (1 << i);
         }
     }
     
     // Выводим битовую маску в формате 00000000
     Serial.print("INPUT_PINS: ");
     for (int8_t i = 7; i >= 0; i--) {
         Serial.print((pinMask >> i) & 1);
     }
     Serial.println();
 }
 
 /**
  * Проверка переполненности резервуара
  * Читает состояние пина WASTE (индекс 3 в controlPins)
  * 
  * @return true если резервуар переполнен
  */
 bool checkReservoirOverflow() {
     bool wasteState = digitalRead(controlPins[WASTE].pin);
     
     // WASTE пин активный высокий - если HIGH, то резервуар переполнен
     if (wasteState) {
         state.lastError = ERROR_RESERVOIR_OVERFLOW;
         Serial.println("WARNING: Reservoir overflow detected!");
         return true;
     }
     
     return false;
 }
 
 /**
  * Запуск измерения веса
  * Активирует датчик веса для измерения
  */
 void startWeightMeasurement() {
     if (!weightManager.isCalibrated) {
         Serial.println("ERROR: Weight sensor not calibrated");
         return;
     }
     
     weightManager.isMeasuring = true;
     weightManager.lastMeasurement = millis();
     Serial.println("Weight measurement started");
 }
 
 /**
  * Остановка измерения веса
  * Деактивирует датчик веса
  */
 void stopWeightMeasurement() {
     weightManager.isMeasuring = false;
     Serial.println("Weight measurement stopped");
 }
 
 /**
  * Получение текущего веса
  * 
  * @return вес в граммах
  */
 float getWeight() {
     if (!weightManager.isMeasuring) {
         return 0.0;
     }
     
     if (millis() - weightManager.lastMeasurement > WEIGHT_MEASUREMENT_TIMEOUT) {
         Serial.println("ERROR: Weight measurement timeout");
         stopWeightMeasurement();
         return 0.0;
     }
     
     if (weightManager.sensor->is_ready()) {
         float weight = weightManager.sensor->get_units(5); // 5 измерений для стабильности
         weightManager.lastMeasurement = millis();
         return weight;
     } else {
         Serial.println("ERROR: Weight sensor not ready");
         return 0.0;
     }
 }
 
 /**
  * Калибровка датчика веса
  * Требует известный вес для калибровки
  */
 void calibrateWeightSensor() {
     Serial.println("Starting weight sensor calibration...");
     Serial.println("Place known weight on sensor and send 'calibrate_weight [weight_in_grams]'");
     
     weightManager.isMeasuring = true;
     weightManager.lastMeasurement = millis();
 }
 
 /**
  * Обнуление датчика веса (tare)
  * Устанавливает текущее показание как ноль
  */
 void zeroWeightSensor() {
     if (weightManager.sensor->is_ready()) {
         weightManager.sensor->tare(10); // 10 измерений для стабильного нуля
         weightManager.offset = 0.0;
         Serial.println("Weight sensor zeroed");
     } else {
         Serial.println("ERROR: Weight sensor not ready for zeroing");
     }
 }
 
 // ============================================
 // ENHANCED UTILITY FUNCTIONS
 // ============================================
 
 /**
  * Преобразование единиц измерения в шаги мотора
  * 
  * @param motor - индекс мотора
  * @param units - значение в единицах (мм, градусы и т.д.)
  * @return количество шагов
  */
 inline int32_t toSteps(uint8_t motor, float units) {
     return units * motors[motor].stepsPerUnit;
 }
 
 /**
  * Преобразование шагов в единицы измерения
  * 
  * @param motor - индекс мотора
  * @param steps - количество шагов
  * @return значение в единицах
  * 
  * ВНИМАНИЕ: Потенциальное деление на ноль если stepsPerUnit = 0!
  */
 inline float toUnits(uint8_t motor, int32_t steps) {
     // TODO: Добавить проверку на ноль
     return (float)steps / motors[motor].stepsPerUnit;
 }
 
 /**
  * Чтение состояния концевого выключателя
  * Учитывает тип концевика (NPN/PNP)
  * 
  * @param motor - индекс мотора
  * @return true если концевик сработал
  */
 bool readEndstop(uint8_t motor) {
     bool pinState = digitalRead(motors[motor].homePin);
     // Инвертируем логику для NPN концевиков
     return motors[motor].isNPN ? !pinState : pinState;
 }
 
 /**
  * Thread-safe управление питанием мотора
  * 
  * @param motor - индекс мотора
  * @param enable - true для включения, false для выключения
  */
 void setMotorPower(uint8_t motor, bool enable) {
     if (motor >= NUM_MOTORS) return;  // Защита от выхода за границы
     
     // В GyverStepper управление питанием через пин enable
     if (enable) {
         digitalWrite(motors[motor].enablePin, LOW);  // Включение (активный низкий уровень)
     } else {
         digitalWrite(motors[motor].enablePin, HIGH); // Выключение
     }
 }
 
 /**
  * Включение всех моторов с проверкой аварийного состояния
  */
 void enableAllMotors() {
     // Блокируем включение при аварийной остановке
     if (state.emergencyStop) {
         Serial.println("ERROR: Cannot enable motors - emergency stop active");
         return;
     }
     
     noInterrupts();  // Критическая секция
     for (uint8_t i = 0; i < NUM_MOTORS; i++) {
         digitalWrite(motors[i].enablePin, LOW);  // Включение моторов
     }
     state.motorsEnabled = true;
     interrupts();
     
     Serial.println("All motors enabled");
 }
 
 /**
  * Отключение временных моторов (не помеченных как alwaysOn)
  * Используется для экономии энергии и уменьшения нагрева
  */
 void disableTemporaryMotors() {
     noInterrupts();  // Критическая секция
     for (uint8_t i = 0; i < NUM_MOTORS; i++) {
         if (!motors[i].alwaysOn) {
             digitalWrite(motors[i].enablePin, HIGH); // Выключение моторов
         }
     }
     state.motorsEnabled = false;
     interrupts();
 }
 
 /**
  * Управление контрольными пинами
  * 
  * @param pinIndex - индекс пина (0-9)
  * @param state - состояние (true = включить, false = выключить)
  */
 void controlPin(uint8_t pinIndex, bool state) {
     if (!validatePinIndex(pinIndex)) {
         Serial.println("ERROR: Invalid pin index");
         return;
     }
     
     digitalWrite(controlPins[pinIndex].pin, state ? HIGH : LOW);
     
     Serial.print("Pin ");
     Serial.print(controlPins[pinIndex].name);
     Serial.print(" (");
     Serial.print(controlPins[pinIndex].pin);
     Serial.print(") ");
     Serial.println(state ? "ENABLED" : "DISABLED");
 }
 
 // ============================================
 // ENHANCED MOTION CONTROL
 // ============================================
 
 /**
  * ОСНОВНАЯ ФУНКЦИЯ ДВИЖЕНИЯ
  * Выполняет координированное движение нескольких осей
  * с полной валидацией и контролем безопасности
  * 
  * @param positions - массив целевых позиций в единицах
  * @param active - массив флагов активности осей
  */
 void coordinatedMove(float positions[], bool active[]) {
     // Проверка 1: Аварийное состояние
     if (state.emergencyStop) {
         Serial.println("ERROR: Emergency stop active");
         return;
     }
     
     // Проверка 2: Блокировка во время homing
     if (state.homingActive) {
         Serial.println("ERROR: Cannot move during homing");
         return;
     }
     
     // Проверка 3: Валидация всех позиций
     if (!validateMove(positions, active)) {
         state.lastError = ERROR_INVALID_POSITION;
         return;
     }
     
     Serial.println("=== SECURE COORDINATED MOVE ===");
     
     // Устанавливаем флаги состояния (thread-safe)
     noInterrupts();
     state.commandInProgress = true;
     state.lastActivityTime = millis();
     interrupts();
     
     // Включаем все моторы перед движением
     enableAllMotors();
     
     // Подготовка целевых позиций
     int32_t targets[NUM_MOTORS];
     bool hasMovement = false;
     
     // Расчёт целевых позиций в шагах
     for (uint8_t i = 0; i < NUM_MOTORS; i++) {
         if (active[i]) {
             targets[i] = toSteps(i, positions[i]);
             
             // Проверяем, есть ли реальное движение
             if (targets[i] != steppers[i].pos) hasMovement = true;
             
             // Выводим информацию о движении
             Serial.print(motors[i].name);
             Serial.print(" -> ");
             Serial.print(positions[i]);
             Serial.print(" units (");
             Serial.print(targets[i]);
             Serial.println(" steps)");
         } else {
             // Неактивные оси остаются на месте
             targets[i] = steppers[i].pos;
         }
     }
     
     // Если нет реального движения, завершаем
     if (!hasMovement) {
         Serial.println("Already at target");
         Serial.println("COMPLETE");
         state.commandInProgress = false;
         return;
     }
     
     // Передаём целевые позиции планировщику
     planner.setTarget(targets);
     
     // Запускаем таймаут для контроля времени выполнения
     startTimeout(MOVE_TIMEOUT_MS);
     
     // Основной цикл движения
     while (!planner.ready()) {
         // Выполняем один шаг планировщика
         planner.tick();
         
         // Проверка аварийных условий
         if (state.emergencyStop || isTimeoutExpired()) {
             planner.brake();  // Экстренная остановка
             clearTimeout();
             state.commandInProgress = false;
             return;
         }
         
         // Периодическая проверка безопасности (каждые 100мс)
         if (millis() % EMERGENCY_CHECK_INTERVAL == 0) {
             checkEmergency();
         }
     }
     
     // Движение завершено успешно
     clearTimeout();
     
     // Выводим финальные позиции
     for (uint8_t i = 0; i < NUM_MOTORS; i++) {
         if (active[i]) {
             Serial.print(motors[i].name);
             Serial.print(" at ");
             Serial.print(toUnits(i, steppers[i].pos), 2);
             Serial.println(" units");
         }
     }
     
     // Отключаем временные моторы для экономии энергии
     disableTemporaryMotors();
     state.commandInProgress = false;
     Serial.println("COMPLETE");
 }
 
 // ============================================
 // ENHANCED HOMING FUNCTIONS
 // ============================================
 
 /**
  * Вспомогательная функция для выполнения backoff движения
  * Используется в процессе homing для отхода от концевиков
  * 
  * @param phase - название фазы для отладки
  * @param positions - массив целевых позиций
  */
 void performBackoff(const char* phase, int32_t positions[]) {
     Serial.print(phase);
     Serial.println(" backoff...");
     
     planner.setTarget(positions);
     uint32_t backoffStart = millis();
     
     // Цикл выполнения backoff с таймаутом 5 секунд
     while (!planner.ready()) {
         planner.tick();
         
         // Проверка таймаута и аварийной остановки
         if (state.emergencyStop || (millis() - backoffStart) > 5000) {
             planner.brake();
             return;
         }
     }
     
     planner.brake();
 }
 
 /**
  * ФУНКЦИЯ HOMING (ВОЗВРАТ В ИСХОДНОЕ ПОЛОЖЕНИЕ)
  * Выполняет поиск концевых выключателей и установку нулевой позиции
  * 
  * Алгоритм:
  * 1. Pre-backoff - предварительный отход от концевиков
  * 2. Move-away - отъезд если уже на концевике
  * 3. Seek - поиск концевиков
  * 4. Final backoff - финальный отход и обнуление
  * 
  * @param flags - массив флагов (1 = выполнить homing, 0 = пропустить)
  */
 void homeMotors(bool flags[]) {
     // Проверка аварийного состояния
     if (state.emergencyStop) {
         Serial.println("ERROR: Emergency stop active");
         return;
     }
     
     // Проверка наличия хотя бы одного активного флага
     bool hasValidFlags = false;
     for (uint8_t i = 0; i < NUM_MOTORS; i++) {
         if (flags[i]) hasValidFlags = true;
     }
     
     if (!hasValidFlags) {
         Serial.println("ERROR: No valid homing flags");
         return;
     }
     
     // Установка флагов состояния
     noInterrupts();
     state.homingActive = true;
     state.commandInProgress = true;
     state.lastActivityTime = millis();
     interrupts();
     
     Serial.println("=== SECURE HOMING START ===");
     enableAllMotors();
     
     // Запуск таймаута для всей операции homing
     startTimeout(HOMING_TIMEOUT_MS);
     
     int32_t positions[NUM_MOTORS];
     bool needMove;
     
     // Получаем текущие позиции всех моторов
     for (uint8_t i = 0; i < NUM_MOTORS; i++) {
         positions[i] = steppers[i].pos;
     }
     
     // ФАЗА 1: Предварительный отход (pre-backoff)
     // Необходим для некоторых механических конфигураций
     needMove = false;
     for (uint8_t i = 0; i < 4; i++) { // E1 обрабатывается отдельно в clampHome
         if (flags[i] && motors[i].preBackoff > 0) {
             positions[i] += motors[i].preBackoff;
             needMove = true;
         }
     }
     if (needMove && !state.emergencyStop) performBackoff("Pre-homing", positions);
     
     // ФАЗА 2: Отъезд если уже на концевике
     // Предотвращает ложное срабатывание
     if (!state.emergencyStop) {
         needMove = false;
         for (uint8_t i = 0; i < NUM_MOTORS; i++) {
             positions[i] = steppers[i].pos;
         }
         
         for (uint8_t i = 0; i < 4; i++) {
             if (flags[i] && readEndstop(i)) {
                 positions[i] += 500;  // Фиксированный отход 500 шагов
                 needMove = true;
                 Serial.print(motors[i].name);
                 Serial.println(" - endstop triggered, moving away");
             }
         }
         if (needMove) performBackoff("Move-away", positions);
     }
     
     // ФАЗА 3: Поиск концевиков
     // Движение к концевикам с контролем срабатывания
     if (!state.emergencyStop) {
         for (uint8_t i = 0; i < NUM_MOTORS; i++) {
             positions[i] = steppers[i].pos;
         }
         
         // Устанавливаем целевые позиции для поиска
         for (uint8_t i = 0; i < 4; i++) {
             if (flags[i]) {
                 positions[i] -= motors[i].maxSteps;  // Движение в отрицательном направлении
             }
         }
         
         planner.setTarget(positions);
         bool homed[NUM_MOTORS] = {false};  // Флаги успешного homing
         
         // Цикл поиска концевиков
         while (!planner.ready()) {
             planner.tick();
             
             // Проверка таймаута и аварийной остановки
             if (state.emergencyStop || isTimeoutExpired()) {
                 planner.brake();
                 break;
             }
             
             // Проверка срабатывания концевиков
             for (uint8_t i = 0; i < 4; i++) {
                 if (flags[i] && !homed[i] && readEndstop(i)) {
                     homed[i] = true;
                     Serial.print(motors[i].name);
                     Serial.println(" - endstop reached");
                 }
             }
             
             // Проверка завершения для всех запрошенных осей
             bool allDone = true;
             for (uint8_t i = 0; i < 4; i++) {
                 if (flags[i] && !homed[i]) allDone = false;
             }
             if (allDone) break;
         }
         
         planner.brake();
         
         // ФАЗА 4: Финальный отход и обнуление
         if (!state.emergencyStop) {
             needMove = false;
             for (uint8_t i = 0; i < NUM_MOTORS; i++) {
                 positions[i] = steppers[i].pos;
             }
             
             // Отход на заданное расстояние от концевика
             for (uint8_t i = 0; i < 4; i++) {
                 if (flags[i] && homed[i] && motors[i].homeBackoff > 0) {
                     positions[i] += motors[i].homeBackoff;
                     needMove = true;
                 }
             }
             if (needMove) performBackoff("Final", positions);
             
             // Обнуление позиций успешно захоуменных осей
             for (uint8_t i = 0; i < 4; i++) {
                 if (flags[i] && homed[i]) {
                     steppers[i].pos = 0;
                     Serial.print(motors[i].name);
                     Serial.println(" zeroed");
                 }
             }
         }
     }
     
     // Очистка состояния
     clearTimeout();
     planner.reset();
     
     noInterrupts();
     state.homingActive = false;
     state.commandInProgress = false;
     interrupts();
     
     Serial.println("COMPLETE");
 }
 
 // ============================================
 // SETUP & LOOP FUNCTIONS
 // ============================================
 
 /**
  * Инициализация системы
  * Настройка пинов, планировщика и начального состояния
  */
 void setup() {
     Serial.begin(115200);
     Serial.println("=== 5-MOTOR CONTROL SYSTEM v3.0 ===");
     Serial.println("Initializing...");
     
     // Инициализация пинов концевиков
     for (uint8_t i = 0; i < NUM_MOTORS; i++) {
         pinMode(motors[i].homePin, INPUT_PULLUP);
     }
     
     // Инициализация пинов enable моторов
     for (uint8_t i = 0; i < NUM_MOTORS; i++) {
         pinMode(motors[i].enablePin, OUTPUT);
         digitalWrite(motors[i].enablePin, HIGH); // Начальное состояние - выключено
     }
     
     // Инициализация контрольных пинов
     for (uint8_t i = 0; i < NUM_CTRL_PINS; i++) {
         pinMode(controlPins[i].pin, OUTPUT);
         digitalWrite(controlPins[i].pin, LOW);  // Начальное состояние - выключено
     }
     
     // Инициализация входных пинов
     for (uint8_t i = 0; i < NUM_INPUT_PINS; i++) {
         pinMode(inputPins[i].pin, INPUT_PULLUP);
     }
     
     // Инициализация датчика веса
     Serial.println("Initializing weight sensor...");
     weightManager.sensor->begin(controlPins[HX711_DT].pin, controlPins[HX711_SCK].pin);
     
     // Ждем стабилизации датчика
     delay(1000);
     
     if (weightManager.sensor->is_ready()) {
         Serial.println("Weight sensor ready");
         // Устанавливаем начальный калибровочный коэффициент
         weightManager.sensor->set_scale(weightManager.calibrationFactor);
         weightManager.sensor->tare(10);
         weightManager.isCalibrated = true;
     } else {
         Serial.println("ERROR: Weight sensor not ready");
         weightManager.isCalibrated = false;
     }
     
     // Добавление моторов в планировщик
     for (uint8_t i = 0; i < NUM_MOTORS; i++) {
         planner.addStepper(i, steppers[i]);
     }
     
     // Настройка планировщика
     planner.setMaxSpeed(500);      // Максимальная скорость в шагах/сек
     planner.setAcceleration(500);  // Ускорение в шагах/сек²
     
     // Включение моторов
     enableAllMotors();
     
     // Сброс позиций в 0
     planner.reset();
     
     Serial.println("System ready!");
     Serial.println("=== AVAILABLE COMMANDS ===");
     Serial.println("MOTION COMMANDS:");
     Serial.println("  home [x] [y] [z] [e0] [e1] - homing for specified axes");
     Serial.println("    Examples: home 1 1 1 0 0  (X,Y,Z only)");
     Serial.println("              home 1 0 0 0 0  (X only)");
     Serial.println("              home             (all axes)");
     Serial.println("");
     Serial.println("  move [x] [y] [z] [e0] [e1] - move to absolute positions");
     Serial.println("    Examples: move 100 50 0 0 0  (X=100, Y=50, Z=0)");
     Serial.println("              move 0 0 -10 0 0   (Z=-10 only)");
     Serial.println("              move 50            (X=50 only)");
     Serial.println("");
     Serial.println("SYSTEM COMMANDS:");
     Serial.println("  status - show system status and motor positions");
     Serial.println("  reset - emergency stop reset");
     Serial.println("  help - show this help message");
     Serial.println("  version - show system version");
     Serial.println("");
     Serial.println("CONTROL PIN COMMANDS:");
     Serial.println("  pin [index] [state] - control output pins");
     Serial.println("    Examples: pin 0 1  (enable PUMP)");
     Serial.println("              pin 1 0  (disable KL1)");
     Serial.println("              pin 4 1  (enable ROTOR1)");
     Serial.println("");
     Serial.println("SAFETY COMMANDS:");
     Serial.println("  emergency - trigger emergency stop");
     Serial.println("  enable - enable all motors");
     Serial.println("  disable - disable all motors");
     Serial.println("");
     Serial.println("MONITORING COMMANDS:");
     Serial.println("  read_pins - read input pins status (binary mask)");
     Serial.println("  check_overflow - check reservoir overflow status");
     Serial.println("");
     Serial.println("WEIGHT SENSOR COMMANDS:");
     Serial.println("  start_weight - start weight measurement");
     Serial.println("  stop_weight - stop weight measurement");
     Serial.println("  get_weight - get current weight");
     Serial.println("  zero_weight - zero weight sensor (tare)");
     Serial.println("  calibrate_weight [grams] - calibrate with known weight");
     Serial.println("");
     Serial.println("Type 'help' for detailed command reference");
 }
 
 /**
  * Основной цикл системы
  * Обработка команд, проверка безопасности, обновление планировщика
  */
 void loop() {
     // Обработка входящих команд
     if (Serial.available()) {
         char c = Serial.read();
         
         // Добавление символа в буфер
         if (state.inputBufferPos < MAX_COMMAND_LENGTH - 1) {
             state.inputBuffer[state.inputBufferPos++] = c;
             state.lastActivityTime = millis();
         }
         
         // Команда завершена (Enter или перевод строки)
         if (c == '\n' || c == '\r') {
             state.inputBuffer[state.inputBufferPos] = '\0';  // Завершающий нуль
             state.commandReady = true;
             state.inputBufferPos = 0;
         }
     }
     
     // Обработка готовой команды
     if (state.commandReady && !state.commandInProgress) {
         processCommand(state.inputBuffer);
         clearCommandBuffer();
     }
     
     // Обновление планировщика движения
     if (!state.emergencyStop) {
         planner.tick();
     }
     
     // Периодическая проверка безопасности
     static uint32_t lastCheck = 0;
     if (millis() - lastCheck >= EMERGENCY_CHECK_INTERVAL) {
         checkEmergency();
         lastCheck = millis();
     }
     
     // Небольшая задержка для стабильности
     delay(1);
 }
 
 // ============================================
 // COMMAND PROCESSING
 // ============================================
 
 /**
  * Обработка входящих команд
  * 
  * @param command - строка команды для обработки
  */
 void processCommand(const char* command) {
     // Убираем пробелы в начале и конце
     while (*command == ' ') command++;
     
     // Создаем копию команды для очистки от \r и \n
     char cleanCommand[MAX_COMMAND_LENGTH];
     strncpy(cleanCommand, command, MAX_COMMAND_LENGTH - 1);
     cleanCommand[MAX_COMMAND_LENGTH - 1] = '\0';
     
     // Удаляем символы \r и \n из конца строки
     char* end = cleanCommand + strlen(cleanCommand) - 1;
     while (end >= cleanCommand && (*end == '\r' || *end == '\n' || *end == ' ')) {
         *end = '\0';
         end--;
     }
     
     if (strcmp(cleanCommand, "reset") == 0) {
         // Сброс аварийной остановки
         if (state.emergencyStop) {
             state.emergencyStop = false;
             state.lastError = ERROR_NONE;
             Serial.println("Emergency stop reset");
         }
     }
     else if (strncmp(cleanCommand, "home", 4) == 0) {
         // Команда homing
         bool flags[NUM_MOTORS] = {false};
         parseHomingFlags(cleanCommand + 4, flags);
         homeMotors(flags);
     }
     else if (strncmp(cleanCommand, "move", 4) == 0) {
         // Команда движения
         float positions[NUM_MOTORS];
         bool active[NUM_MOTORS] = {false};
         parseMoveCommand(cleanCommand + 4, positions, active);
         coordinatedMove(positions, active);
     }
     else if (strcmp(cleanCommand, "status") == 0) {
         // Статус системы
         printSystemStatus();
     }
     else if (strcmp(cleanCommand, "help") == 0) {
         // Показать справку
         printHelp();
     }
     else if (strcmp(cleanCommand, "version") == 0) {
         // Показать версию
         printVersion();
     }
     else if (strncmp(cleanCommand, "pin", 3) == 0) {
         // Команда управления пинами
         uint8_t pinIndex;
         int tempState;
         if (sscanf(cleanCommand + 3, "%hhu %d", &pinIndex, &tempState) == 2) {
             if (validatePinIndex(pinIndex)) {
                 controlPin(pinIndex, tempState != 0);
             } else {
                 Serial.println("ERROR: Invalid pin index");
             }
         } else {
             Serial.println("ERROR: Invalid pin command format");
         }
     }
     else if (strcmp(cleanCommand, "emergency") == 0) {
         // Аварийная остановка
         emergencyStop();
     }
     else if (strcmp(cleanCommand, "enable") == 0) {
         // Включение всех моторов
         enableAllMotors();
     }
     else if (strcmp(cleanCommand, "disable") == 0) {
         // Отключение временных моторов
         disableTemporaryMotors();
     }
     else if (strcmp(cleanCommand, "read_pins") == 0) {
         // Чтение состояния входных пинов
         readInputPins();
     }
     else if (strcmp(cleanCommand, "check_overflow") == 0) {
         // Проверка переполненности резервуара
         if (checkReservoirOverflow()) {
             Serial.println("RESERVOIR OVERFLOW DETECTED!");
         } else {
             Serial.println("Reservoir level normal");
         }
     }
     else if (strcmp(cleanCommand, "start_weight") == 0) {
         // Запуск измерения веса
         startWeightMeasurement();
     }
     else if (strcmp(cleanCommand, "stop_weight") == 0) {
         // Остановка измерения веса
         stopWeightMeasurement();
     }
     else if (strcmp(cleanCommand, "get_weight") == 0) {
         // Получение текущего веса
         if (weightManager.isMeasuring) {
             float weight = getWeight();
             Serial.print("Current weight: ");
             Serial.print(weight, 2);
             Serial.println(" grams");
         } else {
             Serial.println("ERROR: Weight measurement not active");
         }
     }
     else if (strcmp(cleanCommand, "zero_weight") == 0) {
         // Обнуление датчика веса
         zeroWeightSensor();
     }
     else if (strncmp(cleanCommand, "calibrate_weight", 15) == 0) {
         // Калибровка датчика веса
         float knownWeight;
         if (sscanf(cleanCommand + 15, "%f", &knownWeight) == 1) {
             if (knownWeight > 0) {
                 Serial.print("Calibrating with known weight: ");
                 Serial.print(knownWeight);
                 Serial.println(" grams");
                 
                 if (weightManager.sensor->is_ready()) {
                     // Получаем среднее значение с датчика
                     float rawValue = weightManager.sensor->get_units(10);
                     
                     if (rawValue != 0) {
                         weightManager.calibrationFactor = rawValue / knownWeight;
                         weightManager.sensor->set_scale(weightManager.calibrationFactor);
                         weightManager.isCalibrated = true;
                         
                         Serial.print("Calibration factor: ");
                         Serial.println(weightManager.calibrationFactor, 6);
                         Serial.println("Calibration completed successfully");
                     } else {
                         Serial.println("ERROR: Invalid sensor reading");
                     }
                 } else {
                     Serial.println("ERROR: Weight sensor not ready");
                 }
             } else {
                 Serial.println("ERROR: Known weight must be positive");
             }
         } else {
             Serial.println("ERROR: Invalid calibration command format");
             Serial.println("Use: calibrate_weight [weight_in_grams]");
         }
     }
     else {
         Serial.print("Unknown command: ");
         Serial.println(cleanCommand);
     }
 }
 
 /**
  * Парсинг флагов homing из команды
  * 
  * @param args - аргументы команды
  * @param flags - массив флагов для заполнения
  */
 void parseHomingFlags(const char* args, bool flags[]) {
     // По умолчанию все оси
     for (uint8_t i = 0; i < NUM_MOTORS; i++) {
         flags[i] = true;
     }
     
     // Если есть аргументы, парсим их
     if (strlen(args) > 0) {
         for (uint8_t i = 0; i < NUM_MOTORS; i++) {
             flags[i] = false;
         }
         
         char* token = strtok((char*)args, " ");
         uint8_t axis = 0;
         
         while (token && axis < NUM_MOTORS) {
             if (strcmp(token, "1") == 0 || strcmp(token, "true") == 0) {
                 flags[axis] = true;
             }
             token = strtok(NULL, " ");
             axis++;
         }
     }
 }
 
 /**
  * Парсинг команды движения
  * 
  * @param args - аргументы команды
  * @param positions - массив позиций для заполнения
  * @param active - массив флагов активности для заполнения
  */
 void parseMoveCommand(const char* args, float positions[], bool active[]) {
     char* token = strtok((char*)args, " ");
     uint8_t axis = 0;
     
     while (token && axis < NUM_MOTORS) {
         positions[axis] = atof(token);
         active[axis] = true;
         token = strtok(NULL, " ");
         axis++;
     }
     
     // Остальные оси неактивны
     for (uint8_t i = axis; i < NUM_MOTORS; i++) {
         active[i] = false;
     }
 }
 
 /**
  * Вывод статуса системы
  */
 void printSystemStatus() {
     Serial.println("=== SYSTEM STATUS ===");
     Serial.print("Emergency Stop: ");
     Serial.println(state.emergencyStop ? "ACTIVE" : "Inactive");
     Serial.print("Motors Enabled: ");
     Serial.println(state.motorsEnabled ? "Yes" : "No");
     Serial.print("Homing Active: ");
     Serial.println(state.homingActive ? "Yes" : "No");
     Serial.print("Command In Progress: ");
     Serial.println(state.commandInProgress ? "Yes" : "No");
     
     Serial.println("Motor Positions:");
     for (uint8_t i = 0; i < NUM_MOTORS; i++) {
         Serial.print("  ");
         Serial.print(motors[i].name);
         Serial.print(": ");
         Serial.print(toUnits(i, steppers[i].pos), 2);
         Serial.println(" units");
     }
     
     if (state.lastError != ERROR_NONE) {
         Serial.print("Last Error: ");
         Serial.println(state.lastError);
     }
 }

 /**
  * Вывод справки по командам
  */
 void printHelp() {
     Serial.println("=== COMMAND HELP ===");
     Serial.println("MOTION COMMANDS:");
     Serial.println("  home [x] [y] [z] [e0] [e1] - homing for specified axes");
     Serial.println("    Examples: home 1 1 1 0 0  (X,Y,Z only)");
     Serial.println("              home 1 0 0 0 0  (X only)");
     Serial.println("              home             (all axes)");
     Serial.println("    Flags: 1 or true - perform homing, 0 or false - skip");
     Serial.println("");
     Serial.println("  move [x] [y] [z] [e0] [e1] - move to absolute positions");
     Serial.println("    Examples: move 100 50 0 0 0  (X=100, Y=50, Z=0)");
     Serial.println("              move 0 0 -10 0 0   (Z=-10 only)");
     Serial.println("              move 50            (X=50 only)");
     Serial.println("    Units: mm, degrees, etc.");
     Serial.println("");
     Serial.println("SYSTEM COMMANDS:");
     Serial.println("  status - show system status and motor positions");
     Serial.println("  reset - emergency stop reset");
     Serial.println("  help - show this help message");
     Serial.println("  version - show system version");
     Serial.println("");
     Serial.println("CONTROL PIN COMMANDS:");
     Serial.println("  pin [index] [state] - control output pins");
     Serial.println("    Examples: pin 0 1  (enable PUMP)");
     Serial.println("              pin 1 0  (disable KL1)");
     Serial.println("              pin 4 1  (enable ROTOR1)");
     Serial.println("    State: 1 - enable, 0 - disable");
     Serial.println("");
     Serial.println("SAFETY COMMANDS:");
     Serial.println("  emergency - trigger emergency stop");
     Serial.println("  enable - enable all motors");
     Serial.println("  disable - disable all motors");
     Serial.println("");
     Serial.println("MONITORING COMMANDS:");
     Serial.println("  read_pins - read input pins status (binary mask)");
     Serial.println("  check_overflow - check reservoir overflow status");
     Serial.println("");
     Serial.println("WEIGHT SENSOR COMMANDS:");
     Serial.println("  start_weight - start weight measurement");
     Serial.println("  stop_weight - stop weight measurement");
     Serial.println("  get_weight - get current weight");
     Serial.println("  zero_weight - zero weight sensor (tare)");
     Serial.println("  calibrate_weight [grams] - calibrate with known weight");
     Serial.println("");
     Serial.println("Type 'help' for detailed command reference");
 }

 /**
  * Вывод версии системы
  */
 void printVersion() {
     Serial.println("=== SYSTEM VERSION ===");
     Serial.println("5-MOTOR CONTROL SYSTEM v3.0");
     Serial.println("Security & Safety Enhanced");
     Serial.println("Platform: PlatformIO / Arduino");
     Serial.println("Last updated: 2023-10-27");
     Serial.println("Author: Your Name");
     Serial.println("License: MIT");
     Serial.println("=== END OF VERSION ===");
 }