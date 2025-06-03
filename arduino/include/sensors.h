#ifndef SENSORS_H
#define SENSORS_H

#include <stdint.h>
#include "config.h"

// Инициализация пинов датчиков
void initializeSensors();

// Чтение состояния ротора
void readRotorState(char* stateBuffer);

// Чтение состояния датчика отходов
bool readWasteSensor();

// Чтение состояния концевых выключателей
bool readEndstopState(int endstopPin);

#endif // SENSORS_H 