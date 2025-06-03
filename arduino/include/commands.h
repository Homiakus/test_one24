#ifndef COMMANDS_H
#define COMMANDS_H

#include <SerialCommand.h>
#include <NBHX711.h>
#include "config.h"
#include "stepper_control.h"
#include "sensors.h"
#include "valves.h"

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

// Обработчики команд для новых двигателей E0 и E1
void handleClamp();
void handleClampZero();

// Обработчики команд хоминга
void handleZeroMulti();
void handleZeroMultizone();
void handleZeroRRight();

// Обработчики команд управления насосом
void handlePumpOn();
void handlePumpOff();

// Обработчики команд управления клапанами
void handleKl1On();
void handleKl2On();
void handleKl3On();
void handleKl1Off();
void handleKl2Off();
void handleKl3Off();

// Обработчики команд чтения датчиков
void handleWeight();
void handleRawWeight();
void handleWeightDebug();
void handleStateRotor();
void handleWaste();
void handleCalibrateWeight();
void handleCalibrateWeightFactor();
void handleWeightReportOn();
void handleWeightReportOff();

// Обработчики диагностических команд
void handleCheckMultiEndstop();
void handleCheckMultizoneEndstop();
void handleCheckRRightEndstop();
void handleCheckAllEndstops();


// Обработчики команд для клапанов
void handleKl1Toggle();
void handleKl2Toggle();
void handleKl3Toggle();
void handleKl1Off();
void handleKl2Off();
void handleKl3Off();

// Обработчики команд для насоса
void handlePumpToggle();
void handlePumpOn();
void handlePumpOff();

// Обработчики команд для роторов
void handleRotorForward();
void handleRotorReverse();
void handleRotorStop();

// Обработчик команд для весов
void handleGetWeight();

#endif // COMMANDS_H 