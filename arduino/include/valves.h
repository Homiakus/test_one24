#ifndef VALVES_H
#define VALVES_H

#include <stdint.h>
#include "config.h"

// Инициализация пинов клапанов и насоса
void initializeValves();

// Управление насосом
void setPumpState(bool state);

// Переключение состояния клапана
void toggleValveState(int valvePin);

// Установка состояния клапана
void setValveState(int valvePin, bool state);

// Включение клапана
void turnValveOn(int valvePin);

// Выключение клапана
void turnValveOff(int valvePin);

#endif // VALVES_H 