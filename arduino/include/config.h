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
#define RRIGHT_ENDSTOP_PIN 3   // Z+ на плате

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

// ============== CONSTANTS ==============
const int HOMING_SPEED = 300;     // steps/sec
const int HOMING_TIMEOUT = 10000; // ms
const int CLAMP_SPEED = 2000;      // steps/sec для функции clamp
const int CLAMP_ZERO_SPEED = 2000; // steps/sec для функции clamp_zero
const int CLAMP_ACCELERATION = 2000; // steps/sec^2 для функций clamp и clamp_zero

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