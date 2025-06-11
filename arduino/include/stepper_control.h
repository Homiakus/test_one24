#ifndef STEPPER_CONTROL_H
#define STEPPER_CONTROL_H

#include <GyverStepper2.h>
#include <stdint.h>
#include "config.h"

// Типы шаговых двигателей
typedef enum {
  STEPPER_MULTI,
  STEPPER_MULTIZONE,
  STEPPER_RRIGHT,
  STEPPER_E0,
  STEPPER_E1
} StepperType;

// Структура для хранения конфигурации шагового двигателя
typedef struct {
  int stepPin;
  int dirPin;
  int endstopPin;
  int stepsPerRevolution;
  int maxSpeed;
  int acceleration;
  int homingSpeed;
  bool endstopTypeNPN;
  bool powerAlwaysOn;
} StepperConfig;

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

// Получение указателя на двигатель по типу
GStepper2<STEPPER2WIRE>* getStepperByType(StepperType type);

// Получение конфигурации двигателя по типу
StepperConfig getStepperConfig(StepperType type);

// Применение конфигурации к двигателю
void applyStepperConfig(GStepper2<STEPPER2WIRE>& stepper, const StepperConfig& config);

// Чтение концевого выключателя с учетом типа (NPN/PNP)
bool readEndstopWithType(int endstopPin, bool isNPN);

// Универсальные функции управления двигателями
bool moveStepper(StepperType type, long position);
bool homeStepper(StepperType type);
bool zeroAndMoveStepper(StepperType type, long position);

// Индивидуальные функции для E0 и E1
bool moveE0(long position);
bool moveE1(long position);
bool homeE0();
bool homeE1();

// Базовые функции для работы с двигателями
bool setStepperPosition(GStepper2<STEPPER2WIRE>& stepper, long position);
bool homeStepperMotor(GStepper2<STEPPER2WIRE>& stepper, int endstopPin);
bool homeStepperMotorWithConfig(GStepper2<STEPPER2WIRE>& stepper, const StepperConfig& config);

// Синхронное вращение двигателей E0 и E1
bool clampMotors(long steps);

// Обнуление двигателей E0 и E1 по датчику
bool clampZeroMotors();

// Дополнительные функции для Multi и RRight
bool zeroAndMoveMulti(long position);
bool zeroAndMoveRRight(long position);

#endif // STEPPER_CONTROL_H 