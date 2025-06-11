#ifndef CONFIG_H
#define CONFIG_H

#include <Arduino.h>

// ============== PIN ASSIGNMENT ==============
// Stepper Multi (X на плате)
#define MULTI_STEP_PIN A0
#define MULTI_DIR_PIN A1
#define MULTI_ENABLE_PIN 38
#define MULTI_ENDSTOP_PIN 14    // X+ на плате

// Pump (digital output)
#define PUMP_PIN 18

// Stepper Multizone (Y на плате)
#define MULTIZONE_STEP_PIN A6
#define MULTIZONE_DIR_PIN A7
#define MULTIZONE_ENABLE_PIN A2
#define MULTIZONE_ENDSTOP_PIN 2    // Y+ на плате

// Stepper RRight (Z на плате)
#define RRIGHT_STEP_PIN 46
#define RRIGHT_DIR_PIN 48
#define RRIGHT_ENABLE_PIN A8
#define RRIGHT_ENDSTOP_PIN 2   // Z+ на плате

// Stepper E0 (E0 на схеме распиновки)
#define E0_STEP_PIN 26
#define E0_DIR_PIN 28
#define E0_ENABLE_PIN 24

// Stepper E1 (E1 на схеме распиновки)
#define E1_STEP_PIN 36
#define E1_DIR_PIN 34
#define E1_ENABLE_PIN 30

// Датчик для функции clamp_zero (изменен с 3 на 15, чтобы избежать конфликта)
#define CLAMP_SENSOR_PIN 15

// Valves (используем свободные пины)
#define KL1_PIN 8
#define KL2_PIN 10

// Sensors
// HX711 датчик веса - используем доступные пины для MKS Gen L v1
#define WEIGHT_SENSOR_SCK 42    // SCK пин для HX711
#define WEIGHT_SENSOR_DT 40     // DT пин для HX711

#define WASTE_PIN 19
#define ROTOR_PINS {27, 29, 23, 25}

// ============== STEPPER MOTOR CONFIGURATIONS ==============

// Stepper Multi (X) Configuration
#define MULTI_STEPS_PER_REVOLUTION 200    // шагов на оборот
#define MULTI_MAX_SPEED 6000               // steps/sec
#define MULTI_ACCELERATION 5000           // steps/sec^2
#define MULTI_HOMING_SPEED 6000            // steps/sec для хоминга (увеличено)
#define MULTI_ENDSTOP_TYPE_NPN false       // true = NPN, false = PNP
#define MULTI_POWER_ALWAYS_ON true         // true = питание постоянно, false = только при движении

// Stepper Multizone (Y) Configuration
#define MULTIZONE_STEPS_PER_REVOLUTION 200  // шагов на оборот
#define MULTIZONE_MAX_SPEED 600             // steps/sec
#define MULTIZONE_ACCELERATION 800          // steps/sec^2
#define MULTIZONE_HOMING_SPEED 400          // steps/sec для хоминга (увеличено)
#define MULTIZONE_ENDSTOP_TYPE_NPN true     // true = NPN, false = PNP
#define MULTIZONE_POWER_ALWAYS_ON true      // true = питание постоянно, false = только при движении

// Stepper RRight (Z) Configuration
#define RRIGHT_STEPS_PER_REVOLUTION 200     // шагов на оборот
#define RRIGHT_MAX_SPEED 30000                // steps/sec (временно увеличено для диагностики)
#define RRIGHT_ACCELERATION 2000             // steps/sec^2 (временно увеличено для диагностики)
#define RRIGHT_HOMING_SPEED 2000             // steps/sec для хоминга (увеличено)
#define RRIGHT_ENDSTOP_TYPE_NPN true        // true = NPN, false = PNP
#define RRIGHT_POWER_ALWAYS_ON true         // true = питание постоянно, false = только при движении

// Stepper E0 Configuration
#define E0_STEPS_PER_REVOLUTION 200         // шагов на оборот
#define E0_MAX_SPEED 2000                   // steps/sec
#define E0_ACCELERATION 2000                // steps/sec^2
#define E0_HOMING_SPEED 1000                // steps/sec для хоминга (если будет использоваться)
#define E0_ENDSTOP_TYPE_NPN true            // true = NPN, false = PNP (для clamp_zero датчика)
#define E0_POWER_ALWAYS_ON true            // ВРЕМЕННО true для диагностики

// Stepper E1 Configuration
#define E1_STEPS_PER_REVOLUTION 200         // шагов на оборот
#define E1_MAX_SPEED 2000                   // steps/sec
#define E1_ACCELERATION 2000                // steps/sec^2
#define E1_HOMING_SPEED 1000                // steps/sec для хоминга (если будет использоваться)
#define E1_ENDSTOP_TYPE_NPN true            // true = NPN, false = PNP (для clamp_zero датчика)
#define E1_POWER_ALWAYS_ON true            // ВРЕМЕННО true для диагностики

// ============== LEGACY CONSTANTS (для обратной совместимости) ==============
const int HOMING_SPEED = 300;               // Общий хоминг (устарело, используйте индивидуальные настройки)
const int HOMING_TIMEOUT = 30000;           // ms - увеличен для более медленных двигателей
const int CLAMP_SPEED = 2000;               // steps/sec для функции clamp (устарело)
const int CLAMP_ZERO_SPEED = 2000;          // steps/sec для функции clamp_zero (устарело)
const int CLAMP_ACCELERATION = 2000;        // steps/sec^2 для функций clamp и clamp_zero (устарело)

// ============== RESPONSE MESSAGES ==============
#define MSG_OK "OK"
#define MSG_ERROR "ERR"
#define MSG_RECEIVED "RECEIVED"
#define MSG_COMPLETED "COMPLETED"
#define MSG_HOMING_TIMEOUT "HOMING TIMEOUT"
#define MSG_NO_POSITION "NO POSITION"
#define MSG_INVALID_VALUE "INVALID VALUE"
#define MSG_MISSING_PARAMETER "MISSING PARAMETER"
#define MSG_INVALID_PARAMETER "INVALID PARAMETER"

#endif // CONFIG_H 