#include <Arduino.h>
#include <Bounce2.h>
#include <NBHX711.h>
#include "config.h"
#include "stepper_control.h"
#include "valves.h"
#include "commands.h"

// Объект для работы с датчиком веса
NBHX711 scale(WEIGHT_SENSOR_DT, WEIGHT_SENSOR_SCK, 16);
Bounce tara;

// Флаг для включения/выключения периодической отправки веса
bool autoReportWeight = false;

// Включить автоматический отчет о весе
void enableWeightReport() {
  autoReportWeight = true;
  Serial.println(F("Автоматический отчет о весе ВКЛЮЧЕН"));
}

// Выключить автоматический отчет о весе
void disableWeightReport() {
  autoReportWeight = false;
  Serial.println(F("Автоматический отчет о весе ВЫКЛЮЧЕН"));
}

// ============== SETUP ==============
void setup() {
  // Инициализация последовательного порта
  Serial.begin(115200);
  
  // Задержка для стабилизации порта
  delay(1000);
  
  Serial.println(F("======== CИСТЕМА ЗАПУСКАЕТСЯ ========"));
  Serial.println(F("Версия: 1.0"));
  
  // Инициализация шаговых двигателей
  initializeSteppers();
  
  // Инициализация датчика веса
  scale.begin();
  scale.setScale(2230.0); // Установить калибровочный коэффициент
  scale.tare(); // Тарируем весы при запуске
  Serial.println(F("Датчик веса инициализирован и тарирован."));
  
  // Кнопка тарирования весов (переназначим пин, если KL1_PIN используется)
  // Убедитесь, что TARA_BUTTON_PIN не конфликтует с другими пинами!
  #define TARA_BUTTON_PIN 9 // Пример: используем пин 9 для кнопки тары
  tara.attach(TARA_BUTTON_PIN, INPUT_PULLUP); 
  Serial.print(F("Кнопка тарирования подключена к пину: ")); Serial.println(TARA_BUTTON_PIN);
  
  // Инициализация клапанов
  initializeValves();
  
  // Настройка обработчиков команд
  setupCommandHandlers();
  
  // Отправляем тестовое сообщение, чтобы убедиться, что все работает
  Serial.println();
  Serial.println(F("======== СИСТЕМА ГОТОВА ========"));
  // Обновим список команд, если команды серво были добавлены
  Serial.println(F("Доступные команды:"));
  Serial.println(F("- test: проверка связи"));
  Serial.println(F("- move_multi <шаги>, move_multizone <шаги>, move_rright <шаги>"));
  Serial.println(F("- zero_multi, zero_multizone, zero_rright"));
  Serial.println(F("- clamp <позиция>: движение моторов E0 и E1 в указанную абсолютную позицию"));
  Serial.println(F("- clamp_zero: обнуление моторов E0 и E1 по датчику (оба получают позицию 100)"));
  Serial.println(F("- clamp_stop: аварийная остановка моторов E0 и E1"));
  Serial.println(F("- kl1_on/off, kl2_on/off, kl3_on/off"));
  Serial.println(F("- pump_on/off"));
  Serial.println(F("- weight: получить вес"));
  Serial.println(F("- raw_weight: получить сырое значение"));
  Serial.println(F("- calibrate_weight: тарировать весы"));
  Serial.println(F("- calibrate_weight_factor <число>: установить калибровочный коэффициент"));
  // Добавим команды серво, если они есть в commands.cpp
  // Serial.println(F("- servo1 <проценты>, servo2 <проценты>"));
  // Serial.println(F("- reset_servos")); 
  // Serial.println(F("- servo_test_on/off"));
  Serial.println();
  Serial.println(F("Ожидание команд..."));
}

// ============== MAIN LOOP ==============
void loop() {
  // УДАЛЕНО: static unsigned long lastWeightReportTime = 0;
  // УДАЛЕНО: static bool firstTime = true;
  // УДАЛЕНО: static byte initialCount = 0;
  
  // Обработка входящих команд
  if (Serial.available() > 0) {
    sCmd.readSerial();
  }
  
  // УДАЛЕНО: Обработка кнопки тарирования
  // if (tara.update() && tara.fell()) { ... }
  
  // УДАЛЕНО: Обновление состояния датчика веса
  // scale.update(); 

  // УДАЛЕНО: Логика автоматической отправки веса
  // if (autoReportWeight && (millis() - lastWeightReportTime >= 1000)) { ... }
  
  // УДАЛЕНО: Обновление состояния шаговых двигателей
  // updateSteppers(); 
} 