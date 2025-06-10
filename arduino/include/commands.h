#ifndef COMMANDS_H
#define COMMANDS_H

#include <SerialCommand.h>
#include <NBHX711.h>
#include "config.h"
#include "stepper_control.h"
#include "sensors.h"
#include "valves.h"
#include <stdint.h>

// Объявление внешних переменных
extern SerialCommand sCmd;
extern NBHX711 scale;

// Сообщения команд
#ifndef MSG_RECEIVED
#define MSG_RECEIVED "RECEIVED"
#endif

#ifndef MSG_COMPLETED
#define MSG_COMPLETED "COMPLETED"
#endif

#ifndef MSG_ERROR
#define MSG_ERROR "ERROR"
#endif

#ifndef MSG_TIMEOUT
#define MSG_TIMEOUT "TIMEOUT"
#endif

#ifndef MSG_NO_POSITION
#define MSG_NO_POSITION "ERR_NO_POSITION"
#endif

#ifndef MSG_HOMING_TIMEOUT
#define MSG_HOMING_TIMEOUT "ERR_HOMING_TIMEOUT"
#endif

#ifndef MSG_MISSING_PARAMETER
#define MSG_MISSING_PARAMETER "ERR_MISSING_PARAMETER"
#endif

#ifndef MSG_INVALID_PARAMETER
#define MSG_INVALID_PARAMETER "ERR_INVALID_PARAMETER"
#endif

// Настройка обработчиков команд
void setupCommandHandlers();

// Отправка сообщения о получении команды
void sendReceived();

// Отправка сообщения о завершении команды
void sendCompleted();

// Отправка сообщения об ошибке
void sendError(const char* errorMsg);

// Обработка неизвестной команды
void handleUnrecognized(const char* command);

// Тестовая функция для проверки связи
void testCommand();

// Обработчики команд движения
void handleMoveMulti();
void handleMoveMultizone();
void handleMoveRRight();

// Новые обработчики команд для Multi и RRight
void handleMultiPos();
void handleRRightPos();
void handleZeroAndMoveMulti();
void handleZeroAndMoveRRight();

// Обработчики команд хоминга
void handleZeroMulti();
void handleZeroMultizone();
void handleZeroRRight();

// Обработчики команд насоса
void handlePumpOn();
void handlePumpOff();

// Обработчики команд клапанов
void handleKl1();
void handleKl2();
void handleKl1On();
void handleKl2On();
void handleKl1Off();
void handleKl2Off();

// Обработчики команд датчиков
void handleWeight();
void handleRawWeight();
void handleWeightDebug();
void handleCalibrateWeight();
void handleCalibrateWeightFactor();
void handleStateRotor();
void handleWaste();

// Обработчики диагностических команд
void handleCheckMultiEndstop();
void handleCheckMultizoneEndstop();
void handleCheckRRightEndstop();
void handleCheckAllEndstops();

// Обработчики команд clamp
void handleClamp();
void handleClampZero();

// Обработчики команд для роторов
void handleRotorForward();
void handleRotorReverse();
void handleRotorStop();

// Обработчик команд для весов
void handleGetWeight();

// Обработка входящих команд
void processCommands();

#endif // COMMANDS_H 