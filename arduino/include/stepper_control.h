#ifndef STEPPER_CONTROL_H
#define STEPPER_CONTROL_H

#include <GyverStepper2.h>
#include <stdint.h>
#include "config.h"

// Объявления шаговых двигателей
extern GStepper2<STEPPER2WIRE> multiStepper;
extern GStepper2<STEPPER2WIRE> multizoneSteper;
extern GStepper2<STEPPER2WIRE> rRightStepper;
extern GStepper2<STEPPER2WIRE> e0Stepper;
extern GStepper2<STEPPER2WIRE> e1Stepper;

// Функции для управления переменной clampInProgress
void resetClampFlag();
bool isClampInProgress();

// Инициализация шаговых двигателей
void initializeSteppers();

// Установка позиции для двигателя
bool setStepperPosition(GStepper2<STEPPER2WIRE>& stepper, long position);

// Выполнение хоминга для двигателя
bool homeStepperMotor(GStepper2<STEPPER2WIRE>& stepper, int endstopPin);

// Синхронное вращение двигателей E0 и E1
bool clampMotors(long steps);

// Обнуление двигателей E0 и E1 по датчику D3
bool clampZeroMotors();

#endif // STEPPER_CONTROL_H 