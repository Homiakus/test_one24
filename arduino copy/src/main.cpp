/**
 * @file: main.cpp
 * @description: Система управления 5 шаговыми двигателями с использованием GyverPlanner
 * @dependencies: GyverPlanner
 * @created: 2024-12-19
 * @updated: 2024-12-19 - переход на GyverPlanner с правильным API
 */

#include <Arduino.h>
#include "GyverPlanner.h"

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
const float maxSpeed[NUM_MOTORS] = {10000.0, 200.0, 4000.0, 30000.0, 30000.0};          // шагов/сек
const float acceleration[NUM_MOTORS] = {10000.0, 300.0, 1000.0, 30000.0, 30000.0};       // шагов/сек²
const long stepsPerRevolution[NUM_MOTORS] = {200, 200, 200, 200, 200};     // шагов на оборот
const float homingSpeed[NUM_MOTORS] = {3000.0, 40.0, 4000.0, 30000.0, 30000.0};        // шагов/сек для хоминга
const bool endstopTypeNPN[NUM_MOTORS] = {false, true, true, true, true};   // тип датчика (true=NPN, false=PNP)

// НОВАЯ НАСТРОЙКА: Управление питанием двигателей
const bool powerAlwaysOn[NUM_MOTORS] = {true, true, true, false, false};   // питание постоянно (true) или временно (false)
// Multi(X): постоянное питание
// Multizone(Y): постоянное питание  
// RRight(Z): постоянное питание
// E0: временное питание (выключается после движения)
// E1: временное питание (выключается после движения)

// Настройки для преобразования единиц (шагов на мм - можно настроить под ваши механизмы)
const long stepsPerUnit[NUM_MOTORS] = {80, 80, 80, 200, 200};                // шагов/мм
const long maxSteps[NUM_MOTORS] = {16000, 16000, 16000, 16000, 16000};      // максимальные шаги для поиска нуля
const long homeBackoff[NUM_MOTORS] = {200, 200, 200, 200, 200};            // шаги отката после касания концевика

// ============================================
// ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ
// ============================================

// Создаем объекты шаговиков для планировщика
Stepper<STEPPER2WIRE> stepper0(stepPins[0], dirPins[0]);
Stepper<STEPPER2WIRE> stepper1(stepPins[1], dirPins[1]);
Stepper<STEPPER2WIRE> stepper2(stepPins[2], dirPins[2]);
Stepper<STEPPER2WIRE> stepper3(stepPins[3], dirPins[3]);
Stepper<STEPPER2WIRE> stepper4(stepPins[4], dirPins[4]);

// Создаем планировщик для 5 осей
GPlanner<STEPPER2WIRE, NUM_MOTORS> planner;

// Массив указателей на шаговики для удобства работы
Stepper<STEPPER2WIRE>* steppers[NUM_MOTORS] = {&stepper0, &stepper1, &stepper2, &stepper3, &stepper4};

bool motorsEnabled = true;
bool homingActive = false;

String inputString = "";
bool stringComplete = false;

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
 * Включение конкретного двигателя
 */
void enableMotor(int motorIndex) {
    digitalWrite(enablePins[motorIndex], LOW); // LOW включает драйвер
    Serial.print(motorNames[motorIndex]);
    Serial.println(" enabled");
}

/**
 * Отключение конкретного двигателя (только если у него временное питание)
 */
void disableMotor(int motorIndex) {
    if (!powerAlwaysOn[motorIndex]) {
        digitalWrite(enablePins[motorIndex], HIGH); // HIGH отключает драйвер
        Serial.print(motorNames[motorIndex]);
        Serial.println(" disabled (temporary power)");
    } else {
        Serial.print(motorNames[motorIndex]);
        Serial.println(" remains enabled (always on power)");
    }
}

/**
 * Включение всех двигателей
 */
void enableMotors() {
    for (int i = 0; i < NUM_MOTORS; i++) {
        enableMotor(i);
    }
    motorsEnabled = true;
    Serial.println("All motors enabled");
}

/**
 * Отключение двигателей согласно их настройкам питания
 */
void disableMotors() {
    bool anyDisabled = false;
    for (int i = 0; i < NUM_MOTORS; i++) {
        if (!powerAlwaysOn[i]) {
            digitalWrite(enablePins[i], HIGH); // HIGH отключает драйвер
            anyDisabled = true;
        }
    }
    
    if (anyDisabled) {
        Serial.print("Temporary power motors disabled: ");
        for (int i = 0; i < NUM_MOTORS; i++) {
            if (!powerAlwaysOn[i]) {
                Serial.print(motorNames[i]);
                Serial.print(" ");
            }
        }
        Serial.println();
    }
    
    Serial.print("Always-on motors remain enabled: ");
    for (int i = 0; i < NUM_MOTORS; i++) {
        if (powerAlwaysOn[i]) {
            Serial.print(motorNames[i]);
            Serial.print(" ");
        }
    }
    Serial.println();
    
    motorsEnabled = false; // Флаг показывает что система в режиме экономии
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

// ============================================
// ОСНОВНЫЕ ФУНКЦИИ УПРАВЛЕНИЯ
// ============================================

/**
 * Функция движения моторов согласно примеру GyverPlanner
 */
void moveMotorsToPosition(float positions[NUM_MOTORS], bool flags[NUM_MOTORS]) {
    if (homingActive) {
        Serial.println("ERROR: Cannot move during homing");
        return;
    }
    
    Serial.println("=== COORDINATED MOVE START ===");
    
    // Включаем двигатели
    enableMotors();
    
    // Подготавливаем целевые позиции
    int32_t targetPositions[NUM_MOTORS];
    for (int i = 0; i < NUM_MOTORS; i++) {
        if (flags[i]) {
            targetPositions[i] = unitsToSteps(i, positions[i]);
            Serial.print(motorNames[i]);
            Serial.print(" -> ");
            Serial.print(positions[i]);
            Serial.print(" units (");
            Serial.print(targetPositions[i]);
            Serial.print(" steps) from current ");
            Serial.print(steppers[i]->pos);
            Serial.println(" steps");
        } else {
            targetPositions[i] = steppers[i]->pos; // Текущая позиция
            Serial.print(motorNames[i]);
            Serial.println(" -> no movement");
        }
    }
    
    // Проверяем, есть ли реальное движение
    bool hasMovement = false;
    for (int i = 0; i < NUM_MOTORS; i++) {
        if (flags[i] && targetPositions[i] != steppers[i]->pos) {
            hasMovement = true;
            break;
        }
    }
    
    if (!hasMovement) {
        Serial.println("WARNING: All motors are already at target positions - no movement needed");
        Serial.println("=== COORDINATED MOVE COMPLETED (NO MOVEMENT) ===");
        disableMotors();
        Serial.println("COMPLETE");
        return;
    }
    
    // Используем правильный API GyverPlanner
    planner.setTarget(targetPositions);
    
    Serial.println("Target set, starting movement...");
    
    // МАКСИМАЛЬНО УПРОЩЕННЫЙ ЦИКЛ - ТОЛЬКО tick()!
    while (!planner.ready()) {
        planner.tick(); // ВСЕ РЕСУРСЫ НА tick()!
    }
    
    // ИСПРАВЛЕНО: Принудительная очистка планировщика
    planner.stop();  // Останавливаем все движения
    delay(50);       // Пауза для стабилизации
    
    Serial.println("=== COORDINATED MOVE COMPLETED ===");
    
    // Показываем финальные позиции
    for (int i = 0; i < NUM_MOTORS; i++) {
        if (flags[i]) {
            long currentSteps = steppers[i]->pos;
            float currentUnits = stepsToUnits(i, currentSteps);
            Serial.print(motorNames[i]);
            Serial.print(" final position: ");
            Serial.print(currentUnits, 2);
            Serial.print(" units (");
            Serial.print(currentSteps);
            Serial.println(" steps)");
        }
    }
    
    disableMotors();
    
    // ОБЯЗАТЕЛЬНЫЙ СТАТУС ЗАВЕРШЕНИЯ
    Serial.println("COMPLETE");
}

/**
 * Поиск нуля для выбранных двигателей согласно примеру
 */
void stepperHome(bool homeFlags[NUM_MOTORS]) {
    // ИСПРАВЛЕНО: Ждем готовности планировщика вместо немедленного отказа
    Serial.println("Waiting for planner to be ready...");
    
    // Добавляем таймаут для ожидания планировщика
    unsigned long waitStart = millis();
    while (!planner.ready()) {
        planner.tick(); // Продолжаем обработку до готовности
        delay(10);      // Небольшая задержка для избежания зависания
        
        // Таймаут ожидания планировщика
        if (millis() - waitStart > 5000) { // 5 секунд максимум
            Serial.println("ERROR: Planner timeout - forcing reset");
            planner.stop();  // Принудительная остановка
            delay(100);
            break;
        }
    }
    
    homingActive = true;
    Serial.println("=== HOMING PROCEDURE START ===");
    
    enableMotors();
    
    bool homingSuccess = true; // Флаг успешности хоминга
    
    // Обрабатываем индивидуальные моторы (Multi, Multizone, RRight)
    for (int i = 0; i < 3; i++) {
        if (!homeFlags[i]) continue;
        
        Serial.print("Homing ");
        Serial.print(motorNames[i]);
        Serial.print(" (");
        Serial.print(endstopTypeNPN[i] ? "NPN" : "PNP");
        Serial.println(" sensor)");
        
        // ИСПРАВЛЕНО: Правильная логика для уже сработавшего датчика
        if (readHomeSwitch(i)) {
            // Датчик уже сработал - сначала отъезжаем от него
            Serial.print(motorNames[i]);
            Serial.println(" - endstop already triggered, moving away first");
            
            planner.setSpeed(i, homingSpeed[i]); // положительная скорость - от концевика
            
            unsigned long moveStart = millis();
            while (readHomeSwitch(i)) {  // пока концевик сработан
                planner.tick();          // отъезжаем
                
                // Таймаут для отъезда
                if (millis() - moveStart > 10000) { // 10 секунд максимум
                    Serial.print("ERROR: ");
                    Serial.print(motorNames[i]);
                    Serial.println(" - timeout moving away from endstop");
                    homingSuccess = false;
                    break;
                }
            }
            
            planner.setSpeed(i, 0);      // останавливаем
            
            if (!homingSuccess) break;
            
            Serial.print(motorNames[i]);
            Serial.println(" - moved away from endstop");
            
            delay(200); // Небольшая пауза для стабилизации
        }
        
        // Теперь движемся к концевику (датчик точно НЕ сработан)
        Serial.print(motorNames[i]);
        Serial.println(" - moving to endstop");
        
        planner.setSpeed(i, -homingSpeed[i]); // отрицательная скорость - к концевику
        
        unsigned long moveStart = millis();
        while (!readHomeSwitch(i)) {  // пока концевик не сработал
            planner.tick();           // крутим
            
            // Таймаут для поиска концевика
            if (millis() - moveStart > 15000) { // 15 секунд максимум
                Serial.print("ERROR: ");
                Serial.print(motorNames[i]);
                Serial.println(" - timeout searching for endstop");
                homingSuccess = false;
                break;
            }
        }
        
        planner.setSpeed(i, 0);       // останавливаем мотор
        
        if (!homingSuccess) break;
        
        Serial.print(motorNames[i]);
        Serial.println(" - endstop triggered");
        
        // ИСПРАВЛЕНО: Устанавливаем нулевую позицию сразу после срабатывания датчика
        Serial.print("Setting ");
        Serial.print(motorNames[i]);
        Serial.println(" position to zero...");
        steppers[i]->pos = 0;  // Устанавливаем позицию в 0
        Serial.print(motorNames[i]);
        Serial.println(" position set to zero");
        
        Serial.print(motorNames[i]);
        Serial.println(" - homing completed");
    }
    
    // Обрабатываем E0 индивидуально (если флаг homeFlags[3] = true)
    if (homeFlags[3] && !homeFlags[4] && homingSuccess) {
        int i = 3; // E0
        Serial.print("Homing ");
        Serial.print(motorNames[i]);
        Serial.print(" individually (");
        Serial.print(endstopTypeNPN[i] ? "NPN" : "PNP");
        Serial.println(" sensor)");
        
        // Аналогичная логика для E0 с таймаутами
        if (readHomeSwitch(i)) {
            Serial.print(motorNames[i]);
            Serial.println(" - endstop already triggered, moving away first");
            
            planner.setSpeed(i, homingSpeed[i]);
            
            unsigned long moveStart = millis();
            while (readHomeSwitch(i)) {
                planner.tick();
                if (millis() - moveStart > 10000) {
                    Serial.print("ERROR: ");
                    Serial.print(motorNames[i]);
                    Serial.println(" - timeout moving away");
                    homingSuccess = false;
                    break;
                }
            }
            
            planner.setSpeed(i, 0);
            
            if (homingSuccess) {
                Serial.print(motorNames[i]);
                Serial.println(" - moved away from endstop");
                delay(200);
            }
        }
        
        if (homingSuccess) {
            Serial.print(motorNames[i]);
            Serial.println(" - moving to endstop");
            
            planner.setSpeed(i, -homingSpeed[i]);
            
            unsigned long moveStart = millis();
            while (!readHomeSwitch(i)) {
                planner.tick();
                if (millis() - moveStart > 15000) {
                    Serial.print("ERROR: ");
                    Serial.print(motorNames[i]);
                    Serial.println(" - timeout searching");
                    homingSuccess = false;
                    break;
                }
            }
            
            planner.setSpeed(i, 0);
            
            if (homingSuccess) {
                Serial.print(motorNames[i]);
                Serial.println(" - endstop triggered");
                
                // ИСПРАВЛЕНО: Устанавливаем нулевую позицию сразу после срабатывания датчика
                Serial.print("Setting ");
                Serial.print(motorNames[i]);
                Serial.println(" position to zero...");
                steppers[i]->pos = 0;  // E0 в позицию 0
                Serial.print(motorNames[i]);
                Serial.println(" position set to zero");
                
                Serial.print(motorNames[i]);
                Serial.println(" - homing completed");
            }
        }
    }
    
    // ОБЩИЙ ХОМИНГ E0 и E1 (если флаг homeFlags[4] = true)
    if (homeFlags[4] && homingSuccess) {
        Serial.println("=== JOINT E0+E1 HOMING ===");
        Serial.print("Homing E0 and E1 together using shared sensor (");
        Serial.print(endstopTypeNPN[3] ? "NPN" : "PNP"); // Используем датчик E0 (индекс 3)
        Serial.println(")");
        
        // Проверяем датчик E0 (который общий для E0 и E1)
        if (readHomeSwitch(3)) { // Датчик уже сработал
            Serial.println("E0+E1 - shared endstop already triggered, moving away first");
            
            // Отъезжаем от датчика координированным движением
            int32_t awayDistance = 1000; // Расстояние отъезда
            int32_t targetPositions[NUM_MOTORS];
            
            for (int i = 0; i < NUM_MOTORS; i++) {
                if (i == 3 || i == 4) { // E0 и E1
                    targetPositions[i] = steppers[i]->pos + awayDistance;
                } else {
                    targetPositions[i] = steppers[i]->pos; // Остальные не двигаются
                }
            }
            
            planner.setTarget(targetPositions);
            
            unsigned long moveStart = millis();
            while (!planner.ready()) {
                planner.tick();
                if (millis() - moveStart > 10000) {
                    Serial.println("ERROR: E0+E1 timeout moving away");
                    homingSuccess = false;
                    break;
                }
            }
            
            if (homingSuccess) {
                Serial.println("E0+E1 - moved away from shared endstop");
                delay(200);
            }
        }
        
        if (homingSuccess) {
            // Теперь движемся к концевику (датчик точно НЕ сработан)
            Serial.println("E0+E1 - moving to shared endstop");
            
            // Используем координированное движение для поиска концевика
            int32_t searchDistance = -50000; // Большое расстояние для поиска
            int32_t targetPositions[NUM_MOTORS];
            
            // Подготавливаем целевые позиции
            for (int i = 0; i < NUM_MOTORS; i++) {
                if (i == 3 || i == 4) { // E0 и E1
                    targetPositions[i] = steppers[i]->pos + searchDistance;
                } else {
                    targetPositions[i] = steppers[i]->pos; // Остальные не двигаются
                }
            }
            
            // Запускаем координированное движение
            planner.setTarget(targetPositions);
            
            Serial.println("Both motors E0 and E1 started coordinated movement...");
            
            // Добавляем счетчик для диагностики
            unsigned long startTime = millis();
            unsigned long lastDiagTime = 0;
            
            while (!readHomeSwitch(3) && !planner.ready()) {  // пока концевик не сработал И движение не завершено
                planner.tick();           // крутим оба мотора
                
                // Диагностика каждые 2 секунды
                if (millis() - lastDiagTime > 2000) {
                    Serial.print("DEBUG: Coordinated homing... Time: ");
                    Serial.print((millis() - startTime) / 1000.0, 1);
                    Serial.print("s, E0 pos: ");
                    Serial.print(steppers[3]->pos);
                    Serial.print(", E1 pos: ");
                    Serial.print(steppers[4]->pos);
                    Serial.print(", Sensor: ");
                    Serial.print(readHomeSwitch(3) ? "TRIGGERED" : "OPEN");
                    Serial.print(", Planner ready: ");
                    Serial.println(planner.ready() ? "YES" : "NO");
                    lastDiagTime = millis();
                }
                
                // Защита от зависания
                if (millis() - startTime > 30000) { // 30 секунд максимум
                    Serial.println("ERROR: E0+E1 homing timeout");
                    homingSuccess = false;
                    break;
                }
            }
            
            // Проверяем причину выхода из цикла
            if (readHomeSwitch(3)) {
                Serial.println("SUCCESS: Shared endstop triggered during coordinated movement");
                
                // ИСПРАВЛЕНО: Устанавливаем нулевую позицию сразу после срабатывания датчика
                Serial.println("Setting E0 and E1 positions to zero...");
                steppers[3]->pos = 0;  // E0 в позицию 0
                steppers[4]->pos = 0;  // E1 в позицию 0
                Serial.println("E0 and E1 positions set to zero");
                
            } else if (planner.ready()) {
                Serial.println("ERROR: Movement completed but endstop not triggered");
                homingSuccess = false;
            } else {
                Serial.println("ERROR: Unknown exit condition from homing loop");
                homingSuccess = false;
            }
            
            // Финальная диагностика с состоянием датчика
            Serial.print("Final positions - E0: ");
            Serial.print(steppers[3]->pos);
            Serial.print(", E1: ");
            Serial.print(steppers[4]->pos);
            Serial.print(", Final sensor state: ");
            Serial.println(readHomeSwitch(3) ? "TRIGGERED" : "OPEN");
            
            Serial.println("E0+E1 - coordinated homing completed");
        }
    }
    
    // ИСПРАВЛЕНО: Принудительная очистка планировщика
    planner.stop();  // Останавливаем все движения
    delay(50);       // Пауза для стабилизации
    
    // ИСПРАВЛЕНО: НЕ вызываем planner.reset() в конце - позиции уже установлены индивидуально
    // planner.reset();    // УБРАНО - позиции устанавливаются индивидуально при срабатывании датчиков
    // delay(50);          // УБРАНО
    
    // ИСПРАВЛЕНО: НЕ отключаем двигатели после хоминга
    // disableMotors(); // УБРАНО - оставляем двигатели включенными
    
    homingActive = false;
    Serial.println("=== HOMING PROCEDURE COMPLETED ===");
    Serial.println("Motors remain enabled for immediate use");
    
    // ОБЯЗАТЕЛЬНЫЙ СТАТУС ЗАВЕРШЕНИЯ
    if (homingSuccess) {
        Serial.println("COMPLETE");
    } else {
        Serial.println("ERROR");
    }
}

// ============================================
// ОБРАБОТКА КОМАНД БЕЗ SERIALCOMMAND
// ============================================

/**
 * Парсинг строки команды и извлечение аргументов
 */
void parseCommand(String command) {
    command.trim();
    int spaceIndex = command.indexOf(' ');
    String cmd = (spaceIndex == -1) ? command : command.substring(0, spaceIndex);
    String args = (spaceIndex == -1) ? "" : command.substring(spaceIndex + 1);
    
    cmd.toLowerCase();
    
    // Определяем тип команды для switch case
    enum CommandType {
        CMD_SM,      // steppermove
        CMD_SH,      // stepperhome
        CMD_PON,     // pinon
        CMD_POFF,    // pinoff
        CMD_STATUS,  // status
        CMD_TEST,    // test
        CMD_UNKNOWN  // неизвестная команда
    };
    
    CommandType cmdType = CMD_UNKNOWN;
    
    // Определяем тип команды
    if (cmd == "sm") {
        cmdType = CMD_SM;
    } else if (cmd == "sh") {
        cmdType = CMD_SH;
    } else if (cmd == "pon") {
        cmdType = CMD_PON;
    } else if (cmd == "poff") {
        cmdType = CMD_POFF;
    } else if (cmd == "status") {
        cmdType = CMD_STATUS;
    } else if (cmd == "test") {
        cmdType = CMD_TEST;
    }
    
    // Обработка команд через switch case
    switch (cmdType) {
        case CMD_SM: {
            // Парсим 5 аргументов для sm (steppermove)
            float positions[NUM_MOTORS];
            bool flags[NUM_MOTORS];
            
            int argCount = 0;
            int lastIndex = 0;
            
            for (int i = 0; i < NUM_MOTORS && argCount < NUM_MOTORS; i++) {
                int nextSpace = args.indexOf(' ', lastIndex);
                String arg = (nextSpace == -1) ? args.substring(lastIndex) : args.substring(lastIndex, nextSpace);
                
                if (arg.length() == 0 && nextSpace == -1) break;
                
                arg.trim();
                if (arg == "*") {
                    flags[i] = false;
                    positions[i] = 0;
                } else {
                    flags[i] = true;
                    positions[i] = arg.toFloat();
                }
                
                argCount++;
                lastIndex = (nextSpace == -1) ? args.length() : nextSpace + 1;
            }
            
            if (argCount == NUM_MOTORS) {
                moveMotorsToPosition(positions, flags);
            } else {
                Serial.print("ERROR: Expected 5 arguments, got ");
                Serial.println(argCount);
                Serial.println("ERROR");
            }
            break;
        }
        
        case CMD_SH: {
            // Парсим 5 аргументов для sh (stepperhome)
            bool homeFlags[NUM_MOTORS];
            
            int argCount = 0;
            int lastIndex = 0;
            
            for (int i = 0; i < NUM_MOTORS && argCount < NUM_MOTORS; i++) {
                int nextSpace = args.indexOf(' ', lastIndex);
                String arg = (nextSpace == -1) ? args.substring(lastIndex) : args.substring(lastIndex, nextSpace);
                
                if (arg.length() == 0 && nextSpace == -1) break;
                
                arg.trim();
                homeFlags[i] = (arg.toInt() != 0);
                
                argCount++;
                lastIndex = (nextSpace == -1) ? args.length() : nextSpace + 1;
            }
            
            if (argCount == NUM_MOTORS) {
                stepperHome(homeFlags);
            } else {
                Serial.print("ERROR: Expected 5 arguments, got ");
                Serial.println(argCount);
                Serial.println("ERROR");
            }
            break;
        }
        
        case CMD_PON: {
            int index = args.toInt();
            if (index >= 0 && index < NUM_CONTROL_PINS) {
                digitalWrite(controlPins[index], HIGH);
                Serial.print("Pin ");
                Serial.print(controlPins[index]);
                Serial.println(" turned ON");
                Serial.println("COMPLETE");
            } else {
                Serial.print("ERROR: Invalid pin index. Range: 0-");
                Serial.println(NUM_CONTROL_PINS - 1);
                Serial.println("ERROR");
            }
            break;
        }
        
        case CMD_POFF: {
            int index = args.toInt();
            if (index >= 0 && index < NUM_CONTROL_PINS) {
                digitalWrite(controlPins[index], LOW);
                Serial.print("Pin ");
                Serial.print(controlPins[index]);
                Serial.println(" turned OFF");
                Serial.println("COMPLETE");
            } else {
                Serial.print("ERROR: Invalid pin index. Range: 0-");
                Serial.println(NUM_CONTROL_PINS - 1);
                Serial.println("ERROR");
            }
            break;
        }
        
        case CMD_STATUS: {
            Serial.println("=== GYVER PLANNER SYSTEM STATUS ===");
            Serial.print("Motors enabled: ");
            Serial.println(motorsEnabled ? "YES" : "NO");
            Serial.print("Homing active: ");
            Serial.println(homingActive ? "YES" : "NO");
            Serial.print("Planner ready: ");
            Serial.println(planner.ready() ? "READY" : "BUSY");
            
            Serial.println("\nMotor positions:");
            for (int i = 0; i < NUM_MOTORS; i++) {
                long currentSteps = steppers[i]->pos;
                float currentUnits = stepsToUnits(i, currentSteps);
                Serial.print(motorNames[i]);
                Serial.print(": ");
                Serial.print(currentUnits, 2);
                Serial.print(" units (");
                Serial.print(currentSteps);
                Serial.println(" steps)");
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
            
            Serial.println("\nMotor power settings:");
            for (int i = 0; i < NUM_MOTORS; i++) {
                Serial.print(motorNames[i]);
                Serial.print(" - Power mode: ");
                Serial.print(powerAlwaysOn[i] ? "ALWAYS ON" : "TEMPORARY");
                Serial.print(", Current state: ");
                bool isEnabled = (digitalRead(enablePins[i]) == LOW);
                Serial.println(isEnabled ? "ENABLED" : "DISABLED");
            }
            
            Serial.println("COMPLETE");
            break;
        }
        
        case CMD_TEST: {
            // Тест всех моторов туда-сюда на 10 единиц в течение 10 секунд
            Serial.println("=== COMPREHENSIVE MOTOR TEST ===");
            Serial.println("Testing all motors with direct pin control");
            Serial.println("Movement: 10 units forward/backward for 10 seconds");
            
            enableMotors();
            
            unsigned long testStartTime = millis();
            unsigned long testDuration = 10000; // 10 секунд
            bool direction = true; // true = вперед, false = назад
            bool testSuccess = true;
            
            while (millis() - testStartTime < testDuration) {
                Serial.print("Direction: ");
                Serial.println(direction ? "FORWARD" : "BACKWARD");
                
                // Устанавливаем направление для всех моторов
                for (int i = 0; i < NUM_MOTORS; i++) {
                    digitalWrite(dirPins[i], direction ? LOW : HIGH);
                }
                
                // Генерируем шаги для всех моторов одновременно
                int stepsToMove = unitsToSteps(0, 10); // 10 единиц для первого мотора (как эталон)
                Serial.print("Generating ");
                Serial.print(stepsToMove);
                Serial.println(" steps for each motor");
                
                for (int step = 0; step < stepsToMove; step++) {
                    // Одновременно шагаем всеми моторами
                    for (int i = 0; i < NUM_MOTORS; i++) {
                        digitalWrite(stepPins[i], HIGH);
                    }
                    delayMicroseconds(500); // Короткий импульс
                    
                    for (int i = 0; i < NUM_MOTORS; i++) {
                        digitalWrite(stepPins[i], LOW);
                    }
                    delayMicroseconds(1500); // Пауза между шагами (скорость ~667 шагов/сек)
                    
                    // Прерываем если время вышло
                    if (millis() - testStartTime >= testDuration) {
                        break;
                    }
                    
                    // Показываем прогресс каждые 100 шагов
                    if (step % 100 == 0) {
                        Serial.print("Step ");
                        Serial.print(step);
                        Serial.print("/");
                        Serial.print(stepsToMove);
                        Serial.print(" - Time: ");
                        Serial.print((millis() - testStartTime) / 1000.0, 1);
                        Serial.println("s");
                    }
                }
                
                // Меняем направление
                direction = !direction;
                delay(500); // Пауза между сменой направления
                
                // Проверяем время
                if (millis() - testStartTime >= testDuration) {
                    break;
                }
            }
            
            Serial.println("=== TEST COMPLETED ===");
            Serial.print("Total test time: ");
            Serial.print((millis() - testStartTime) / 1000.0, 1);
            Serial.println(" seconds");
            
            disableMotors();
            
            if (testSuccess) {
                Serial.println("COMPLETE");
            } else {
                Serial.println("ERROR");
            }
            break;
        }
        
        case CMD_UNKNOWN:
        default: {
            Serial.print("ERROR: Unknown command '");
            Serial.print(cmd);
            Serial.println("'");
            Serial.println("Available commands:");
            Serial.println("  sm pos0 pos1 pos2 pos3 pos4  - coordinated movement (steppermove)");
            Serial.println("  sh bool0 bool1 bool2 bool3 bool4  - homing procedure (stepperhome)");
            Serial.println("    Note: sh flags - Multi Multizone RRight E0_individual E0+E1_joint");
            Serial.println("    Example: sh 1 1 0 0 1 = home Multi, Multizone, and E0+E1 together");
            Serial.println("    Example: sh 0 0 0 1 0 = home only E0 individually");
            Serial.println("  pon index  - turn on control pin (pinon)");
            Serial.println("  poff index  - turn off control pin (pinoff)");
            Serial.println("  status  - show system status");
            Serial.println("  test  - comprehensive motor test (all motors, 10 seconds)");
            Serial.println("\nMotor assignment:");
            for (int i = 0; i < NUM_MOTORS; i++) {
                Serial.print("  Motor ");
                Serial.print(i);
                Serial.print(": ");
                Serial.println(motorNames[i]);
            }
            Serial.println("\nHoming logic:");
            Serial.println("  - Flags 0-2: Individual homing for Multi, Multizone, RRight");
            Serial.println("  - Flag 3: Individual E0 homing (only if flag 4 = 0)");
            Serial.println("  - Flag 4: Joint E0+E1 homing using shared sensor");
            Serial.println("  - If flag 4 = 1, flag 3 is ignored (joint mode takes priority)");
            Serial.println("\nFeatures:");
            Serial.println("  - GyverPlanner for coordinated movement");
            Serial.println("  - Proper API usage with setTarget/setSpeed");
            Serial.println("  - NPN/PNP endstop support");
            Serial.println("  - Analog pins A0, A6, A7 supported");
            Serial.println("  - Direct pin control test mode");
            Serial.println("  - Joint E0+E1 homing with shared sensor");
            Serial.println("  - All commands return COMPLETE or ERROR");
            Serial.println("  - Switch-case architecture for better performance");
            Serial.println("  - Individual motor power management (always-on vs temporary)");
            
            Serial.println("\nMotor power configuration:");
            for (int i = 0; i < NUM_MOTORS; i++) {
                Serial.print("  ");
                Serial.print(motorNames[i]);
                Serial.print(": ");
                Serial.println(powerAlwaysOn[i] ? "ALWAYS ON (never disabled)" : "TEMPORARY (disabled after movement)");
            }
            Serial.println("ERROR");
            break;
        }
    }
    
    // ИСПРАВЛЕНО: Принудительная очистка планировщика после каждой команды
    if (cmdType != CMD_STATUS) { // Статус не требует очистки планировщика
        delay(100);        // Пауза для завершения всех операций
        
        // Принудительно очищаем планировщик если он завис
        if (!planner.ready()) {
            Serial.println("DEBUG: Forcing planner cleanup...");
            planner.stop();
            delay(50);
            // ИСПРАВЛЕНО: Убран planner.reset() чтобы сохранить позиции моторов
            // planner.reset(); // УБРАНО - это сбрасывало позиции в 0
            delay(50);
            Serial.println("DEBUG: Planner cleanup completed");
        }
    }
}

/**
 * Обработка входящих данных Serial
 */
void serialEvent() {
    while (Serial.available()) {
        char inChar = (char)Serial.read();
        
        if (inChar == '\n' || inChar == '\r') {
            if (inputString.length() > 0) {
                stringComplete = true;
            }
        } else {
            inputString += inChar;
        }
    }
}

// ============================================
// ИНИЦИАЛИЗАЦИЯ И ОСНОВНОЙ ЦИКЛ
// ============================================

void setup() {
    Serial.begin(115200);
    Serial.println("=== GyverPlanner 5-Motor System ===");
    Serial.println("=== Proper API Usage ===");
    Serial.println("Initializing...");
    
    // КРИТИЧЕСКИ ВАЖНО: Настройка step и dir пинов как OUTPUT
    for (int i = 0; i < NUM_MOTORS; i++) {
        pinMode(stepPins[i], OUTPUT);
        pinMode(dirPins[i], OUTPUT);
        digitalWrite(stepPins[i], LOW);
        digitalWrite(dirPins[i], LOW);
        Serial.print("Configured pins for ");
        Serial.print(motorNames[i]);
        Serial.print(" - Step:");
        Serial.print(stepPins[i]);
        Serial.print(" Dir:");
        Serial.println(dirPins[i]);
    }
    
    // Настройка пинов enable
    for (int i = 0; i < NUM_MOTORS; i++) {
        pinMode(enablePins[i], OUTPUT);
        digitalWrite(enablePins[i], HIGH); // Изначально отключены
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
    
    // КРИТИЧЕСКИ ВАЖНО: Добавляем шаговики в планировщик
    planner.addStepper(0, stepper0);
    planner.addStepper(1, stepper1);
    planner.addStepper(2, stepper2);
    planner.addStepper(3, stepper3);
    planner.addStepper(4, stepper4);
    
    Serial.println("All steppers added to planner");
    
    // НОВАЯ ЛОГИКА: Включаем двигатели с постоянным питанием
    Serial.println("=== MOTOR POWER INITIALIZATION ===");
    for (int i = 0; i < NUM_MOTORS; i++) {
        if (powerAlwaysOn[i]) {
            digitalWrite(enablePins[i], LOW); // Включаем двигатель
            Serial.print(motorNames[i]);
            Serial.println(" - ALWAYS ON (enabled at startup)");
        } else {
            digitalWrite(enablePins[i], HIGH); // Оставляем выключенным
            Serial.print(motorNames[i]);
            Serial.println(" - TEMPORARY POWER (disabled at startup)");
        }
    }
    Serial.println("Motor power initialization completed");
    
    // ИСПРАВЛЕНО: Устанавливаем высокие общие настройки для быстрого движения E0/E1
    planner.setAcceleration(30000); // Высокое ускорение для E0/E1 (10000 шагов/сек²)
    planner.setMaxSpeed(30000);     // Высокая скорость для E0/E1 (10000 шагов/сек)
    
    Serial.println("High-speed settings applied for E0/E1!");
    Serial.print("Planner MaxSpeed: 10000 steps/sec, Acceleration: 10000 steps/sec²");
    Serial.println();
    
    Serial.println("System initialized successfully!");
    Serial.println("GyverPlanner ready for high-speed coordinated movement");
    Serial.println("Type 'status' for system information");
    Serial.println("Ready for commands...");
}

void loop() {
    
    // Обработка входящих Serial команд
    serialEvent();
    
    if (stringComplete) {
        parseCommand(inputString);
        inputString = "";
        stringComplete = false;
    }
} 