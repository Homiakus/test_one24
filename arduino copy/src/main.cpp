/**
 * @file: main.cpp
 * @description: Система управления 5 шаговыми двигателями с использованием AccelStepper и MultiStepper
 * @dependencies: AccelStepper, MultiStepper, SerialCommand
 * @created: 2024-12-19
 * @updated: 2024-12-19 - добавлен MultiStepper для координированного движения
 */

#include <Arduino.h>
#include <AccelStepper.h>
#include <MultiStepper.h>
#include <SerialCommand.h>

// ============================================
// КОНФИГУРАЦИЯ СИСТЕМЫ
// ============================================

#define NUM_MOTORS 5

// Пины шагов (из config.h)
const int stepPins[NUM_MOTORS] = {A0, A6, 46, 26, 36};    // Multi, Multizone, RRight, E0, E1

// Пины направления (из config.h)
const int dirPins[NUM_MOTORS] = {A1, A7, 48, 28, 34};     // Multi, Multizone, RRight, E0, E1

// Пины включения (из config.h)
const int enablePins[NUM_MOTORS] = {38, A2, A8, 24, 30};  // Multi, Multizone, RRight, E0, E1

// Пины концевых выключателей (из config.h)
const int homePins[NUM_MOTORS] = {14, 2, 2, 15, 15};      // Multi, Multizone, RRight, ClampSensor, ClampSensor

// Дополнительные управляющие пины (насос, клапаны, датчики)
const int controlPins[] = {18, 8, 10, 19, 27, 29, 23, 25, 42, 40}; // PUMP, KL1, KL2, WASTE, ROTOR_PINS[4], HX711_SCK, HX711_DT
const int NUM_CONTROL_PINS = sizeof(controlPins) / sizeof(controlPins[0]);

// Названия двигателей для диагностики
const char* motorNames[NUM_MOTORS] = {"Multi(X)", "Multizone(Y)", "RRight(Z)", "E0", "E1"};

// Настройки двигателей (из config.h)
const float maxSpeed[NUM_MOTORS] = {6000.0, 600.0, 30000.0, 30000.0, 30000.0};          // шагов/сек
const float acceleration[NUM_MOTORS] = {5000.0, 800.0, 2000.0, 3000.0, 2000.0};       // шагов/сек²
const long stepsPerRevolution[NUM_MOTORS] = {200, 200, 200, 200, 200};     // шагов на оборот
const float homingSpeed[NUM_MOTORS] = {6000.0, 400.0, 2000.0, 1000.0, 1000.0};        // шагов/сек для хоминга
const bool endstopTypeNPN[NUM_MOTORS] = {false, true, true, true, true};   // тип датчика (true=NPN, false=PNP)

// Настройки для преобразования единиц (шагов на мм - можно настроить под ваши механизмы)
const long stepsPerUnit[NUM_MOTORS] = {80, 80, 80, 200, 200};                // шагов/мм
const long maxSteps[NUM_MOTORS] = {16000, 16000, 16000, 16000, 16000};      // максимальные шаги для поиска нуля
const long homeBackoff[NUM_MOTORS] = {200, 200, 200, 200, 200};            // шаги отката после касания концевика

// ============================================
// ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ
// ============================================

AccelStepper* steppers[NUM_MOTORS];
MultiStepper multiStepper;  // Планировщик координированного движения
SerialCommand sCmd;

bool motorsEnabled = true;
bool homingActive = false;

// ============================================
// СЛУЖЕБНЫЕ ФУНКЦИИ
// ============================================

/**
 * Преобразование пользовательских единиц в шаги
 */
long unitsToSteps(int motorIndex, float units) {
    return (long)(units * stepsPerUnit[motorIndex]);
}

/**
 * Преобразование шагов в пользовательские единицы
 */
float stepsToUnits(int motorIndex, long steps) {
    return (float)steps / stepsPerUnit[motorIndex];
}

/**
 * Включение всех двигателей
 */
void enableMotors() {
    for (int i = 0; i < NUM_MOTORS; i++) {
        digitalWrite(enablePins[i], LOW); // LOW включает драйвер
    }
    motorsEnabled = true;
    Serial.println("Motors enabled");
}

/**
 * Отключение всех двигателей
 */
void disableMotors() {
    for (int i = 0; i < NUM_MOTORS; i++) {
        digitalWrite(enablePins[i], HIGH); // HIGH отключает драйвер
    }
    motorsEnabled = false;
    Serial.println("Motors disabled");
}

/**
 * Проверка завершения движения всех двигателей (через MultiStepper)
 */
bool allMotorsIdle() {
    return !multiStepper.run();
}

/**
 * Чтение состояния концевого выключателя с учетом типа (NPN/PNP)
 */
bool readHomeSwitch(int motorIndex) {
    bool switchState = digitalRead(homePins[motorIndex]);
    
    if (endstopTypeNPN[motorIndex]) {
        // NPN: активное состояние = LOW
        return switchState == LOW;
    } else {
        // PNP: активное состояние = HIGH
        return switchState == HIGH;
    }
}

/**
 * Ожидание завершения координированного движения с таймаутом
 */
bool waitForCoordinatedMoveComplete(unsigned long timeoutMs = 60000) {
    unsigned long startTime = millis();
    
    Serial.println("Starting coordinated movement...");
    
    while (multiStepper.run()) {
        if (millis() - startTime > timeoutMs) {
            Serial.println("ERROR: Coordinated movement timeout");
            return false;
        }
        
        // Показываем прогресс каждые 2 секунды
        if ((millis() - startTime) % 2000 < 10) {
            Serial.print("Moving... ");
            for (int i = 0; i < NUM_MOTORS; i++) {
                Serial.print(motorNames[i]);
                Serial.print(":");
                Serial.print(steppers[i]->currentPosition());
                Serial.print(" ");
            }
            Serial.println();
        }
        
        delay(1);
    }
    
    Serial.println("Coordinated movement completed");
    return true;
}

// ============================================
// ОСНОВНЫЕ ФУНКЦИИ УПРАВЛЕНИЯ
// ============================================

/**
 * Координированное движение всех двигателей с использованием MultiStepper
 * @param positions массив позиций в пользовательских единицах
 * @param moveFlags массив флагов движения (true - двигать, false - не двигать)
 */
void coordinatedMove(float positions[NUM_MOTORS], bool moveFlags[NUM_MOTORS]) {
    if (homingActive) {
        Serial.println("ERROR: Cannot move during homing");
        return;
    }
    
    Serial.println("=== COORDINATED MOVE START ===");
    
    // Включаем двигатели
    enableMotors();
    
    // Подготавливаем массив целевых позиций
    long targetPositions[NUM_MOTORS];
    
    for (int i = 0; i < NUM_MOTORS; i++) {
        if (moveFlags[i]) {
            targetPositions[i] = unitsToSteps(i, positions[i]);
            Serial.print(motorNames[i]);
            Serial.print(" -> ");
            Serial.print(positions[i]);
            Serial.print(" units (");
            Serial.print(targetPositions[i]);
            Serial.println(" steps)");
        } else {
            // Если двигатель не двигается, оставляем текущую позицию
            targetPositions[i] = steppers[i]->currentPosition();
            Serial.print(motorNames[i]);
            Serial.println(" -> no movement");
        }
    }
    
    // КРИТИЧЕСКИ ВАЖНО: Используем MultiStepper для координированного движения
    multiStepper.moveTo(targetPositions);
    
    // Ожидаем завершения координированного движения
    if (waitForCoordinatedMoveComplete()) {
        Serial.println("=== COORDINATED MOVE COMPLETED ===");
        
        // Показываем финальные позиции
        for (int i = 0; i < NUM_MOTORS; i++) {
            long currentSteps = steppers[i]->currentPosition();
            float currentUnits = stepsToUnits(i, currentSteps);
            Serial.print(motorNames[i]);
            Serial.print(" final position: ");
            Serial.print(currentUnits, 2);
            Serial.print(" units (");
            Serial.print(currentSteps);
            Serial.println(" steps)");
        }
    } else {
        Serial.println("=== COORDINATED MOVE FAILED ===");
    }
    
    // Отключаем двигатели
    disableMotors();
}

/**
 * Поиск нуля для выбранных двигателей
 * @param homeFlags массив флагов поиска нуля (true - искать, false - пропустить)
 */
void stepperHome(bool homeFlags[NUM_MOTORS]) {
    if (!allMotorsIdle()) {
        Serial.println("ERROR: Motors are moving, cannot start homing");
        return;
    }
    
    homingActive = true;
    Serial.println("=== HOMING PROCEDURE START ===");
    
    enableMotors();
    
    for (int i = 0; i < NUM_MOTORS; i++) {
        if (!homeFlags[i]) continue;
        
        Serial.print("Homing ");
        Serial.print(motorNames[i]);
        Serial.print(" (");
        Serial.print(endstopTypeNPN[i] ? "NPN" : "PNP");
        Serial.println(" sensor)");
        
        // Временно отключаем двигатель от MultiStepper для индивидуального хоминга
        
        // Этап 1: Движение до концевика или лимита шагов
        bool homeSwitchTriggered = false;
        steppers[i]->setMaxSpeed(homingSpeed[i]); // Используем индивидуальную скорость хоминга
        steppers[i]->move(-maxSteps[i]); // Движение в отрицательном направлении
        
        unsigned long startTime = millis();
        while (steppers[i]->isRunning()) {
            steppers[i]->run(); // Обновляем мотор
            
            if (readHomeSwitch(i)) {
                steppers[i]->stop();
                while (steppers[i]->isRunning()) {
                    steppers[i]->run();
                    delay(1);
                }
                steppers[i]->setCurrentPosition(0);
                homeSwitchTriggered = true;
                Serial.print(motorNames[i]);
                Serial.println(" - home switch triggered");
                break;
            }
            
            // Таймаут
            if (millis() - startTime > 30000) {
                steppers[i]->stop();
                while (steppers[i]->isRunning()) {
                    steppers[i]->run();
                    delay(1);
                }
                steppers[i]->setCurrentPosition(0);
                Serial.print("ERROR: ");
                Serial.print(motorNames[i]);
                Serial.println(" - homing timeout");
                break;
            }
            
            delay(1);
        }
        
        if (!homeSwitchTriggered) {
            Serial.print("ERROR: ");
            Serial.print(motorNames[i]);
            Serial.println(" - home switch not found");
            continue;
        }
        
        // Этап 2: Отъезд на заданное расстояние
        delay(100); // Пауза между этапами
        steppers[i]->move(homeBackoff[i]);
        
        while (steppers[i]->isRunning()) {
            steppers[i]->run();
            delay(1);
        }
        
        // Установка нулевой позиции
        steppers[i]->setCurrentPosition(0);
        
        Serial.print(motorNames[i]);
        Serial.println(" - homing completed");
        
        // Восстанавливаем рабочую скорость
        steppers[i]->setMaxSpeed(maxSpeed[i]);
    }
    
    disableMotors();
    homingActive = false;
    Serial.println("=== HOMING PROCEDURE COMPLETED ===");
}

// ============================================
// ОБРАБОТКА SERIAL КОМАНД
// ============================================

/**
 * Команда: steppermove pos0 pos1 pos2 pos3 pos4
 * Перемещение двигателей. Символ '*' означает не двигать двигатель
 */
void cmdStepperMove() {
    float positions[NUM_MOTORS];
    bool moveFlags[NUM_MOTORS];
    char* arg;
    
    for (int i = 0; i < NUM_MOTORS; i++) {
        arg = sCmd.next();
        if (arg == NULL) {
            Serial.println("ERROR: Not enough arguments for steppermove");
            return;
        }
        
        if (strcmp(arg, "*") == 0) {
            moveFlags[i] = false;
            positions[i] = 0;
        } else {
            moveFlags[i] = true;
            positions[i] = atof(arg);
        }
    }
    
    coordinatedMove(positions, moveFlags);
}

/**
 * Команда: stepperhome bool0 bool1 bool2 bool3 bool4
 * Поиск нуля для выбранных двигателей (1 - выполнять, 0 - пропустить)
 */
void cmdStepperHome() {
    bool homeFlags[NUM_MOTORS];
    char* arg;
    
    for (int i = 0; i < NUM_MOTORS; i++) {
        arg = sCmd.next();
        if (arg == NULL) {
            Serial.println("ERROR: Not enough arguments for stepperhome");
            return;
        }
        
        homeFlags[i] = (atoi(arg) != 0);
    }
    
    stepperHome(homeFlags);
}

/**
 * Команда: pinon index
 * Включение дополнительного цифрового выхода
 */
void cmdPinOn() {
    char* arg = sCmd.next();
    if (arg == NULL) {
        Serial.println("ERROR: No index specified for pinon");
        return;
    }
    
    int index = atoi(arg);
    if (index < 0 || index >= NUM_CONTROL_PINS) {
        Serial.print("ERROR: Invalid pin index. Range: 0-");
        Serial.println(NUM_CONTROL_PINS - 1);
        return;
    }
    
    digitalWrite(controlPins[index], HIGH);
    Serial.print("Pin ");
    Serial.print(controlPins[index]);
    Serial.println(" turned ON");
}

/**
 * Команда: pinoff index
 * Отключение дополнительного цифрового выхода
 */
void cmdPinOff() {
    char* arg = sCmd.next();
    if (arg == NULL) {
        Serial.println("ERROR: No index specified for pinoff");
        return;
    }
    
    int index = atoi(arg);
    if (index < 0 || index >= NUM_CONTROL_PINS) {
        Serial.print("ERROR: Invalid pin index. Range: 0-");
        Serial.println(NUM_CONTROL_PINS - 1);
        return;
    }
    
    digitalWrite(controlPins[index], LOW);
    Serial.print("Pin ");
    Serial.print(controlPins[index]);
    Serial.println(" turned OFF");
}

/**
 * Команда: status
 * Вывод текущего состояния системы
 */
void cmdStatus() {
    Serial.println("=== STEPPER SYSTEM STATUS ===");
    Serial.print("Motors enabled: ");
    Serial.println(motorsEnabled ? "YES" : "NO");
    Serial.print("Homing active: ");
    Serial.println(homingActive ? "YES" : "NO");
    Serial.print("All motors idle: ");
    Serial.println(allMotorsIdle() ? "YES" : "NO");
    Serial.print("MultiStepper active: ");
    Serial.println(multiStepper.run() ? "RUNNING" : "IDLE");
    
    Serial.println("\nMotor positions:");
    for (int i = 0; i < NUM_MOTORS; i++) {
        long currentSteps = steppers[i]->currentPosition();
        float currentUnits = stepsToUnits(i, currentSteps);
        Serial.print(motorNames[i]);
        Serial.print(": ");
        Serial.print(currentUnits, 2);
        Serial.print(" units (");
        Serial.print(currentSteps);
        Serial.print(" steps) - ");
        Serial.println(steppers[i]->isRunning() ? "RUNNING" : "IDLE");
    }
    
    Serial.println("\nHome switches:");
    for (int i = 0; i < NUM_MOTORS; i++) {
        Serial.print(motorNames[i]);
        Serial.print(" (");
        Serial.print(endstopTypeNPN[i] ? "NPN" : "PNP");
        Serial.print("): ");
        Serial.println(readHomeSwitch(i) ? "TRIGGERED" : "OPEN");
    }
    
    Serial.println("\nPin configuration:");
    for (int i = 0; i < NUM_MOTORS; i++) {
        Serial.print(motorNames[i]);
        Serial.print(" - Step:");
        Serial.print(stepPins[i]);
        Serial.print(" Dir:");
        Serial.print(dirPins[i]);
        Serial.print(" Enable:");
        Serial.print(enablePins[i]);
        Serial.print(" Home:");
        Serial.println(homePins[i]);
    }
}

/**
 * Неизвестная команда
 */
void cmdUnrecognized(const char* command) {
    Serial.print("ERROR: Unknown command '");
    Serial.print(command);
    Serial.println("'");
    Serial.println("Available commands:");
    Serial.println("  steppermove pos0 pos1 pos2 pos3 pos4  - coordinated movement");
    Serial.println("  stepperhome bool0 bool1 bool2 bool3 bool4  - homing procedure");
    Serial.println("  pinon index  - turn on control pin");
    Serial.println("  pinoff index  - turn off control pin");
    Serial.println("  status  - show system status");
    Serial.println("\nMotor assignment:");
    for (int i = 0; i < NUM_MOTORS; i++) {
        Serial.print("  Motor ");
        Serial.print(i);
        Serial.print(": ");
        Serial.println(motorNames[i]);
    }
    Serial.println("\nFeatures:");
    Serial.println("  - Coordinated movement with MultiStepper");
    Serial.println("  - All motors move simultaneously");
    Serial.println("  - NPN/PNP endstop support");
    Serial.println("  - Analog pins A0, A6, A7 supported");
}

// ============================================
// ИНИЦИАЛИЗАЦИЯ И ОСНОВНОЙ ЦИКЛ
// ============================================

void setup() {
    Serial.begin(115200);
    Serial.println("=== AccelStepper + MultiStepper 5-Motor System ===");
    Serial.println("=== Coordinated Movement with Scheduler ===");
    Serial.println("Initializing...");
    
    // Создание и настройка двигателей
    for (int i = 0; i < NUM_MOTORS; i++) {
        // Создаем объект AccelStepper с интерфейсом DRIVER (step/direction)
        steppers[i] = new AccelStepper(AccelStepper::DRIVER, stepPins[i], dirPins[i]);
        
        if (steppers[i] == NULL) {
            Serial.print("ERROR: Cannot create stepper ");
            Serial.print(i);
            Serial.print(" (");
            Serial.print(motorNames[i]);
            Serial.println(")");
            while (1);
        }
        
        // Настройка пинов enable
        pinMode(enablePins[i], OUTPUT);
        digitalWrite(enablePins[i], HIGH); // Изначально отключены
        
        // Настройка параметров движения
        steppers[i]->setMaxSpeed(maxSpeed[i]);
        steppers[i]->setAcceleration(acceleration[i]);
        steppers[i]->setCurrentPosition(0);
        
        // КРИТИЧЕСКИ ВАЖНО: Добавляем двигатель в MultiStepper
        multiStepper.addStepper(*steppers[i]);
        
        Serial.print(motorNames[i]);
        Serial.print(" initialized - Step:");
        Serial.print(stepPins[i]);
        Serial.print(" Dir:");
        Serial.print(dirPins[i]);
        Serial.print(" Enable:");
        Serial.print(enablePins[i]);
        Serial.print(" Home:");
        Serial.print(homePins[i]);
        Serial.print(" (");
        Serial.print(endstopTypeNPN[i] ? "NPN" : "PNP");
        Serial.println(") - ADDED TO MULTISEPPER");
    }
    
    // Настройка концевых выключателей
    for (int i = 0; i < NUM_MOTORS; i++) {
        pinMode(homePins[i], INPUT_PULLUP);
    }
    
    // Настройка дополнительных управляющих пинов
    for (int i = 0; i < NUM_CONTROL_PINS; i++) {
        pinMode(controlPins[i], OUTPUT);
        digitalWrite(controlPins[i], LOW);
    }
    
    // Настройка Serial команд
    sCmd.addCommand("steppermove", cmdStepperMove);
    sCmd.addCommand("stepperhome", cmdStepperHome);
    sCmd.addCommand("pinon", cmdPinOn);
    sCmd.addCommand("pinoff", cmdPinOff);
    sCmd.addCommand("status", cmdStatus);
    sCmd.setDefaultHandler(cmdUnrecognized);
    
    Serial.println("System initialized successfully!");
    Serial.println("MultiStepper configured for coordinated movement");
    Serial.println("Type 'status' for system information");
    Serial.println("Ready for commands...");
}

void loop() {
    // Обработка Serial команд
    sCmd.readSerial();
    
    // ВАЖНО: Обновление MultiStepper для поддержания координированного движения
    multiStepper.run();
    
    // Небольшая задержка для стабильности
    delay(1);
} 