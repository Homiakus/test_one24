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

// Enum для идентификации типов двигателей
enum MotorType {
    MOTOR_MULTI = 0,      // Multi(X)
    MOTOR_MULTIZONE = 1,  // Multizone(Y)
    MOTOR_RRIGHT = 2,     // RRight(Z)
    MOTOR_E0 = 3,         // E0
    MOTOR_E1 = 4          // E1
};

// Enum для контрольных пинов
enum ControlPinType {
    CTRL_PUMP = 0,        // 18
    CTRL_KL1 = 1,         // 8  
    CTRL_KL2 = 2,         // 10
    CTRL_WASTE = 3,       // 19
    CTRL_ROTOR1 = 4,      // 27
    CTRL_ROTOR2 = 5,      // 29
    CTRL_ROTOR3 = 6,      // 23
    CTRL_ROTOR4 = 7,      // 25
    CTRL_HX711_SCK = 8,   // 42
    CTRL_HX711_DT = 9     // 40
};

// Структура конфигурации двигателя
struct MotorConfig {
    int stepPin;
    int dirPin;
    int enablePin;
    int homePin;
    const char* name;
    float maxSpeed;          // шагов/сек
    float acceleration;      // шагов/сек²
    long stepsPerRevolution;
    float homingSpeed;       // шагов/сек для хоминга
    bool endstopTypeNPN;     // тип датчика (true=NPN, false=PNP)
    bool powerAlwaysOn;      // питание постоянно (true) или временно (false)
    long stepsPerUnit;       // шагов/мм
    long maxSteps;           // максимальные шаги для поиска нуля
    long homeBackoff;        // шаги отката после касания концевика
    long preHomingBackoff;   // шаги отъезда перед началом парковки/хоминга
};

// Структура контрольного пина
struct ControlPinConfig {
    int pin;
    const char* name;
};

// Конфигурация всех двигателей
const MotorConfig motorConfigs[NUM_MOTORS] = {
    // MOTOR_MULTI (X-axis)
    {
        .stepPin = A0,
        .dirPin = A1,
        .enablePin = 38,
        .homePin = 14,
        .name = "Multi(X)",
        .maxSpeed = 500.0,
        .acceleration = 500.0,
        .stepsPerRevolution = 200,
        .homingSpeed = 3000.0,
        .endstopTypeNPN = false,
        .powerAlwaysOn = true,
        .stepsPerUnit = 40,
        .maxSteps = 16000,
        .homeBackoff = 1000,
        .preHomingBackoff = 1000
    },
    // MOTOR_MULTIZONE (Y-axis)
    {
        .stepPin = A6,
        .dirPin = A7,
        .enablePin = A2,
        .homePin = 2,
        .name = "Multizone(Y)",
        .maxSpeed = 200.0,
        .acceleration = 300.0,
        .stepsPerRevolution = 200,
        .homingSpeed = 40.0,
        .endstopTypeNPN = true,
        .powerAlwaysOn = true,
        .stepsPerUnit = 80,
        .maxSteps = 16000,
        .homeBackoff = 200,
        .preHomingBackoff = 0
    },
    // MOTOR_RRIGHT (Z-axis)
    {
        .stepPin = 46,
        .dirPin = 48,
        .enablePin = A8,
        .homePin = 2,
        .name = "RRight(Z)",
        .maxSpeed = 1000.0,
        .acceleration = 200.0,
        .stepsPerRevolution = 200,
        .homingSpeed = 10000.0,
        .endstopTypeNPN = true,
        .powerAlwaysOn = true,
        .stepsPerUnit = 200,
        .maxSteps = 16000,
        .homeBackoff = 100,
        .preHomingBackoff = 60
    },
    // MOTOR_E0
    {
        .stepPin = 26,
        .dirPin = 28,
        .enablePin = 24,
        .homePin = 15,
        .name = "E0",
        .maxSpeed = 2000.0,
        .acceleration = 2000.0,
        .stepsPerRevolution = 200,
        .homingSpeed = 2000.0,
        .endstopTypeNPN = true,
        .powerAlwaysOn = false,
        .stepsPerUnit = 200,
        .maxSteps = 16000,
        .homeBackoff = 200,
        .preHomingBackoff = 0
    },
    // MOTOR_E1
    {
        .stepPin = 36,
        .dirPin = 34,
        .enablePin = 30,
        .homePin = 15,
        .name = "E1",
        .maxSpeed = 2000.0,
        .acceleration = 2000.0,
        .stepsPerRevolution = 200,
        .homingSpeed = 2000.0,
        .endstopTypeNPN = true,
        .powerAlwaysOn = false,
        .stepsPerUnit = 200,
        .maxSteps = 16000,
        .homeBackoff = 200,
        .preHomingBackoff = 0
    }
};

// Конфигурация контрольных пинов
const ControlPinConfig controlPinConfigs[] = {
    {18, "PUMP"},
    {8,  "KL1"},
    {10, "KL2"},
    {19, "WASTE"},
    {27, "ROTOR1"},
    {29, "ROTOR2"},
    {23, "ROTOR3"},
    {25, "ROTOR4"},
    {42, "HX711_SCK"},
    {40, "HX711_DT"}
};
const int NUM_CONTROL_PINS = sizeof(controlPinConfigs) / sizeof(controlPinConfigs[0]);

// ============================================
// ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ
// ============================================

// Создаем объекты шаговиков для планировщика
Stepper<STEPPER2WIRE> stepper0(motorConfigs[MOTOR_MULTI].stepPin, motorConfigs[MOTOR_MULTI].dirPin);
Stepper<STEPPER2WIRE> stepper1(motorConfigs[MOTOR_MULTIZONE].stepPin, motorConfigs[MOTOR_MULTIZONE].dirPin);
Stepper<STEPPER2WIRE> stepper2(motorConfigs[MOTOR_RRIGHT].stepPin, motorConfigs[MOTOR_RRIGHT].dirPin);
Stepper<STEPPER2WIRE> stepper3(motorConfigs[MOTOR_E0].stepPin, motorConfigs[MOTOR_E0].dirPin);
Stepper<STEPPER2WIRE> stepper4(motorConfigs[MOTOR_E1].stepPin, motorConfigs[MOTOR_E1].dirPin);

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
long unitsToSteps(MotorType motorType, float units) {
    return (long)(units * motorConfigs[motorType].stepsPerUnit);
}

/**
 * Преобразование шагов в пользовательские единицы
 */
float stepsToUnits(MotorType motorType, long steps) {
    return (float)steps / motorConfigs[motorType].stepsPerUnit;
}

/**
 * Включение конкретного двигателя
 */
void enableMotor(MotorType motorType) {
    digitalWrite(motorConfigs[motorType].enablePin, LOW); // LOW включает драйвер
    Serial.print(motorConfigs[motorType].name);
    Serial.println(" enabled");
}

/**
 * Отключение конкретного двигателя (только если у него временное питание)
 */
void disableMotor(MotorType motorType) {
    if (!motorConfigs[motorType].powerAlwaysOn) {
        digitalWrite(motorConfigs[motorType].enablePin, HIGH); // HIGH отключает драйвер
        Serial.print(motorConfigs[motorType].name);
        Serial.println(" disabled (temporary power)");
    } else {
        Serial.print(motorConfigs[motorType].name);
        Serial.println(" remains enabled (always on power)");
    }
}

/**
 * Включение всех двигателей
 */
void enableMotors() {
    for (int i = 0; i < NUM_MOTORS; i++) {
        enableMotor((MotorType)i);
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
        if (!motorConfigs[i].powerAlwaysOn) {
            digitalWrite(motorConfigs[i].enablePin, HIGH); // HIGH отключает драйвер
            anyDisabled = true;
        }
    }
    
    if (anyDisabled) {
        Serial.print("Temporary power motors disabled: ");
        for (int i = 0; i < NUM_MOTORS; i++) {
            if (!motorConfigs[i].powerAlwaysOn) {
                Serial.print(motorConfigs[i].name);
                Serial.print(" ");
            }
        }
        Serial.println();
    }
    
    Serial.print("Always-on motors remain enabled: ");
    for (int i = 0; i < NUM_MOTORS; i++) {
        if (motorConfigs[i].powerAlwaysOn) {
            Serial.print(motorConfigs[i].name);
            Serial.print(" ");
        }
    }
    Serial.println();
    
    motorsEnabled = false; // Флаг показывает что система в режиме экономии
}

/**
 * Чтение состояния концевого выключателя с учетом типа (NPN/PNP)
 */
bool readHomeSwitch(MotorType motorType) {
    bool switchState = digitalRead(motorConfigs[motorType].homePin);
    
    if (motorConfigs[motorType].endstopTypeNPN) {
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
            targetPositions[i] = unitsToSteps((MotorType)i, positions[i]);
            Serial.print(motorConfigs[i].name);
            Serial.print(" -> ");
            Serial.print(positions[i]);
            Serial.print(" units (");
            Serial.print(targetPositions[i]);
            Serial.print(" steps) from current ");
            Serial.print(steppers[i]->pos);
            Serial.println(" steps");
        } else {
            targetPositions[i] = steppers[i]->pos; // Текущая позиция
            Serial.print(motorConfigs[i].name);
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
    
    // ИСПРАВЛЕНО: Правильная очистка планировщика
    
    Serial.println("=== COORDINATED MOVE COMPLETED ===");
    
    // Показываем финальные позиции
    for (int i = 0; i < NUM_MOTORS; i++) {
        if (flags[i]) {
            long currentSteps = steppers[i]->pos;
            float currentUnits = stepsToUnits((MotorType)i, currentSteps);
            Serial.print(motorConfigs[i].name);
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
 * Упрощенный поиск нуля для выбранных двигателей по образцу GyverPlanner
 */
void stepperHome(bool homeFlags[NUM_MOTORS]) {
    homingActive = true;
    Serial.println("=== TARGET-BASED HOMING PROCEDURE START ===");

    enableMotors();

    /* --------------------------------------------------
     * ЭТАП 1. Предварительный отъезд (preHomingBackoff)
     * -------------------------------------------------- */
    int32_t preBackoffPos[NUM_MOTORS];
    bool needPreBackoff = false;
    for (int i = 0; i < NUM_MOTORS; i++) {
        preBackoffPos[i] = steppers[i]->pos; // базовые – текущие позиции
    }
    for (int i = 0; i < 4; i++) { // работаем только с 0-3, E1 хомится в clampHome
        if (!homeFlags[i]) continue;
        long backoff = motorConfigs[i].preHomingBackoff;
        if (backoff > 0) {
            needPreBackoff = true;
            preBackoffPos[i] += backoff; // положительное направление – «от концевика»
            Serial.print(motorConfigs[i].name);
            Serial.print(" – pre-homing backoff: ");
            Serial.print(backoff);
            Serial.println(" steps");
        }
    }
    if (needPreBackoff) {
        planner.setTarget(preBackoffPos);
        while (!planner.ready()) planner.tick();
        planner.brake();
        Serial.println("Pre-homing backoff completed");
    }

    /* --------------------------------------------------
     * ЭТАП 2. Отъезд, если концевик уже сработал
     * -------------------------------------------------- */
    int32_t moveAwayPos[NUM_MOTORS];
    bool needMoveAway = false;
    for (int i = 0; i < NUM_MOTORS; i++) moveAwayPos[i] = steppers[i]->pos;
    for (int i = 0; i < 4; i++) {
        if (!homeFlags[i]) continue;
        if (readHomeSwitch((MotorType)i)) {
            needMoveAway = true;
            moveAwayPos[i] += 500; // фиксированное значение «дополнительного» отъезда
            Serial.print(motorConfigs[i].name);
            Serial.println(" – endstop already triggered, moving away 500 steps");
        }
    }
    if (needMoveAway) {
        planner.setTarget(moveAwayPos);
        while (!planner.ready()) planner.tick();
        planner.brake();
        Serial.println("Move-away completed");
    }

    /* --------------------------------------------------
     * ЭТАП 3. Движение к концевику (координированное)
     * -------------------------------------------------- */
    int32_t seekPos[NUM_MOTORS];
    for (int i = 0; i < NUM_MOTORS; i++) seekPos[i] = steppers[i]->pos;
    for (int i = 0; i < 4; i++) {
        if (!homeFlags[i]) continue;
        seekPos[i] = steppers[i]->pos - motorConfigs[i].maxSteps; // «к концевику» – отрицательное направление
        Serial.print(motorConfigs[i].name);
        Serial.print(" target: ");
        Serial.print(seekPos[i]);
        Serial.println(" steps (toward endstop)");
    }
    planner.setTarget(seekPos);

    bool homed[NUM_MOTORS] = {false};
    while (true) {
        planner.tick();
        bool allDone = true;
        for (int i = 0; i < 4; i++) {
            if (!homeFlags[i] || homed[i]) continue;
            if (readHomeSwitch((MotorType)i)) {
                homed[i] = true;
                Serial.print(motorConfigs[i].name);
                Serial.print(" – endstop reached at position ");
                Serial.println(steppers[i]->pos);
            }
            if (!homed[i]) allDone = false;
        }
        if (allDone) break;
        if (planner.ready()) {
            Serial.println("WARNING: Maximum homing distance reached without triggering all endstops");
            break;
        }
    }
    planner.brake();

    /* --------------------------------------------------
     * ЭТАП 4. Финальный откат (homeBackoff)
     * -------------------------------------------------- */
    int32_t backoffPos[NUM_MOTORS];
    bool needFinalBackoff = false;
    for (int i = 0; i < NUM_MOTORS; i++) backoffPos[i] = steppers[i]->pos;
    for (int i = 0; i < 4; i++) {
        if (!homeFlags[i] || !homed[i]) continue;
        long hBack = motorConfigs[i].homeBackoff;
        if (hBack > 0) {
            needFinalBackoff = true;
            backoffPos[i] += hBack; // «отъезд от концевика»
            Serial.print(motorConfigs[i].name);
            Serial.print(" – final backoff: ");
            Serial.print(hBack);
            Serial.println(" steps");
        }
    }
    if (needFinalBackoff) {
        planner.setTarget(backoffPos);
        while (!planner.ready()) planner.tick();
        planner.brake();
        Serial.println("Final backoff completed");
    }

    /* --------------------------------------------------
     * Установка нуля для успешно отхомленных моторов
     * -------------------------------------------------- */
    for (int i = 0; i < 4; i++) {
        if (homeFlags[i] && homed[i]) {
            steppers[i]->pos = 0;
            Serial.print(motorConfigs[i].name);
            Serial.println(" position set to zero");
        } else if (homeFlags[i] && !homed[i]) {
            Serial.print("WARNING: ");
            Serial.print(motorConfigs[i].name);
            Serial.println(" homing incomplete – endstop not reached");
        }
    }

    // Сбрасываем планировщик, чтобы все координаты были согласованы
    planner.reset();
    Serial.println("Planner reset – all internal coordinates set to zero");

    homingActive = false;
    Serial.println("=== TARGET-BASED HOMING PROCEDURE COMPLETED ===");
    Serial.println("COMPLETE");
}

/**
 * Улучшенный координированный хоминг E0+E1 с движением к цели и остановкой по концевикам
 */
void clampHome() {
    homingActive = true;
    Serial.println("=== IMPROVED E0+E1 HOMING START ===");
    
    enableMotors();
    
    // Проверяем общий датчик E0 (используется для E0 и E1)
    Serial.println("E0+E1 - checking shared endstop configuration");
    
    // ЭТАП 1: Предварительный отъезд (preHomingBackoff) - ВСЕГДА если > 0 для любого из моторов
    long maxPreBackoff = max(motorConfigs[MOTOR_E0].preHomingBackoff, motorConfigs[MOTOR_E1].preHomingBackoff);
    if (maxPreBackoff > 0) {
        Serial.print("E0+E1 - pre-homing backoff: ");
        Serial.print(maxPreBackoff);
        Serial.println(" steps");
        
        int32_t preBackoffPositions[NUM_MOTORS];
        for (int i = 0; i < NUM_MOTORS; i++) {
            preBackoffPositions[i] = steppers[i]->pos; // текущие позиции
        }
        
        // Отъезжаем на максимальное значение preHomingBackoff
        preBackoffPositions[MOTOR_E0] = steppers[MOTOR_E0]->pos + maxPreBackoff;
        preBackoffPositions[MOTOR_E1] = steppers[MOTOR_E1]->pos + maxPreBackoff;
        
        planner.setTarget(preBackoffPositions);
        
        // Ждем завершения предварительного отъезда
        while (!planner.ready()) {
            planner.tick();
        }
        planner.brake();
        Serial.println("E0+E1 - pre-homing backoff completed");
    }
    
    // ЭТАП 2: Если любой из концевиков уже сработал - отъезжаем от него дополнительно 
    bool e0EndstopActive = readHomeSwitch(MOTOR_E0);
    bool e1EndstopActive = readHomeSwitch(MOTOR_E1);
    
    if (e0EndstopActive || e1EndstopActive) {
        Serial.println("E0+E1 - endstop(s) already triggered, moving away additionally");
        
        // Подготавливаем дополнительные отъездные позиции 
        int32_t moveAwayPositions[NUM_MOTORS];
        for (int i = 0; i < NUM_MOTORS; i++) {
            moveAwayPositions[i] = steppers[i]->pos; // текущие позиции
        }
        
        // Дополнительно отъезжаем на 500 шагов для активных моторов
        moveAwayPositions[MOTOR_E0] = steppers[MOTOR_E0]->pos + 500;
        moveAwayPositions[MOTOR_E1] = steppers[MOTOR_E1]->pos + 500;
        
        planner.setTarget(moveAwayPositions);
        
        // Ждем завершения отъезда или отключения концевиков
        while (!planner.ready() && (readHomeSwitch(MOTOR_E0) || readHomeSwitch(MOTOR_E1))) {
            planner.tick();
        }
        planner.brake();
        Serial.println("E0+E1 - moved away from endstop(s) additionally");
    }
    
    // ЭТАП 3: Движемся к концевикам с использованием координированного движения
    Serial.println("E0+E1 - starting coordinated movement to endstops");
    
    // Подготавливаем далекие целевые позиции в направлении концевиков
    int32_t homingTargetPositions[NUM_MOTORS];
    for (int i = 0; i < NUM_MOTORS; i++) {
        homingTargetPositions[i] = steppers[i]->pos; // базовые позиции - текущие
    }
    
    // Задаем далекие цели для E0 и E1 (в отрицательном направлении к концевикам)
    homingTargetPositions[MOTOR_E0] = steppers[MOTOR_E0]->pos - motorConfigs[MOTOR_E0].maxSteps;
    homingTargetPositions[MOTOR_E1] = steppers[MOTOR_E1]->pos - motorConfigs[MOTOR_E1].maxSteps;
    
    Serial.print("E0 target: ");
    Serial.print(homingTargetPositions[MOTOR_E0]);
    Serial.print(" steps, E1 target: ");
    Serial.print(homingTargetPositions[MOTOR_E1]);
    Serial.println(" steps");
    
    // Устанавливаем координированные цели
    planner.setTarget(homingTargetPositions);
    
    // Флаги для отслеживания завершения хоминга каждого мотора
    bool e0HomingComplete = false;
    bool e1HomingComplete = false;
    
    // Сохраняем позиции для принудительной остановки
    int32_t e0StopPosition = steppers[MOTOR_E0]->pos;
    int32_t e1StopPosition = steppers[MOTOR_E1]->pos;
    
    Serial.println("Starting homing movement...");
    
    // Основной цикл хоминга с проверкой концевиков
    while (!e0HomingComplete || !e1HomingComplete) {
        planner.tick();
        
        // Проверяем концевик E0
        if (!e0HomingComplete && readHomeSwitch(MOTOR_E0)) {
            e0HomingComplete = true;
            e0StopPosition = steppers[MOTOR_E0]->pos;
            Serial.print("E0 endstop reached at position: ");
            Serial.println(e0StopPosition);
        }
        
        // Проверяем концевик E1 (может быть тот же физический датчик)
        if (!e1HomingComplete && readHomeSwitch(MOTOR_E1)) {
            e1HomingComplete = true;
            e1StopPosition = steppers[MOTOR_E1]->pos;
            Serial.print("E1 endstop reached at position: ");
            Serial.println(e1StopPosition);
        }
        
        // Если оба мотора достигли концевиков - выходим
        if (e0HomingComplete && e1HomingComplete) {
            break;
        }
        
        // Проверяем не достигли ли мы максимального расстояния
        if (planner.ready()) {
            Serial.println("WARNING: Maximum homing distance reached");
            break;
        }
    }
    
    // Принудительно останавливаем движение
    planner.brake();
    
    // ЭТАП 4: Финальный откат (homeBackoff) - ВСЕГДА если хоминг успешен
    if (e0HomingComplete && e1HomingComplete) {
        Serial.println("E0+E1 - both endstops reached, performing final backoff");
        
        // Подготавливаем позиции для финального отката
        int32_t finalBackoffPositions[NUM_MOTORS];
        for (int i = 0; i < NUM_MOTORS; i++) {
            finalBackoffPositions[i] = steppers[i]->pos; // текущие позиции
        }
        
        // Отъезжаем на homeBackoff шагов от концевиков
        finalBackoffPositions[MOTOR_E0] = steppers[MOTOR_E0]->pos + motorConfigs[MOTOR_E0].homeBackoff;
        finalBackoffPositions[MOTOR_E1] = steppers[MOTOR_E1]->pos + motorConfigs[MOTOR_E1].homeBackoff;
        
        Serial.print("E0 backoff: ");
        Serial.print(motorConfigs[MOTOR_E0].homeBackoff);
        Serial.print(" steps, E1 backoff: ");
        Serial.print(motorConfigs[MOTOR_E1].homeBackoff);
        Serial.println(" steps");
        
        planner.setTarget(finalBackoffPositions);
        
        // Ждем завершения финального отката
        while (!planner.ready()) {
            planner.tick();
        }
        planner.brake();
        
        Serial.println("E0+E1 - final backoff completed");
        
        // Устанавливаем нулевые позиции после финального отката
        steppers[MOTOR_E0]->pos = 0; 
        steppers[MOTOR_E1]->pos = 0;
        Serial.println("E0 and E1 positions set to zero");
        
    } else {
        // Если хоминг неуспешен - не делаем откат, просто сообщаем об ошибке
        if (e0HomingComplete) {
            steppers[MOTOR_E0]->pos = 0;
            Serial.println("E0 position set to zero (partial success)");
        } else {
            Serial.println("WARNING: E0 homing incomplete - endstop not reached");
        }
        
        if (e1HomingComplete) {
            steppers[MOTOR_E1]->pos = 0;
            Serial.println("E1 position set to zero (partial success)");
        } else {
            Serial.println("WARNING: E1 homing incomplete - endstop not reached");
        }
    }
    
    homingActive = false;
    Serial.println("=== IMPROVED E0+E1 HOMING COMPLETED ===");
    
    // Отчет о результатах
    Serial.print("E0 final position: ");
    Serial.print(steppers[MOTOR_E0]->pos);
    Serial.print(" steps, E1 final position: ");
    Serial.print(steppers[MOTOR_E1]->pos);
    Serial.println(" steps");
    
    // Проверяем успешность хоминга - ERROR если хотя бы один мотор не достиг концевика
    if (e0HomingComplete && e1HomingComplete) {
        Serial.println("COMPLETE");
    } else {
        Serial.println("ERROR: Homing failed - one or more endstops not reached");
        Serial.println("ERROR");
    }
}

// ============================================
// ОБРАБОТКА КОМАНД БЕЗ SERIALCOMMAND
// ============================================

/**
 * Получение числового кода команды для switch-case
 */
int getCommandCode(String cmd) {
    if (cmd == "sm") return 1;
    if (cmd == "sh") return 2;
    if (cmd == "pon") return 3;
    if (cmd == "poff") return 4;
    if (cmd == "status") return 5;
    if (cmd == "test") return 6;
    if (cmd == "clamph") return 7;
    return 0; // неизвестная команда
}

/**
 * Обработка команды steppermove (sm)
 */
void handleStepperMove(String args) {
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
}

/**
 * Обработка команды stepperhome (sh)
 */
void handleStepperHome(String args) {
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
}

/**
 * Обработка команды pinon (pon)
 */
void handlePinOn(String args) {
    int index = args.toInt();
    if (index >= 0 && index < NUM_CONTROL_PINS) {
        digitalWrite(controlPinConfigs[index].pin, HIGH);
        Serial.print("Pin ");
        Serial.print(controlPinConfigs[index].pin);
        Serial.print(" (");
        Serial.print(controlPinConfigs[index].name);
        Serial.println(") turned ON");
        Serial.println("COMPLETE");
    } else {
        Serial.print("ERROR: Invalid pin index. Range: 0-");
        Serial.println(NUM_CONTROL_PINS - 1);
        Serial.println("ERROR");
    }
}

/**
 * Обработка команды pinoff (poff)
 */
void handlePinOff(String args) {
    int index = args.toInt();
    if (index >= 0 && index < NUM_CONTROL_PINS) {
        digitalWrite(controlPinConfigs[index].pin, LOW);
        Serial.print("Pin ");
        Serial.print(controlPinConfigs[index].pin);
        Serial.print(" (");
        Serial.print(controlPinConfigs[index].name);
        Serial.println(") turned OFF");
        Serial.println("COMPLETE");
    } else {
        Serial.print("ERROR: Invalid pin index. Range: 0-");
        Serial.println(NUM_CONTROL_PINS - 1);
        Serial.println("ERROR");
    }
}

/**
 * Обработка команды status
 */
void handleStatus() {
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
        float currentUnits = stepsToUnits((MotorType)i, currentSteps);
        Serial.print(motorConfigs[i].name);
        Serial.print(": ");
        Serial.print(currentUnits, 2);
        Serial.print(" units (");
        Serial.print(currentSteps);
        Serial.println(" steps)");
    }
    
    Serial.println("\nHome switches:");
    for (int i = 0; i < NUM_MOTORS; i++) {
        Serial.print(motorConfigs[i].name);
        Serial.print(" (");
        Serial.print(motorConfigs[i].endstopTypeNPN ? "NPN" : "PNP");
        Serial.print("): ");
        Serial.println(readHomeSwitch((MotorType)i) ? "TRIGGERED" : "OPEN");
    }
    
    Serial.println("\nPin configuration:");
    for (int i = 0; i < NUM_MOTORS; i++) {
        Serial.print(motorConfigs[i].name);
        Serial.print(" - Step:");
        Serial.print(motorConfigs[i].stepPin);
        Serial.print(" Dir:");
        Serial.print(motorConfigs[i].dirPin);
        Serial.print(" Enable:");
        Serial.print(motorConfigs[i].enablePin);
        Serial.print(" Home:");
        Serial.println(motorConfigs[i].homePin);
    }
    
    Serial.println("\nMotor power settings:");
    for (int i = 0; i < NUM_MOTORS; i++) {
        Serial.print(motorConfigs[i].name);
        Serial.print(" - Power mode: ");
        Serial.print(motorConfigs[i].powerAlwaysOn ? "ALWAYS ON" : "TEMPORARY");
        Serial.print(", Current state: ");
        bool isEnabled = (digitalRead(motorConfigs[i].enablePin) == LOW);
        Serial.println(isEnabled ? "ENABLED" : "DISABLED");
    }
    
    Serial.println("\nControl pins:");
    for (int i = 0; i < NUM_CONTROL_PINS; i++) {
        Serial.print("Index ");
        Serial.print(i);
        Serial.print(": Pin ");
        Serial.print(controlPinConfigs[i].pin);
        Serial.print(" (");
        Serial.print(controlPinConfigs[i].name);
        Serial.print(") - State: ");
        Serial.println(digitalRead(controlPinConfigs[i].pin) ? "HIGH" : "LOW");
    }
    
    Serial.println("COMPLETE");
}

/**
 * Обработка команды test
 */
void handleTest() {
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
            digitalWrite(motorConfigs[i].dirPin, direction ? LOW : HIGH);
        }
        
        // Генерируем шаги для всех моторов одновременно
        int stepsToMove = unitsToSteps(MOTOR_MULTI, 10); // 10 единиц для первого мотора (как эталон)
        Serial.print("Generating ");
        Serial.print(stepsToMove);
        Serial.println(" steps for each motor");
        
        for (int step = 0; step < stepsToMove; step++) {
            // Одновременно шагаем всеми моторами
            for (int i = 0; i < NUM_MOTORS; i++) {
                digitalWrite(motorConfigs[i].stepPin, HIGH);
            }
            delayMicroseconds(500); // Короткий импульс
            
            for (int i = 0; i < NUM_MOTORS; i++) {
                digitalWrite(motorConfigs[i].stepPin, LOW);
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
}

/**
 * Обработка команды clamph (координированный хоминг E0+E1)
 */
void handleClampHome(String args) {
    clampHome();
}

/**
 * Обработка неизвестной команды
 */
void handleUnknownCommand(String cmd) {
    Serial.print("ERROR: Unknown command '");
    Serial.print(cmd);
    Serial.println("'");
    Serial.println("Available commands:");
    Serial.println("  sm pos0 pos1 pos2 pos3 pos4  - coordinated movement (steppermove)");
    Serial.println("  sh bool0 bool1 bool2 bool3 0  - individual homing (stepperhome)");
    Serial.println("    Note: sh flags - Multi Multizone RRight E0 (E1 not supported, use clamph)");
    Serial.println("    Example: sh 1 1 0 1 0 = home Multi, Multizone, and E0 individually");
    Serial.println("  clamph  - coordinated E0+E1 homing using shared sensor");
    Serial.println("  pon index  - turn on control pin (pinon)");
    Serial.println("  poff index  - turn off control pin (pinoff)");
    Serial.println("  status  - show system status");
    Serial.println("  test  - comprehensive motor test (all motors, 10 seconds)");
    Serial.println("\nMotor assignment:");
    for (int i = 0; i < NUM_MOTORS; i++) {
        Serial.print("  Motor ");
        Serial.print(i);
        Serial.print(": ");
        Serial.println(motorConfigs[i].name);
    }
    Serial.println("\nControl pins assignment:");
    for (int i = 0; i < NUM_CONTROL_PINS; i++) {
        Serial.print("  Index ");
        Serial.print(i);
        Serial.print(": Pin ");
        Serial.print(controlPinConfigs[i].pin);
        Serial.print(" (");
        Serial.print(controlPinConfigs[i].name);
        Serial.println(")");
    }
    Serial.println("\nHoming logic:");
    Serial.println("  - sh command: Individual homing for Multi, Multizone, RRight, E0 (using setSpeed)");
    Serial.println("  - clamph command: Coordinated E0+E1 homing using shared sensor (using setTarget)");
    Serial.println("  - sh flag 4 (E1) is ignored - use clamph for E0+E1 coordinated homing");
    Serial.println("\nFeatures:");
    Serial.println("  - GyverPlanner for coordinated movement");
    Serial.println("  - Separate homing methods: setSpeed for individual, setTarget for coordinated");
    Serial.println("  - NPN/PNP endstop support");
    Serial.println("  - Analog pins A0, A6, A7 supported");
    Serial.println("  - Direct pin control test mode");
    Serial.println("  - All commands return COMPLETE or ERROR");
    Serial.println("  - Structured configuration with enum types");
    Serial.println("  - Simplified logic without timeouts");
    
    Serial.println("\nMotor power configuration:");
    for (int i = 0; i < NUM_MOTORS; i++) {
        Serial.print("  ");
        Serial.print(motorConfigs[i].name);
        Serial.print(": ");
        Serial.println(motorConfigs[i].powerAlwaysOn ? "ALWAYS ON (never disabled)" : "TEMPORARY (disabled after movement)");
    }
    Serial.println("ERROR");
}

/**
 * Парсинг строки команды и извлечение аргументов
 */
void parseCommand(String command) {
    command.trim();
    Serial.println("RECEIVED");
    int spaceIndex = command.indexOf(' ');
    String cmd = (spaceIndex == -1) ? command : command.substring(0, spaceIndex);
    String args = (spaceIndex == -1) ? "" : command.substring(spaceIndex + 1);
    
    cmd.toLowerCase();
    
    // Получаем код команды для switch-case
    int cmdCode = getCommandCode(cmd);
    
    // Обработка команд через switch-case с отдельными функциями
    switch (cmdCode) {
        case 1: // sm
            handleStepperMove(args);
            break;
            
        case 2: // sh
            handleStepperHome(args);
            break;
            
        case 3: // pon
            handlePinOn(args);
            break;
            
        case 4: // poff
            handlePinOff(args);
            break;
            
        case 5: // status
            handleStatus();
            break;
            
        case 6: // test
            handleTest();
            break;
            
        case 7: // clamph
            handleClampHome(args);
            break;
            
        default: // неизвестная команда
            handleUnknownCommand(cmd);
            break;
    }
    
    // ИСПРАВЛЕНО: Убрана принудительная очистка планировщика с planner.reset()
    // planner.reset() сбрасывает все координаты в 0, что неправильно!
    // Согласно примеру GyverPlanner, reset() нужен только при инициализации и после хоминга
    if (cmdCode != 5) { // Статус не требует дополнительных действий
        delay(100);        // Пауза для завершения всех операций
        
        // Проверяем готовность планировщика без принудительного сброса координат
        if (!planner.ready()) {
            Serial.println("DEBUG: Planner still busy after command completion");
            // НЕ вызываем planner.reset() - это сбросит координаты!
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
        pinMode(motorConfigs[i].stepPin, OUTPUT);
        pinMode(motorConfigs[i].dirPin, OUTPUT);
        digitalWrite(motorConfigs[i].stepPin, LOW);
        digitalWrite(motorConfigs[i].dirPin, LOW);
        Serial.print("Configured pins for ");
        Serial.print(motorConfigs[i].name);
        Serial.print(" - Step:");
        Serial.print(motorConfigs[i].stepPin);
        Serial.print(" Dir:");
        Serial.println(motorConfigs[i].dirPin);
    }
    
    // Настройка пинов enable
    for (int i = 0; i < NUM_MOTORS; i++) {
        pinMode(motorConfigs[i].enablePin, OUTPUT);
        digitalWrite(motorConfigs[i].enablePin, HIGH); // Изначально отключены
    }
    
    // Настройка концевых выключателей
    for (int i = 0; i < NUM_MOTORS; i++) {
        pinMode(motorConfigs[i].homePin, INPUT_PULLUP);
    }
    
    // Настройка дополнительных управляющих пинов
    for (int i = 0; i < NUM_CONTROL_PINS; i++) {
        pinMode(controlPinConfigs[i].pin, OUTPUT);
        digitalWrite(controlPinConfigs[i].pin, LOW);
        Serial.print("Configured control pin ");
        Serial.print(controlPinConfigs[i].pin);
        Serial.print(" (");
        Serial.print(controlPinConfigs[i].name);
        Serial.println(")");
    }
    
    // КРИТИЧЕСКИ ВАЖНО: Добавляем шаговики в планировщик
    planner.addStepper(0, stepper0);
    planner.addStepper(1, stepper1);
    planner.addStepper(2, stepper2);
    planner.addStepper(3, stepper3);
    planner.addStepper(4, stepper4);
    
    Serial.println("All steppers added to planner");
    
    // ИСПРАВЛЕНО: Начальный сброс позиций согласно примеру GyverPlanner
    planner.reset();  // сбрасываем все позиции в 0 (они и так в 0 при запуске)
    Serial.println("Initial position reset completed");
    
    // НОВАЯ ЛОГИКА: Включаем двигатели с постоянным питанием
    Serial.println("=== MOTOR POWER INITIALIZATION ===");
    for (int i = 0; i < NUM_MOTORS; i++) {
        if (motorConfigs[i].powerAlwaysOn) {
            digitalWrite(motorConfigs[i].enablePin, LOW); // Включаем двигатель
            Serial.print(motorConfigs[i].name);
            Serial.println(" - ALWAYS ON (enabled at startup)");
        } else {
            digitalWrite(motorConfigs[i].enablePin, HIGH); // Оставляем выключенным
            Serial.print(motorConfigs[i].name);
            Serial.println(" - TEMPORARY POWER (disabled at startup)");
        }
    }
    Serial.println("Motor power initialization completed");
    
    // ИСПРАВЛЕНО: Устанавливаем высокие общие настройки для быстрого движения E0/E1
    planner.setAcceleration(30000); // Высокое ускорение для E0/E1
    planner.setMaxSpeed(30000);     // Высокая скорость для E0/E1
    
    Serial.println("High-speed settings applied for E0/E1!");
    Serial.print("Planner MaxSpeed: 30000 steps/sec, Acceleration: 30000 steps/sec²");
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